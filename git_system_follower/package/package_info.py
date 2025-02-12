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

""" Package description file (package.yaml) processing module """
from pathlib import Path
from typing import TypedDict, Any

import yaml

from git_system_follower.logger import logger
from git_system_follower.errors import (
    PackageNotFoundError, PackageDescriptionFileError, DescriptionSectionError, MaxDependencyDepthError
)
from git_system_follower.variables import PACKAGE_DIRNAME, PACKAGE_DESCRIPTION_FILE_API
from git_system_follower.plugins.cli.packages.default import ImagePlugin
from git_system_follower.typings.package import PackageData, PackageLocalData


__all__ = [
    'DESCRIPTION_FILENAME',
    'get_package_info', 'add_dependencies', 'check_dependency_depth'
]


DESCRIPTION_FILENAME = 'package.yaml'
MAX_DEPENDENCY_LEVEL = 1
PACKAGE_DESCRIPTION_FILE_API: dict[str, 'ApiVersionInfo']


class ApiVersionInfo(TypedDict):
    mandatory_sections: tuple[str, ...]
    optional_sections: tuple[str, ...]
    section_types: tuple[object, ...]
    package_types: tuple[str, ...]


def _has_downloaded(path: Path) -> bool:
    """ Has package been downloaded

    :param path: path to directory with local package
    :return: True/False
    """
    return path.exists()


def add_dependencies(
        packages: list[PackageLocalData], dependencies: list[PackageLocalData],
        is_deps_first: bool
) -> list[PackageLocalData]:
    for dependency in dependencies:
        if dependency in packages:
            continue

        if is_deps_first:
            packages.insert(-1, dependency)
        else:
            packages.append(dependency)
    return packages


def get_package_info(directory: Path, name: str) -> PackageLocalData:
    """ Get package info from package description file (package.yaml)

    :param directory: path to directory with local package
    :param name: package name

    :return: local package info
    """
    path = directory / PACKAGE_DIRNAME / DESCRIPTION_FILENAME
    if not directory.exists():
        raise PackageNotFoundError(f'No such directory with {name} package ({directory.absolute()})')
    if not path.parent.exists():
        raise PackageNotFoundError(f'No such directory inside the project with package files {path.parent.absolute()}')
    if not path.exists():
        raise PackageNotFoundError(f'No such package.yaml file for {name} package ({path.absolute()})')

    with open(path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)

    try:
        data = _validate_package_info(data)
    except PackageDescriptionFileError:
        logger.critical(f'Error during validation of {DESCRIPTION_FILENAME} file ({path.absolute()})')
        raise

    return PackageLocalData(
        **data,
        path=directory
    )


def _validate_package_info(data: dict[str, Any]) -> PackageData:
    """ Validate package information

    :param data: information from package description file (package.yaml)
    :return: ready-made package information
    """
    # TODO: implement package.yaml validate
    api_version = _validate_api_version_section(data)
    api_info = PACKAGE_DESCRIPTION_FILE_API[api_version]
    _validate_section_names(data, api_info['mandatory_sections'], api_info['optional_sections'])
    # _validate_section_types(data, api_info['sections'], api_info['section_types'])
    _validate_type_section(data['type'], api_info['package_types'])
    updated_dependencies = []
    dependencies = data.get('dependencies')
    if dependencies is not None:
        image_plugin = ImagePlugin()
        for dependency in data['dependencies']:
            dependency = image_plugin.parse_image(dependency)
            updated_dependencies.append(dependency)
    data['version'] = str(data['version'])
    data['dependencies'] = tuple(updated_dependencies)
    return data


def _validate_api_version_section(data: dict[str, Any]) -> str:
    if (api_version := data.get('apiVersion')) is None:
        raise DescriptionSectionError("Section 'apiVersion' missing")

    if api_version not in PACKAGE_DESCRIPTION_FILE_API.keys():
        raise DescriptionSectionError(f"Unsupported package description file api version: '{api_version}'. "
                                      f"Available versions: {', '.join(PACKAGE_DESCRIPTION_FILE_API.keys())}")
    return api_version


def _validate_section_names(
        data: dict[str, Any], mandatory_keys: tuple[str, ...], optional_keys: tuple[str, ...]
) -> None:
    """ Mandatory keys validation

    :param data: information from package description file (package.yaml)
    """
    for mandatory_key in mandatory_keys:
        if mandatory_key not in data.keys():
            raise DescriptionSectionError(f'No mandatory section in {DESCRIPTION_FILENAME} file ({mandatory_key})')

    for key in data.keys():
        if key not in mandatory_keys and key not in optional_keys:
            raise DescriptionSectionError(f'An extra section is specified in {DESCRIPTION_FILENAME} file ({key})')


def _validate_section_types(data: dict[str, Any], sections: tuple[str, ...], types: tuple[object, ...]) -> None:
    # TODO: implement package.yaml validate: section types
    pass


def _validate_type_section(package_type: str, available_types: tuple[str, ...]) -> None:
    if package_type not in available_types:
        raise DescriptionSectionError(f"Unsupported package type: '{package_type}'. "
                                      f"Available types: {', '.join(available_types)}")


def check_dependency_depth(level: int, tree: str) -> None:
    """ Checking the dependency tree for maximum depth

    :param level: current dependency depth level
    :param tree: current dependency tree/string to printing the problematic dependency chain (to raise error),
                 e.g. `parent-package -> parent-dependency -> problem-dependency`
    """
    if level > MAX_DEPENDENCY_LEVEL:
        msg = f'The maximum dependency level has been reached ({MAX_DEPENDENCY_LEVEL}). Error for {tree}'
        raise MaxDependencyDepthError(msg)
