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

""" Module with api to work with CI/CD variables for package developers """
import json

from gitlab.base import RESTObject

from git_system_follower.variables import PACKAGE_API_RESULT as __PACKAGE_API_RESULT
from git_system_follower.develop.api.types import Parameters
from git_system_follower.errors import PackageCICDVariablePolicyError
from git_system_follower.package.cicd_variables import (
    CICDVariable,
    create_variable as __create_variable,
    delete_variable as __delete_variable
)


__all__ = ['CICDVariable', 'create_variable', 'delete_variable']


def create_variable(parameters: Parameters, variable: CICDVariable, *, is_force: bool = False) -> RESTObject | None:
    """ Create CI/CD variable using gitlab REST API

    If <is_force> parameter is False, then it will necessarily be safe to create CI/CD variable:
        1. If CI/CD variable doesn't exist: create CI/CD variable
        2. If CI/CD variable exists:
            1. CI/CD variables values doesn't match: notification of this (warning)
            2. CI/CD variables values matches: notification of this (info)

    If <is_force> parameter is True, then it will necessarily be force to create CI/CD variable:
        1. If CI/CD variable doesn't exist: create CI/CD variable
        2. If CI/CD variable exists:
            1. CI/CD variables values doesn't match: overwrite this CI/CD variable, notification of this (warning)
            2. CI/CD variables values content matches: notification of this (info)

    :param parameters: parameters that were passed to the package api
    :param variable: CI/CD variable to be created
    :param is_force: forced creation (ignore variable value)

    :return: creation response if variable is created
    """
    system_params = parameters._Parameters__system_params
    if variable['name'] in system_params.created_cicd_vars_names:
        raise PackageCICDVariablePolicyError(f"{variable['name']} CI/CD variable used in another package. According "
                                             f"to package manager policy, you cannot use the same variables in "
                                             f"different packages")

    is_force = True if is_force or system_params.is_force else False
    response = __create_variable(
        system_params.project, variable, is_force=is_force
    )
    __add_info_about_variable(variable)
    return response


def delete_variable(parameters: Parameters, variable: CICDVariable, *, is_force: bool = False) -> None:
    """ Delete CI/CD variable using gitlab REST API

    If <is_force> parameter is False, then it will necessarily be safe to delete CI/CD variable:
        1. If CI/CD variable doesn't exist: do nothing
        2. If CI/CD variable exists:
            1. CI/CD variables values doesn't match: notification of this (warning)
            2. CI/CD variables value matches: delete this CI/CD variable, notification of this (info)

    If <is_force> parameter is True, then it will necessarily be force to delete CI/CD variable:
        1. If CI/CD variable doesn't exist: do nothing
        2. If CI/CD variable exists:
            1. CI/CD variables values doesn't match: delete this file, notification of this (warning)
            2. CI/CD variables values matches: delete this file, notification of this (info)

    :param parameters: parameters that were passed to the package api
    :param variable: CI/CD variable to be deleted
    :param is_force: forced deletion (ignore variable value)
    """
    system_params = parameters._Parameters__system_params
    if variable['name'] in system_params.created_cicd_vars_names:
        raise PackageCICDVariablePolicyError(f"{variable['name']} CI/CD variable used in another package. According "
                                             f"to package manager policy, you cannot use the same variables in "
                                             f"different packages")

    is_force = True if is_force or system_params.is_force else False
    __delete_variable(
        system_params.project, variable, is_force=is_force
    )
    __delete_info_about_variable(variable)


def __add_info_about_variable(variable: CICDVariable) -> None:
    with open(__PACKAGE_API_RESULT, 'r') as file:
        content = json.load(file)
    if variable not in content['cicd_variables']:
        content['cicd_variables'].append(variable)
    with open(__PACKAGE_API_RESULT, 'w') as file:
        json.dump(content, file)


def __delete_info_about_variable(variable: CICDVariable) -> None:
    with open(__PACKAGE_API_RESULT, 'r') as file:
        content = json.load(file)
    if variable not in content['cicd_variables']:
        return
    index = content['cicd_variables'].index(variable)
    content['cicd_variables'].pop(index)
    with open(__PACKAGE_API_RESULT, 'w') as file:
        json.dump(content, file)
