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
from cookiecutter.exceptions import RepositoryNotFound
from git_system_follower.logger import logger
from git_system_follower.develop.api.types import Parameters, ExtraParams, ExtraParam
from git_system_follower.develop.api.cicd_variables import CICDVariable, create_variable, delete_variable
from git_system_follower.variables import PACKAGE_API_RESULT as __PACKAGE_API_RESULT
from git_system_follower.errors import PackageAPIDevelopmentError, PackageTemplatePolicyError, PackageApiError
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
        is_force: bool = False, skip_files: tuple[str, ...] = ()
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
        system_params.script_dir, name, parameters.workdir, variables=variables,
        is_autoheal=system_params.is_autoheal, skip_files=skip_files, is_force=is_force
    )


def update_template(
        parameters: Parameters, variables: Optional[ExtraParams | dict[str, str]] = None, *,
        is_force: bool = False, skip_files: tuple[str, ...] = ()
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
    template_param = parameters.extras.get("TEMPLATE")
    used_template = template_param.value if template_param is not None else parameters.used_template
    updated_variables = {}
    try:
        updated_variables = __execute_template_update(parameters, used_template, variables, is_force, skip_files)
    except (PackageApiError, RepositoryNotFound) as e:
        if 'Template is missing' in str(e) or isinstance(e, RepositoryNotFound):
            logger.warning(f"Template '{used_template}' not found, retrying with {parameters.used_template}")
            updated_variables = __execute_template_update(parameters, parameters.used_template, variables,
                is_force, skip_files)
        else:
            raise
    finally:
        update_cicd_variables(parameters, list(updated_variables.keys()))


def delete_template(parameters: Parameters, *, is_force: bool = False, skip_files: tuple[str, ...] = ()) -> None:
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
        variables=parameters.template_variables, skip_files=skip_files, is_force=is_force
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


def __update_template_variables(template: str, variables: dict[str, str] | None) -> dict[str, str]:
    with open(__PACKAGE_API_RESULT, 'r') as file:
        content = json.load(file)
    content['template'] = template
    content['template_variables'] = __get_variables(variables)
    with open(__PACKAGE_API_RESULT, 'w') as file:
        json.dump(content, file)
    return content['template_variables']


def __delete_info_about_template() -> None:
    with open(__PACKAGE_API_RESULT, 'r') as file:
        content = json.load(file)
    if content['template'] is None:
        raise PackageTemplatePolicyError('No template was used, nothing to delete')
    content['template'] = None
    content['template_variables'] = []
    with open(__PACKAGE_API_RESULT, 'w') as file:
        json.dump(content, file)

def __execute_template_update(
        parameters: Parameters, used_template: str, variables: Optional[ExtraParams | dict[str, str]],
        is_force: bool, skip_files: tuple[str, ...]
) -> dict[str, str]:
    system_params = parameters._Parameters__system_params
    updated_variables = __update_template_variables(used_template, variables)
    __create_template(
        system_params.script_dir, used_template, parameters.workdir, variables=updated_variables,
        is_autoheal=system_params.is_autoheal, skip_files=skip_files, is_force=is_force,
        current_version_dir=parameters.current_version_dir
    )
    return updated_variables


def __get_variables(variables: Optional[ExtraParams | dict[str, str]] = None) -> dict[str, str]:
    """ Get variables for generate template and save these variables to state file

    Convert ExtraParams to dict[str, str]

    :param variables: A dict of parameters used to generate the template. Which will be saved in the state file
    :return: dict of variables
    """
    if variables is None:
        return {}

    if not isinstance(variables, dict):
        error = f"Invalid variables type. 'dict' or 'ExtraParams' is required. Current type={type(variables)}"
        raise PackageAPIDevelopmentError(error)
    elif all(isinstance(k, str) and isinstance(v, str) for k, v in variables.items()):
        return variables
    elif all(isinstance(k, str) and isinstance(v, ExtraParam) for k, v in variables.items()):
        return {variable.name: variable.value for variable in variables.values()}
    raise PackageAPIDevelopmentError('Invalid variables value type')


def update_cicd_variables(parameters: Parameters, template_variables_names: list[str]) -> None:
    for name, extra in parameters.extras.items():
        if name in template_variables_names:
            continue

        if name in parameters.cicd_variables:
            delete_variable(parameters, parameters.cicd_variables[name])
        create_variable(parameters, CICDVariable(
            name=extra.name,
            value=extra.value,
            env='*',
            masked=extra.masked
        ))
