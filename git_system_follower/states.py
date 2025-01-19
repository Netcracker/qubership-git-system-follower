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
from typing import TypedDict, Any
from enum import Enum
from pathlib import Path
import hashlib
from datetime import datetime

import yaml

from git_system_follower.logger import logger
from git_system_follower.package_manager.errors import HashesMismatch
from git_system_follower.package_manager.typings.package import PackageLocalData
from git_system_follower.package_manager.typings.script import ScriptResponse
from git_system_follower.package_manager.package.cicd_variables import CICDVariable


__all__ = [
    'STATE_FILE_NAME', 'ChangeStatus', 'PackageState',
    'read_raw_state_file', 'save_state_file', 'get_package_in_states', 'add_package_to_state',
    'get_created_cicd_variables', 'get_state_file_current_cicd_variables', 'update_created_cicd_variables'
]


STATE_FILE_NAME = '.state.yaml'


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


def read_raw_state_file(raw: bytes, current_cicd_variables: dict[str, CICDVariable]) -> list[PackageState]:
    """ Read raw state file (e.g. from GitLab REST API)

    :param: raw state file
    :param: raw state file

    :return: state ('packages' section) from state file
    """
    content: StateFileContent = yaml.safe_load(raw)
    computed_hash = _get_hash(content['packages'])
    if content['hash'] != computed_hash:
        raise HashesMismatch(f"Hash specified in state file ({content['hash']}) and "
                             f"generated hash ({computed_hash}) do not match",
                             state_file_hash=content['hash'], generated_hash=computed_hash)

    for package in content['packages']:
        _check_cicd_variables_hash(package, current_cicd_variables)
    return content['packages']


def _check_cicd_variables_hash(package: PackageState, current_cicd_variables: dict[str, CICDVariable]) -> None:
    """ Check hash for CI/CD variables of <package>

    :param package: package with information about variable names
    :param current_cicd_variables: current CI/CD variables in Gitlab
    """
    variables = get_state_file_current_cicd_variables(package, current_cicd_variables)
    computed_hash = _get_hash(variables)
    if computed_hash != package['cicd_variables']['hash']:
        raise HashesMismatch(f"CI/CD variables hash specified in state file in "
                             f"{package['name']}@{package['version']} package ({package['cicd_variables']['hash']}) "
                             f"and generated hash ({computed_hash}) do not match",
                             state_file_hash=package['cicd_variables']['hash'], generated_hash=computed_hash)


def get_state_file_current_cicd_variables(
        state: PackageState | None, current_cicd_variables: dict[str, CICDVariable]
) -> list[CICDVariable]:
    """ Get current CI/CD variables state (name, value, env, etc.) for CI/CD variables specified in state file

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


def save_state_file(directory: Path, state: list[PackageState]) -> None:
    """ Save state file

    :param directory: path where state file will be saved
    :param state: state ('packages' section) for state file
    """
    path = directory / STATE_FILE_NAME
    computed_hash = _get_hash(state)
    content = StateFileContent(hash=computed_hash, packages=state)
    logger.debug(f'New hash generated: {computed_hash}')
    with open(path, 'w') as file:
        yaml.dump(content, file)


def _get_hash(state: Any) -> str:
    """ Generate hash for any variable. For example, for 'packages' section in state file, for 'cicd_variables' section

    :param state: state ('packages' section) from state file

    :return: generated hash
    """
    sorted_state = _sort_state(state)  # sort for the same behaviour when working with hash for saving/reading
    string = str(sorted_state)
    return hashlib.sha256(string.encode()).hexdigest()


def _sort_state(state: list[PackageState] | PackageState):
    if isinstance(state, list):
        return [_sort_state(item) for item in state]
    elif isinstance(state, dict):
        return {key: _sort_state(value) for key, value in sorted(state.items())}
    else:
        return state


def get_package_in_states(
    package: PackageLocalData, states: list[PackageState], *, is_delete: bool
) -> PackageState | None:
    """ Get state with package from state

    :param package: package which need to find in states
    :param states: current states from state file
    :param is_delete: is need to find package to delete (or to install)

    :return: found package
    """
    if is_delete:
        return get_package_in_states_by_name_and_version(package, states)
    return get_package_in_states_by_name(package, states)


def get_created_cicd_variables(states: list[PackageState]) -> list[str]:
    """ Get created CI/CD variables from state file

    :param states: installed packages state
    :return: list of CI/CD variables names
    """
    variables = []
    for state in states:
        variables.extend(state['cicd_variables']['names'])
    return variables


def update_created_cicd_variables(
        created_cicd_variables: list[str], response: ScriptResponse
) -> list[str]:
    response_variables = response['cicd_variables'] if response is not None else []
    for variable in response_variables:
        created_cicd_variables.append(variable['name'])
    return created_cicd_variables


def get_package_in_states_by_name(
        package: PackageLocalData, states: list[PackageState]
) -> PackageState | None:
    """ Get state with package from state by name

    :param package: package which need to find in states
    :param states: current states from state file

    :return: found package by name
    """
    for state in states:
        if package['name'] == state['name']:
            return state


def get_package_in_states_by_name_and_version(
        package: PackageLocalData, states: list[PackageState]
) -> PackageState | None:
    """ Get state with package from state by name

    :param package: package which need to find in states
    :param states: current states from state file

    :return: found package by name and version
    """
    for state in states:
        if package['name'] == state['name'] and package['version'] == state['version']:
            return state


def add_package_to_state(
        package: PackageLocalData, response: ScriptResponse | None,
        state: PackageState | None, states: list[PackageState]
) -> list[PackageState]:
    """ Add package to state file

    :param package: package which need to add to state file
    :param response: script response with information about used template, used ci/cd variables
    :param state: current state from state file (if package already installed but another versions)
    :param states: updated state file content
    """
    if response is None:
        return states

    variables_names = [variable['name'] for variable in response['cicd_variables']]
    variables = response['cicd_variables'] if response is not None else []
    data = PackageState(
        name=package['name'], version=package['version'],
        used_template=response['template'],
        template_variables=response['template_variables'],
        last_update=str(datetime.now()),
        dependencies=[f"{dependency.name}@{dependency.version}" for dependency in package['dependencies']],
        cicd_variables=CICDVariablesSection(
            names=variables_names,
            hash=_get_hash(variables)
        )
    )
    if state is None:
        states.append(data)
        return states
    index = states.index(state)
    states[index] = data
    return states
