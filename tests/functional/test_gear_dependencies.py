# Copyright 2024-2025 NetCracker Technology Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""" Functional tests of the end-to-end dependency resolution pipeline.

Dependencies of a gear are always docker images referenced from `package.yaml`.
The registry HTTP layer is replaced with a fake registry client that serves
pre-built local `.tar.gz` archives, so the whole download() flow (recursive
resolution, ordering, de-duplication, depth limit, mapping to name@version)
is exercised against real gear folders and real archives without any network.
"""
import shutil
import tarfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from git_system_follower.download import download
from git_system_follower.errors import DownloadPackageError, MaxDependencyDepthError
from git_system_follower.typings.cli import (
    PackageCLI, PackageCLIImage, PackageCLISource, Credentials,
)
from git_system_follower.typings.registry import RegistryInfo, RegistryTypes
from git_system_follower.variables import IMAGE_PACKAGE_MAP, PACKAGE_DIRNAME, PACKAGES_PATH


def _build_gear(root: Path, name: str, version: str, dependencies=()) -> Path:
    """ Create a local gear source directory with the given package.yaml """
    gear_dir = root / name
    package_dir = gear_dir / PACKAGE_DIRNAME
    (package_dir / 'scripts').mkdir(parents=True)
    data = {
        'apiVersion': 'v1',
        'type': 'gitlab-ci-pipeline',
        'name': name,
        'version': version,
    }
    if dependencies:
        data['dependencies'] = list(dependencies)
    with open(package_dir / 'package.yaml', 'w', encoding='utf-8') as file:
        yaml.safe_dump(data, file)
    return gear_dir


def _build_targz(root: Path, name: str, version: str, dependencies=()) -> Path:
    """ Build a package archive the way it would be stored in a registry """
    gear_dir = _build_gear(root, name, version, dependencies)
    archive = root / f'{name}@{version}.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        tar.add(gear_dir / PACKAGE_DIRNAME, arcname=PACKAGE_DIRNAME)
    return archive


def _build_tarballs(root: Path, packages: list[tuple]) -> dict[tuple, Path]:
    """ Build several archives keyed by (image_name, tag) """
    tarballs = {}
    for name, version, *rest in packages:
        dependencies = rest[0] if rest else ()
        tarballs[(name, version)] = _build_targz(root, name, version, dependencies)
    return tarballs


class FakeRegistryClient:
    """ Mimics the registry client interface used by download_package """

    def __init__(self, tarballs: dict[tuple, Path]):
        self.tarballs = tarballs
        self.auth = Mock()

    def download(self, target: str, outdir: Path, *, registry):
        """ Serve a local archive instead of pulling a layer from a registry """
        image = target.rsplit('/', 1)[-1].rsplit(':', 1)[0]
        tag = target.rsplit(':', 1)[-1]
        tarball = self.tarballs.get((image, tag))
        if tarball is None:
            return None
        destination = Path(outdir) / tarball.name
        shutil.copy(tarball, destination)
        return destination

    def get_container(self, target):
        return Mock()

    def _basic_auth(self, container, *, registry):
        return 'fake-token'

    def get_manifest_wrapper(self, container):
        return {
            'mediaType': 'application/vnd.docker.distribution.manifest.v2+json',
            'config': {'digest': 'sha256:fake'},
        }


def _clean_global_state():
    """ Remove artifacts written into the global package store between tests """
    if PACKAGES_PATH.exists():
        shutil.rmtree(PACKAGES_PATH)
    PACKAGES_PATH.mkdir(parents=True, exist_ok=True)
    if IMAGE_PACKAGE_MAP.exists():
        IMAGE_PACKAGE_MAP.unlink()


@pytest.fixture(autouse=True)
def _clean_package_store():
    _clean_global_state()
    yield
    _clean_global_state()


def _registry() -> RegistryInfo:
    return RegistryInfo(
        credentials=Credentials(username='user', password='pass'),
        type=RegistryTypes.auto,
        is_insecure=False,
    )


@pytest.mark.functional
def test_download_main_source_with_dependency_from_same_registry(tmp_path):
    main = _build_gear(tmp_path, 'main-gear', '1.0.0',
                       dependencies=['artifactory.example.com/deps/dep-a:1.0.0'])
    tarballs = _build_tarballs(tmp_path, [('dep-a', '1.0.0')])

    with patch('git_system_follower.download.get_client',
               return_value=FakeRegistryClient(tarballs)):
        result = download([PackageCLISource(path=main)], registry=_registry(), is_deps_first=True)

    assert [package['name'] for package in result] == ['dep-a', 'main-gear']
    assert result[1]['dependencies'] == (PackageCLI(name='dep-a', version='1.0.0'),)


@pytest.mark.functional
def test_download_dependencies_from_different_registries_same_credentials(tmp_path):
    main = _build_gear(tmp_path, 'main-gear', '1.0.0', dependencies=[
        'artifactory.example.com/deps/dep-a:1.0.0',
        'nexus.example.com/deps/dep-b:1.0.0',
    ])
    tarballs = _build_tarballs(tmp_path, [('dep-a', '1.0.0'), ('dep-b', '1.0.0')])
    registry = _registry()

    requested = []

    def fake_get_client(registry_address, *, registry):
        requested.append((registry_address, registry))
        return FakeRegistryClient(tarballs)

    with patch('git_system_follower.download.get_client', side_effect=fake_get_client):
        result = download([PackageCLISource(path=main)], registry=registry, is_deps_first=True)

    addresses = [address for address, _ in requested]
    assert sorted(addresses) == ['artifactory.example.com', 'nexus.example.com']
    for _, passed_registry in requested:
        assert passed_registry is registry
    assert [package['name'] for package in result] == ['dep-a', 'dep-b', 'main-gear']
    assert result[2]['dependencies'] == (
        PackageCLI(name='dep-a', version='1.0.0'),
        PackageCLI(name='dep-b', version='1.0.0'),
    )


@pytest.mark.functional
def test_download_main_image_with_dependency_from_another_registry(tmp_path):
    tarballs = _build_tarballs(tmp_path, [
        ('dep-a', '1.0.0'),
        ('main-gear', '1.0.0', ['artifactory.example.com/deps/dep-a:1.0.0']),
    ])
    main_image = PackageCLIImage(
        registry='artifactory.example.com', repository='main', image='main-gear', tag='1.0.0',
    )

    with patch('git_system_follower.download.get_client',
               return_value=FakeRegistryClient(tarballs)):
        result = download([main_image], registry=_registry(), is_deps_first=True)

    assert [package['name'] for package in result] == ['dep-a', 'main-gear']
    assert result[1]['dependencies'] == (PackageCLI(name='dep-a', version='1.0.0'),)


@pytest.mark.functional
def test_download_uninstall_ordering_main_first(tmp_path):
    main = _build_gear(tmp_path, 'main-gear', '1.0.0',
                       dependencies=['artifactory.example.com/deps/dep-a:1.0.0'])
    tarballs = _build_tarballs(tmp_path, [('dep-a', '1.0.0')])

    with patch('git_system_follower.download.get_client',
               return_value=FakeRegistryClient(tarballs)):
        result = download([PackageCLISource(path=main)], registry=_registry(), is_deps_first=False)

    assert [package['name'] for package in result] == ['main-gear', 'dep-a']


@pytest.mark.functional
def test_download_two_level_chain_raises_max_dependency_depth(tmp_path):
    main = _build_gear(tmp_path, 'main-gear', '1.0.0',
                       dependencies=['artifactory.example.com/deps/dep-a:1.0.0'])
    tarballs = _build_tarballs(tmp_path, [
        ('dep-b', '1.0.0'),
        ('dep-a', '1.0.0', ['artifactory.example.com/deps/dep-b:1.0.0']),
    ])

    with patch('git_system_follower.download.get_client',
               return_value=FakeRegistryClient(tarballs)):
        with pytest.raises(MaxDependencyDepthError):
            download([PackageCLISource(path=main)], registry=_registry(), is_deps_first=True)


@pytest.mark.functional
def test_download_shared_dependency_is_deduplicated(tmp_path):
    main_a = _build_gear(tmp_path, 'main-a', '1.0.0',
                         dependencies=['artifactory.example.com/deps/dep-a:1.0.0'])
    main_b = _build_gear(tmp_path, 'main-b', '1.0.0',
                         dependencies=['artifactory.example.com/deps/dep-a:1.0.0'])
    tarballs = _build_tarballs(tmp_path, [('dep-a', '1.0.0')])

    with patch('git_system_follower.download.get_client',
               return_value=FakeRegistryClient(tarballs)):
        result = download(
            [PackageCLISource(path=main_a), PackageCLISource(path=main_b)],
            registry=_registry(), is_deps_first=True,
        )

    names = [package['name'] for package in result]
    assert names.count('dep-a') == 1
    assert names == ['dep-a', 'main-a', 'main-b']


@pytest.mark.functional
def test_download_same_image_second_time_reuses_downloaded_package(tmp_path):
    main = _build_gear(tmp_path, 'main-gear', '1.0.0', dependencies=[
        'artifactory.example.com/deps/dep-a:1.0.0',
    ])
    tarballs = _build_tarballs(tmp_path, [('dep-a', '1.0.0')])
    registry = _registry()

    with patch('git_system_follower.download.get_client',
               return_value=FakeRegistryClient(tarballs)):
        first = download([PackageCLISource(path=main)], registry=registry, is_deps_first=True)
        second = download([PackageCLISource(path=main)], registry=registry, is_deps_first=True)

    assert [package['name'] for package in first] == ['dep-a', 'main-gear']
    assert [package['name'] for package in second] == ['dep-a', 'main-gear']


@pytest.mark.functional
def test_download_dependency_that_is_not_a_gear_raises(tmp_path):
    main = _build_gear(tmp_path, 'main-gear', '1.0.0',
                       dependencies=['registry.example.com/deps/not-a-gear:1.0.0'])

    with patch('git_system_follower.download.get_client',
               return_value=FakeRegistryClient({})):
        with pytest.raises(DownloadPackageError):
            download([PackageCLISource(path=main)], registry=_registry(), is_deps_first=True)
