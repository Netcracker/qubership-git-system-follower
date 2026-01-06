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

from pathlib import Path
from unittest.mock import patch

import pytest

from git_system_follower.errors import DownloadPackageError
from git_system_follower.download import (
    _get_filename_without_suffix,
    _save_info_about_downloaded_package, _get_current_path_using_mapping, _get_fixed_package_using_mapping,
)
from git_system_follower.plugins.cli.packages.default import TarGzPlugin
from git_system_follower.typings.cli import (
    PackageCLI, PackageCLISource, PackageCLITarGz, PackageCLIImage
)


@pytest.mark.unit
@pytest.mark.parametrize(
    "path,suffix,result", [
        (Path("filename@1.0.0.tar.gz"), TarGzPlugin.suffix, "filename@1.0.0"),
        (Path("package.yaml"), ".yaml", "package"),
        (Path("absolute/path/to/filename.txt"), ".txt", "filename"),
    ]
)
def test__get_filename_without_suffix(path: Path, suffix: str, result: str):
    assert _get_filename_without_suffix(path, suffix) == result


@pytest.mark.unit
@pytest.mark.parametrize(
    "loads,package,actual_path,expected", [
        (  # before not gears
            {}, PackageCLIImage(registry="fake", repository="fake", image="gear", ref="v1"),
            Path("path/to/.git-system-follower/packages/gear@v1.tar.gz"), 
            {"gear@v1": "fake/fake/gear:v1"},
        ),
        (  # before exist gears
            {"exist@2.0": "fake-image"}, PackageCLIImage(registry="fake", repository="fake", image="gear", ref="v1"),
            Path("path/to/.git-system-follower/packages/gear@v1.tar.gz"), 
            {"exist@2.0": "fake-image", "gear@v1": "fake/fake/gear:v1"},
        ),
        (  # envgene case. Before no gears
            {}, PackageCLIImage(registry='ghcr.io', repository='netcracker', image='qubership-gsf-discovery', ref='feature_ns-filter-support_20251225-054807'),
            Path("packages/envgene_discovery_project@1.13.2.tar.gz"), 
            {"envgene_discovery_project@1.13.2": "ghcr.io/netcracker/qubership-gsf-discovery:feature_ns-filter-support_20251225-054807"},
        )
    ]
)
def test__save_info_about_downloaded_package(loads: dict, package: PackageCLIImage, actual_path: Path, expected: dict):
    with patch("builtins.open"), \
         patch("git_system_follower.download.json.load", return_value=loads), \
         patch("git_system_follower.download.json.dump") as dump:
        _save_info_about_downloaded_package(package, actual_path)

    content = dump.call_args.args[0]
    assert content == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "loads,packages,package,expected", [
        ({}, (), PackageCLIImage(registry="registry.io", repository="repo", image="gear", ref="v1"), None),
        (  # no packages in mapper and package_dir
            {"gear@v1": "registry.io/repo/gear:v1"}, (),
            PackageCLIImage(registry="registry.io", repository="repo", image="gear", ref="v1"), None,
        ),
        (  # mismatch packages in mapper and package_dir
            {"gear@v1": "registry.io/repo/gear:v1"}, (Path("path/to/fake-gear@v1.tar.gz"),),
            PackageCLIImage(registry="registry.io", repository="repo", image="gear", ref="v1"), None,
        ),
        (  # matching packages in mapper and package_dir
            {"gear@v1": "registry.io/repo/gear:v1"}, (Path("path/to/gear@v1.tar.gz"),),
            PackageCLIImage(registry="registry.io", repository="repo", image="gear", ref="v1"), 
            Path("path/to/gear@v1.tar.gz"),
        ),
    ]
)
def test__get_current_path_using_mapping(loads: dict, packages: tuple[str], package: PackageCLIImage, expected: str | None):
    with patch("builtins.open"), \
         patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.glob", return_value=packages), \
         patch("git_system_follower.download.json.load", return_value=loads):
        package = _get_current_path_using_mapping(package, Path("fake/path/to/dir"))

    assert package == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "loads,package,expected", [
        ({}, PackageCLIImage(registry="registry.io", repository="repo", image="gear", ref="v1"), DownloadPackageError),
        (  # mismatch packages in mapper and package
            {"gear@v1": "registry.io/repo/gear:v1"},
            PackageCLIImage(registry="registry.io", repository="repo", image="fake-gear", ref="v1"),
            DownloadPackageError,
        ),
        (  # matching packages in mapper and package
            {"gear@v1": "registry.io/repo/gear:v1"},
            PackageCLIImage(registry="registry.io", repository="repo", image="gear", ref="v1"),
            PackageCLI(name="gear", version="v1")
        ),
    ]
)
def test__get_fixed_package_using_mapping(
    loads: dict, package: PackageCLIImage | PackageCLITarGz | PackageCLISource, expected: PackageCLI | Exception
):
    with patch("builtins.open"), \
         patch("git_system_follower.download.json.load", return_value=loads):
        if isinstance(expected, type) and issubclass(expected, Exception):
            with pytest.raises(DownloadPackageError):
                package = _get_fixed_package_using_mapping(package)
        else:
            package = _get_fixed_package_using_mapping(package)
            assert package == expected
