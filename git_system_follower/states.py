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

""" Module for working with state file """
from typing import TypedDict, Any, NamedTuple
from enum import Enum
from pathlib import Path
import hashlib
from datetime import datetime
from pprint import pformat
import base64

import yaml

from git_system_follower.logger import logger
from git_system_follower.errors import HashesMismatch
from git_system_follower.typings.cli import PackageCLI
from git_system_follower.typings.package import PackageLocalData
from git_system_follower.typings.script import ScriptResponse
from git_system_follower.package.cicd_variables import CICDVariable


__all__ = [
    'ChangeStatus', 'PackageState', 'StateFile',
    'get_installed_packages', 'filter_cicd_variables_by_state', 'update_created_cicd_variables',
    'mask_data', 'unmask_data'
]


class ChangeStatus(Enum):
    no_change = 0
    changed = 1


class CICDVariablesSection(TypedDict):
    names: list[str]
    hash: str


class PackageState(TypedDict):
    name: str
    version: str
    used_template: str
    template_variables: dict[str, str]
    last_update: str
    dependencies: list[str]
    cicd_variables: CICDVariablesSection


class StateFileContent(TypedDict):
    hash: str
    packages: list[PackageState]


class InstalledPackage(NamedTuple):
    name: str
    version: str


class StateFile:
    __name = '.state.yaml'

    def __init__(self, *, raw: bytes | None = None, current_cicd_variables: dict[str, CICDVariable] | None = None):
        """ Read raw state file (e.g. from GitLab REST API) or init state file with empty packages section

        :param raw: state file
        :param current_cicd_variables: current CI/CD variables in Gitlab
        """
        self.__change_status = ChangeStatus.no_change
        if raw is None:
            packages = []
            computed_hash = self.__get_hash(packages)
            self.__content = StateFileContent(hash=computed_hash, packages=packages)
            return

        content: StateFileContent = yaml.safe_load(raw)
        computed_hash = self.__get_hash(content['packages'])
        if content['hash'] != computed_hash:
            raise HashesMismatch(f"Hash specified in state file ({content['hash']}) and "
                                 f"generated hash ({computed_hash}) do not match",
                                 state_file_hash=content['hash'], generated_hash=computed_hash)

        for package in content['packages']:
            self.__check_cicd_variables_hash(package, current_cicd_variables)
        self.__content = StateFileContent(hash=computed_hash, packages=content['packages'])

    def __get_hash(self, state: Any) -> str:
        """ Generate hash for any variable.
        For example, for 'packages' section in state file, for 'cicd_variables' section

        :param state: state ('packages' section) from state file

        :return: generated hash
        """
        sorted_state = self.__sort_state(state)  # sort for the same behaviour when working with hash for saving/reading
        string = str(sorted_state)
        return hashlib.sha256(string.encode()).hexdigest()

    def __sort_state(self, state: list[PackageState] | PackageState):
        if isinstance(state, list):
            return [self.__sort_state(item) for item in state]
        elif isinstance(state, dict):
            return {key: self.__sort_state(value) for key, value in sorted(state.items())}
        else:
            return state

    def __check_cicd_variables_hash(
            self, package: PackageState, current_cicd_variables: dict[str, CICDVariable]
    ) -> None:
        """ Check hash for CI/CD variables of <package>

        :param package: package with information about variable names
        :param current_cicd_variables: current CI/CD variables in Gitlab
        """
        variables = filter_cicd_variables_by_state(package, current_cicd_variables)
        computed_hash = self.__get_hash(variables)
        if computed_hash != package['cicd_variables']['hash']:
            raise HashesMismatch(f"CI/CD variables hash specified in state file in "
                                 f"{package['name']}@{package['version']} package "
                                 f"({package['cicd_variables']['hash']}) "
                                 f"and generated hash ({computed_hash}) do not match",
                                 state_file_hash=package['cicd_variables']['hash'], generated_hash=computed_hash)

    def get_installed_packages(self) -> tuple[InstalledPackage, ...]:
        packages = []
        for package in self.__content['packages']:
            packages.append(InstalledPackage(name=package['name'], version=package['version']))
        return tuple(packages)

    def get_all_created_cicd_variables(self) -> tuple[str, ...]:
        """ Get created CI/CD variables from state file from all packages

        :return: list of CI/CD variables names in all installed packages
        """
        variables = []
        for package in self.__content['packages']:
            variables.extend(package['cicd_variables']['names'])
        return tuple(variables)

    def get_package(self, package: PackageLocalData, *, for_delete: bool) -> PackageState | None:
        """ Get state with package from state

        :param package: package which need to find in states
        :param for_delete: is need to find package to delete (or to install)

        :return: found package
        """
        if for_delete:
            return self.__get_package_state_by_name_and_version(package)
        return self.__get_package_state_by_name(package)

    def __get_package_state_by_name_and_version(self, package: PackageLocalData) -> PackageState | None:
        """ Get state with package from state by name

        :param package: package which need to find in states

        :return: found package by name and version
        """
        for state in self.__content['packages']:
            if package['name'] == state['name'] and package['version'] == state['version']:
                return state

    def __get_package_state_by_name(self, package: PackageLocalData) -> PackageState | None:
        """ Get state with package from state by name

        :param package: package which need to find in states

        :return: found package by name
        """
        for state in self.__content['packages']:
            if package['name'] == state['name']:
                return state

    def add_package(
            self, package: PackageLocalData, response: ScriptResponse | None, state: PackageState | None
    ) -> None:
        """ Add package to state file

        :param package: package which need to add to state file
        :param response: script response with information about used template, used ci/cd variables
        :param state: current state from state file (if package already installed but another versions)
        """
        if response is None:
            return

        self.__change_status = ChangeStatus.changed
        variables_names = [variable['name'] for variable in response['cicd_variables']]
        new_state = PackageState(
            name=package['name'], version=package['version'],
            used_template=response['template'],
            template_variables={name: mask_data(value) for name, value in response['template_variables'].items()},
            last_update=str(datetime.now()),
            dependencies=[f"{dependency.name}@{dependency.version}" for dependency in package['dependencies']],
            cicd_variables=CICDVariablesSection(
                names=variables_names,
                hash=self.__get_hash(response['cicd_variables'])
            )
        )
        if state is None:
            self.__content['packages'].append(new_state)
            return
        index = self.__content['packages'].index(state)
        self.__content['packages'][index] = new_state

    def delete_package(self, state: PackageState) -> PackageState:
        self.__change_status = ChangeStatus.changed
        index = self.__content['packages'].index(state)
        return self.__content['packages'].pop(index)

    def get_packages(self) -> list[PackageState]:
        return self.__content['packages'].copy()

    def status(self) -> ChangeStatus:
        return self.__change_status

    def save(self, directory: Path) -> None:
        """ Save state file

        :param directory: path where state file will be saved
        """
        path = directory / self.__name
        state = self.__content['packages']
        computed_hash = self.__get_hash(state)
        content = StateFileContent(hash=computed_hash, packages=state)
        logger.debug(f'New hash generated: {computed_hash}')
        with open(path, 'w') as file:
            yaml.dump(content, file)

    def __str__(self) -> str:
        return pformat(self.__content['packages'])


def filter_cicd_variables_by_state(
        state: PackageState | None, current_cicd_variables: dict[str, CICDVariable]
) -> list[CICDVariable]:
    """ Get current CI/CD variables of package state for CI/CD variables specified in state file
    Note: only variable names are stored in state file

    :param state: state from state file with variable names for which necessary to find it's current state
    :param current_cicd_variables: current CI/CD variables in Gitlab
    :return: list of CI/CD variables filtered by necessary variable names
    """
    if state is None:
        return []

    names = state['cicd_variables']['names']
    variables = []
    for variable in names:
        if variable in current_cicd_variables.keys():
            variables.append(current_cicd_variables[variable])
    return variables


def get_installed_packages(states: dict[str, StateFile]) -> set[PackageCLI]:
    """ Getting information about installed packages

    :param states: current states in GitLab repository branches
    :return: installed packages set
    """
    installed_packages = set()
    for package_states in states.values():
        for package in package_states.get_installed_packages():
            installed_packages.add(PackageCLI(name=package.name, version=package.version))
    return installed_packages


def update_created_cicd_variables(
        created_cicd_variables: list[str], response: ScriptResponse
) -> list[str]:
    response_variables = response['cicd_variables'] if response is not None else []
    for variable in response_variables:
        created_cicd_variables.append(variable['name'])
    return created_cicd_variables


def mask_data(data: str) -> str:
    encoded_bytes = base64.b64encode(data.encode("utf-8"))
    return encoded_bytes.decode("utf-8")


def unmask_data(encoded_data: str) -> str:
    decoded_bytes = base64.b64decode(encoded_data)
    return decoded_bytes.decode("utf-8")
