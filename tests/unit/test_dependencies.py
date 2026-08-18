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

import contextlib
import copy
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from git_system_follower.download import download
from git_system_follower.errors import MaxDependencyDepthError
from git_system_follower.package.package_info import (
    _validate_package_info, add_dependencies, check_dependency_depth,
)
from git_system_follower.states import StateFile
from git_system_follower.typings.cli import (
    PackageCLI, PackageCLIImage, PackageCLISource, PackageCLITypes,
)
from git_system_follower.typings.package import PackageLocalData
from git_system_follower.uninstall import (
    validate_packages_dependencies, _is_package_a_dependency, _whether_to_delete_main_packages,
)


def _pkg(name: str, version: str = '1.0.0', dependencies=()) -> PackageLocalData:
    """ Build a minimal local package info dict """
    return PackageLocalData(
        apiVersion='v1',
        type='gitlab-ci-pipeline',
        name=name,
        version=version,
        dependencies=tuple(dependencies),
        path=Path(f'/fake/{name}'),
    )


class TestAddDependencies:
    """ add_dependencies: ordering and de-duplication of downloaded packages """

    def test_deps_first_inserts_dependencies_before_main(self):
        main = _pkg('main')
        deps = [_pkg('dep-a'), _pkg('dep-b')]

        result = add_dependencies([main], deps, is_deps_first=True)

        assert [package['name'] for package in result] == ['dep-a', 'dep-b', 'main']

    def test_deps_first_inserts_sub_dependency_before_parent(self):
        dep = _pkg('dep-a')
        sub_dep = _pkg('dep-b')

        result = add_dependencies([dep], [sub_dep], is_deps_first=True)

        assert [package['name'] for package in result] == ['dep-b', 'dep-a']

    def test_deps_last_appends_dependencies_after_main(self):
        main = _pkg('main')
        deps = [_pkg('dep-a'), _pkg('dep-b')]

        result = add_dependencies([main], deps, is_deps_first=False)

        assert [package['name'] for package in result] == ['main', 'dep-a', 'dep-b']

    def test_already_present_dependency_is_not_duplicated(self):
        dep = _pkg('dep-a')
        main = _pkg('main')
        packages = [dep, main]

        result = add_dependencies(packages, [dep], is_deps_first=True)

        assert result == [dep, main]

    def test_empty_dependencies_do_not_change_packages(self):
        main = _pkg('main')

        result = add_dependencies([main], [], is_deps_first=True)

        assert result == [main]


class TestCheckDependencyDepth:
    """ check_dependency_depth: maximum allowed dependency level is 1 """

    def test_root_level_is_allowed(self):
        check_dependency_depth(0, 'main')

    def test_first_dependency_level_is_allowed(self):
        check_dependency_depth(1, 'main -> dep-a')

    def test_second_level_raises_max_dependency_depth_error(self):
        with pytest.raises(MaxDependencyDepthError):
            check_dependency_depth(2, 'main -> dep-a -> dep-b')


class TestValidatePackageInfoDependencies:
    """ dependencies section parsing in package.yaml """

    def test_dependencies_are_parsed_into_image_objects(self):
        data = {
            'apiVersion': 'v1',
            'type': 'gitlab-ci-pipeline',
            'name': 'main',
            'version': '1.0.0',
            'dependencies': [
                'artifactory.example.com/deps/dep-a:1.0.0',
                'nexus.example.com/deps/dep-b:2.0.0',
            ],
        }

        result = _validate_package_info(copy.deepcopy(data))

        dependencies = result['dependencies']
        assert isinstance(dependencies, tuple)
        assert len(dependencies) == 2

        first, second = dependencies
        assert first.registry == 'artifactory.example.com'
        assert first.repository == 'deps'
        assert first.image == 'dep-a'
        assert first.tag == '1.0.0'
        assert second.registry == 'nexus.example.com'
        assert second.image == 'dep-b'
        assert second.tag == '2.0.0'

    def test_missing_dependencies_default_to_empty_tuple(self):
        data = {
            'apiVersion': 'v1',
            'type': 'gitlab-ci-pipeline',
            'name': 'main',
            'version': '1.0.0',
        }

        result = _validate_package_info(copy.deepcopy(data))

        assert result['dependencies'] == ()


def _patch_download_pipeline(packages_by_name: dict):
    """ Mock the registry/filesystem access points of download() so only the
    dependency resolution logic is exercised. """

    def fake_get_source(package, directory, *, registry):
        if package.type == PackageCLITypes.source:
            return Path('/fake/main/git-system-follower-package')
        if isinstance(package, PackageCLIImage):
            return Path(f'/fake/{package.image}/git-system-follower-package')
        return None

    def fake_get_package_info(directory, name):
        return packages_by_name[directory.name]

    def fake_get_fixed_package_using_mapping(dependency):
        return PackageCLI(name=dependency.image, version=dependency.tag)

    return (
        patch('git_system_follower.download.get_source', side_effect=fake_get_source),
        patch('git_system_follower.download.get_package_info', side_effect=fake_get_package_info),
        patch('git_system_follower.download._get_fixed_package_using_mapping',
              side_effect=fake_get_fixed_package_using_mapping),
        patch('git_system_follower.download.get_gear_info', return_value={'structure_type': 'simple'}),
    )


class TestDownloadDependencyRecursion:
    """ download(): recursive dependency resolution and ordering """

    @staticmethod
    def _run(packages_by_name: dict, *, is_deps_first: bool, packages):
        registry = Mock()
        patchers = _patch_download_pipeline(packages_by_name)
        with _combined_patches(patchers):
            return download(packages, registry=registry, is_deps_first=is_deps_first)

    def test_single_dependency_is_downloaded_before_main(self):
        dep = _pkg('dep-a')
        main = _pkg('main', dependencies=[
            PackageCLIImage(registry='artifactory.example.com', repository='deps', image='dep-a', tag='1.0.0'),
        ])

        result = self._run({'main': main, 'dep-a': dep}, is_deps_first=True,
                           packages=[PackageCLISource(path=Path('/src/main'))])

        assert [package['name'] for package in result] == ['dep-a', 'main']
        assert result[1]['dependencies'] == (PackageCLI(name='dep-a', version='1.0.0'),)

    def test_dependencies_from_different_registries_are_resolved(self):
        dep_a = _pkg('dep-a')
        dep_b = _pkg('dep-b')
        main = _pkg('main', dependencies=[
            PackageCLIImage(registry='artifactory.example.com', repository='deps', image='dep-a', tag='1.0.0'),
            PackageCLIImage(registry='nexus.example.com', repository='deps', image='dep-b', tag='1.0.0'),
        ])

        result = self._run({'main': main, 'dep-a': dep_a, 'dep-b': dep_b}, is_deps_first=True,
                           packages=[PackageCLISource(path=Path('/src/main'))])

        assert [package['name'] for package in result] == ['dep-a', 'dep-b', 'main']
        assert result[2]['dependencies'] == (
            PackageCLI(name='dep-a', version='1.0.0'),
            PackageCLI(name='dep-b', version='1.0.0'),
        )

    def test_two_level_chain_raises_max_dependency_depth_error(self):
        sub_dep = _pkg('dep-b')
        dep_a = _pkg('dep-a', dependencies=[
            PackageCLIImage(registry='artifactory.example.com', repository='deps', image='dep-b', tag='1.0.0'),
        ])
        main = _pkg('main', dependencies=[
            PackageCLIImage(registry='artifactory.example.com', repository='deps', image='dep-a', tag='1.0.0'),
        ])

        with pytest.raises(MaxDependencyDepthError):
            self._run({'main': main, 'dep-a': dep_a, 'dep-b': sub_dep}, is_deps_first=True,
                      packages=[PackageCLISource(path=Path('/src/main'))])

    def test_dependency_that_skips_download_does_not_break_ordering(self):
        main = _pkg('main', dependencies=[
            PackageCLIImage(registry='artifactory.example.com', repository='deps', image='dep-a', tag='1.0.0'),
        ])

        def fake_get_source(package, directory, *, registry):
            if package.type == PackageCLITypes.source:
                return Path('/fake/main/git-system-follower-package')
            return None  # image download skipped

        patchers = _patch_download_pipeline({'main': main})
        registry = Mock()
        with _combined_patches(patchers):
            with patch('git_system_follower.download.get_source', side_effect=fake_get_source):
                result = download([PackageCLISource(path=Path('/src/main'))],
                                  registry=registry, is_deps_first=True)

        assert [package['name'] for package in result] == ['main']

    def test_uninstall_ordering_main_first(self):
        dep = _pkg('dep-a')
        main = _pkg('main', dependencies=[
            PackageCLIImage(registry='artifactory.example.com', repository='deps', image='dep-a', tag='1.0.0'),
        ])

        result = self._run({'main': main, 'dep-a': dep}, is_deps_first=False,
                           packages=[PackageCLISource(path=Path('/src/main'))])

        assert [package['name'] for package in result] == ['main', 'dep-a']


def _combined_patches(patchers):
    """ Enter a stack of context managers (patchers) and return it """
    stack = contextlib.ExitStack()
    for patcher in patchers:
        stack.enter_context(patcher)
    return stack


class TestUninstallDependencyGuard:
    """ uninstall(): excluding dependencies that are still used by other packages """

    @staticmethod
    def _state(installed_packages):
        class StubState:
            def get_packages(self):
                return installed_packages
        return StubState()

    def test_uninstall_main_keeps_its_dependency_installed(self):
        main = _pkg('main', dependencies=['dep-a@1.0.0'])
        state = self._state([main])

        result = validate_packages_dependencies((main,), state)

        assert result == (main,)

    def test_uninstall_main_without_dependencies(self):
        main = _pkg('main')
        state = self._state([main])

        result = validate_packages_dependencies((main,), state)

        assert result == (main,)

    def test_uninstall_main_and_dependency_together(self):
        dep = _pkg('dep-a')
        main = _pkg('main', dependencies=['dep-a@1.0.0'])
        state = self._state([main])

        result = validate_packages_dependencies((main, dep), state)

        assert result == (main, dep)

    def test_uninstall_dependency_used_by_package_that_stays_is_excluded(self):
        dep = _pkg('dep-a')
        main = _pkg('main', dependencies=['dep-a@1.0.0'])
        state = self._state([main])

        result = validate_packages_dependencies((dep,), state)

        assert result == ()

    def test_uninstall_shared_dependency_partially_kept_is_excluded(self):
        dep = _pkg('dep-a')
        main_a = _pkg('main-a', dependencies=['dep-a@1.0.0'])
        main_b = _pkg('main-b', dependencies=['dep-a@1.0.0'])
        state = self._state([main_a, main_b])

        result = validate_packages_dependencies((main_a, dep), state)

        assert result == (main_a,)

    def test_uninstall_shared_dependency_fully_deleted_is_kept(self):
        dep = _pkg('dep-a')
        main_a = _pkg('main-a', dependencies=['dep-a@1.0.0'])
        main_b = _pkg('main-b', dependencies=['dep-a@1.0.0'])
        state = self._state([main_a, main_b])

        result = validate_packages_dependencies((main_a, main_b, dep), state)

        assert result == (main_a, main_b, dep)

    def test_is_package_a_dependency_matches_name_and_version(self):
        dep = _pkg('dep-a', version='1.0.0')
        main_matching = _pkg('main', dependencies=['dep-a@1.0.0'])
        main_other_version = _pkg('main-other', dependencies=['dep-a@2.0.0'])

        is_dependency, for_packages = _is_package_a_dependency(dep, [main_matching])
        assert is_dependency is True
        assert for_packages == [main_matching]

        is_dependency, for_packages = _is_package_a_dependency(dep, [main_other_version])
        assert is_dependency is False
        assert for_packages == []

    def test_whether_to_delete_main_packages(self):
        main_a = _pkg('main-a', dependencies=[PackageCLI(name='dep-a', version='1.0.0')])
        main_b = _pkg('main-b', dependencies=[PackageCLI(name='dep-a', version='1.0.0')])

        assert _whether_to_delete_main_packages((main_a,), [main_a]) is True
        assert _whether_to_delete_main_packages((main_a,), [main_a, main_b]) is False
        assert _whether_to_delete_main_packages((main_a, main_b), [main_a, main_b]) is True


class TestStateRecordsDependencies:
    """ states: dependencies are persisted in .state.yaml as name@version """

    def test_add_package_records_dependencies(self):
        main = _pkg('main', dependencies=[
            PackageCLI(name='dep-a', version='1.0.0'),
            PackageCLI(name='dep-b', version='2.0.0'),
        ])
        response = {
            'cicd_variables': [],
            'webhooks': [],
            'template': 'default',
            'template_variables': {},
        }

        state = StateFile()
        state.add_package(main, (), response, None, structure_type='simple')

        package_state = state.get_package(main, for_delete=False)
        assert package_state['dependencies'] == ['dep-a@1.0.0', 'dep-b@2.0.0']

    def test_add_package_records_empty_dependencies(self):
        main = _pkg('main', dependencies=[])
        response = {
            'cicd_variables': [],
            'webhooks': [],
            'template': 'default',
            'template_variables': {},
        }

        state = StateFile()
        state.add_package(main, (), response, None, structure_type='simple')

        package_state = state.get_package(main, for_delete=False)
        assert package_state['dependencies'] == []
