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

""" Module with api to work with templates for package developers """
import json
from typing import Optional

from git_system_follower.develop.api.types import Parameters, ExtraParams, ExtraParam
from git_system_follower.variables import PACKAGE_API_RESULT as __PACKAGE_API_RESULT
from git_system_follower.errors import PackageAPIDevelopmentError, PackageTemplatePolicyError
from git_system_follower.package.templates import (
    get_template_names as __get_template_names,
    create_template as __create_template,
    delete_template as __delete_template
)


__all__ = ['get_template_names', 'create_template', 'update_template', 'delete_template']


def get_template_names(parameters: Parameters) -> tuple[str, ...]:
    """ Get available template names

    :param parameters: parameters that were passed to the package api
    :returns: tuple of template names
    """
    system_params = parameters._Parameters__system_params
    return __get_template_names(system_params.script_dir)


def create_template(
        parameters: Parameters, name: str, variables: Optional[ExtraParams | dict[str, str]] = None, *,
        is_force: bool = False
) -> None:
    """ Create files using cookiecutter template

    If <is_force> parameter is False, then it will necessarily be safe to create files using template:
        1. If file doesn't exist: create file
        2. If file exists:
            1. Files content doesn't match: notification of this (warning)
            2. Files content matches: notification of this (info)

    If <is_force> parameter is True, then it will necessarily be force to create files using template:
        1. If file doesn't exist: create file
        2. If file exists:
            1. Files content doesn't match: overwrite this file, notification of this (warning)
            2. Files content matches: notification of this (info)

    :param parameters: parameters that were passed to the package api
    :param name: name of template to be created
    :param variables: A dict of parameters used to generate the template. Which will be saved in the state file
    :param is_force: forced creation (ignore file content)
    """
    system_params = parameters._Parameters__system_params
    is_force = True if is_force or system_params.is_force else False
    variables = __get_variables(variables)
    __add_info_about_template(name, variables)
    __create_template(
        system_params.script_dir, name, parameters.workdir,
        variables=variables, is_force=is_force
    )


def update_template(
        parameters: Parameters, variables: Optional[ExtraParams | dict[str, str]] = None, *,
        is_force: bool = False
) -> None:
    """ Update files using cookiecutter template

    If <is_force> parameter is False, then it will necessarily be safe to update files using template:
        1. If file doesn't exist: create file
        2. If file exists: do nothing
            1. Files content doesn't match: notification of this (warning)
            2. Files content matches: notification of this (info)

    If <is_force> parameter is True, then it will necessarily be force to update files using template:
        1. If file doesn't exist: create file
        2. If file exists:
            1. Files content doesn't match: overwrite this file, notification of this (warning)
            2. Files content matches: notification of this (info)

    :param parameters: parameters that were passed to the package api
    :param variables: A dict of parameters used to generate the template. Which will be saved in the state file
    :param is_force: forced creation (ignore file content)
    """
    system_params = parameters._Parameters__system_params
    is_force = True if is_force or system_params.is_force else False
    variables = __update_template_variables(variables)
    __create_template(
        system_params.script_dir, parameters.used_template, parameters.workdir,
        variables=variables, is_force=is_force
    )


def delete_template(parameters: Parameters, *, is_force: bool = False) -> None:
    """ Delete files using cookiecutter template

    If <is_force> parameter is False, then it will necessarily be safe to delete files using template:
        1. If file doesn't exist: do nothing
        2. If file exists:
            1. Files content doesn't match: notification of this (warning)
            2. Files content matches: delete this file, notification of this (info)

    If <is_force> parameter is True, then it will necessarily be force to delete files using template:
        1. If file doesn't exist: do nothing
        2. If file exists:
            1. Files content doesn't match: delete this file, notification of this (warning)
            2. Files content matches: delete this file, notification of this (info)

    :param parameters: parameters that were passed to the package api
    :param is_force: forced deletion (ignore file content)
    """
    system_params = parameters._Parameters__system_params
    is_force = True if is_force or system_params.is_force else False
    __delete_info_about_template()
    __delete_template(
        system_params.script_dir, parameters.used_template, parameters.workdir,
        variables=parameters.template_variables, is_force=is_force
    )


def __add_info_about_template(template: str, variables: dict[str, str]) -> None:
    with open(__PACKAGE_API_RESULT, 'r') as file:
        content = json.load(file)
    if content['template'] is not None:
        raise PackageTemplatePolicyError('You cannot create multiple templates, only one')
    content['template'] = template
    content['template_variables'] = variables
    with open(__PACKAGE_API_RESULT, 'w') as file:
        json.dump(content, file)


def __update_template_variables(variables: dict[str, str]) -> dict[str, str]:
    with open(__PACKAGE_API_RESULT, 'r') as file:
        content = json.load(file)
    template_variables = content['template_variables'].copy()
    template_variables.update(__get_variables(variables))
    content['template_variables'] = template_variables
    with open(__PACKAGE_API_RESULT, 'w') as file:
        json.dump(content, file)
    return template_variables


def __delete_info_about_template() -> None:
    with open(__PACKAGE_API_RESULT, 'r') as file:
        content = json.load(file)
    if content['template'] is None:
        raise PackageTemplatePolicyError('No template was used, nothing to delete')
    content['template'] = None
    content['template_variables'] = []
    with open(__PACKAGE_API_RESULT, 'w') as file:
        json.dump(content, file)


def __get_variables(variables: Optional[ExtraParams | dict[str, str]] = None) -> dict[str, str]:
    """ Get variables for generate template and save these variables to state file

    Convert ExtraParams to dict[str, str]

    :param variables: A dict of parameters used to generate the template. Which will be saved in the state file
    :return: dict of variables
    """
    if variables is None:
        return {}

    if not isinstance(variables, dict):
        raise PackageAPIDevelopmentError(f"Invalid variables type. 'dict' or 'ExtraParams' is required. "
                                         f"Current type={type(variables)}")
    elif all(isinstance(k, str) and isinstance(v, str) for k, v in variables.items()):
        return variables
    elif all(isinstance(k, str) and isinstance(v, ExtraParam) for k, v in variables.items()):
        return {variable.name: variable.value for variable in variables.values()}
    else:
        raise PackageAPIDevelopmentError('Invalid variables value type')
