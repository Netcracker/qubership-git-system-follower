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

""" Module for executing package api """
from pathlib import Path
from enum import Enum
import importlib.util
import os
import sys
import json

from gitlab.v4.objects import Project

from git_system_follower.errors import PackageApiError
from git_system_follower.variables import PACKAGE_API_RESULT
from git_system_follower.typings.cli import ExtraParam
from git_system_follower.package.cicd_variables import CICDVariable
from git_system_follower.states import PackageState, filter_cicd_variables_by_state, unmask_data
from git_system_follower.develop.api.types import Parameters, SystemParameters, ExtraParams
from git_system_follower.package.system import get_system_info
from git_system_follower.typings.script import ScriptResponse
from git_system_follower.package.default import init_default_main, delete_default_main


__all__ = ['run_script']


class SubprocessStatus(Enum):
    ok = 0


def run_script(
        path: Path, workdir: Path, project: Project, all_cicd_variables: dict[str, CICDVariable],
        used_template: str | None, *,
        extras: tuple[ExtraParam, ...], is_force: bool, state: PackageState | None = None,
        created_cicd_variables: tuple[str, ...]
) -> ScriptResponse:
    """ Run script (package api): init/update/delete

    :param path: path to package api
    :param workdir: workdir for package api
    :param project: gitlab project
    :param all_cicd_variables: all CI/CD variables in Gitlab repository
    :param used_template: last used template
    :param created_cicd_variables: list of created CI/CD variables in previous package installations
    :param extras: extra parameters to be passed to package api
    :param is_force: forced working: create/delete CI/CI variables, create/delete template, etc.
    :param state: current state for this package with another version
    :return: script response with information: CI/CD variables, last used template, etc. after running package api
    """
    template_variables = get_template_variables(state)
    cicd_variables = filter_cicd_variables_by_state(state, all_cicd_variables)
    created_cicd_vars_in_other_pkgs = _fetch_cicd_vars_except_package(created_cicd_variables, cicd_variables)
    default_package_api = init_default_main if path.name == 'init.py' else delete_default_main
    response = execute_package_api(
        path, workdir, project, used_template,
        template_variables=template_variables,
        cicd_variables={variable['name']: variable for variable in cicd_variables},
        all_cicd_variables=all_cicd_variables, created_cicd_vars_in_other_pkgs=created_cicd_vars_in_other_pkgs,
        extras=extras, is_force=is_force,
        default=default_package_api
    )
    return response


def get_template_variables(state: PackageState | None) -> dict[str, str]:
    if state is None:
        return {}

    return {name: unmask_data(value) for name, value in state['template_variables'].items()}


def _fetch_cicd_vars_except_package(all_vars_names: tuple[str, ...], pkg_variables: list[CICDVariable]) -> list[str]:
    """ Get created CI/CD variables except current package

    :param all_vars_names: all CI/CD variables names created in repository
    :param pkg_variables: CI/CD variables created in current package of another version
    :return: CI/CD variables names except package CI/CD variable
    """
    result = []
    pkg_vars_names = [package['name'] for package in pkg_variables]
    for variable in all_vars_names:
        if variable not in pkg_vars_names:
            result.append(variable)
    return result


def execute_module(func):
    """ Wrapper for executing package api: import module, change workdir """
    def wrapper(path: Path, workdir: Path, *args, default: str | None = None, **kwargs):
        """ Wrapper for execute_module decorator

        :param path: path to package api
        :param workdir: working directory for package api
        :param default: default package api code if package api doesn't exist (for init.py, delete.py)
        """
        path = path.absolute()
        workdir = workdir.absolute()

        module = _load_module(path, default=default)
        old = os.getcwd()
        os.chdir(workdir)
        result = func(path, workdir, *args, **kwargs, module=module)
        os.chdir(old)
        os.remove(PACKAGE_API_RESULT)
        return result
    return wrapper


def _load_module(path: Path, *, default: str | None):
    if not path.exists():
        if path.name == 'update.py':
            raise PackageApiError(f'No script file. Path: {path}')
        if default is None:
            raise PackageApiError(f'Module {path} not found and no default provided')
        module = type('default_module', (), {})
        module.main = default
        return module

    # add the path with the api package so that relative import can work
    module_dir = str(path.parent)
    if module_dir not in sys.path:
        sys.path.append(module_dir)

    # add module for running package api
    spec = importlib.util.spec_from_file_location('package_api', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    func_name = 'main'
    if func_name not in dir(module):
        raise PackageApiError(f"The '{func_name}' function is missing in the module {path.absolute()}")
    if module.main.__class__.__name__ != 'function':
        raise PackageApiError(f"Object '{func_name}' is not a function in the module {path.absolute()}")
    return module


@execute_module
def execute_package_api(
        path: Path, workdir: Path, project: Project, used_template: str | None, *,
        module,
        template_variables: dict[str, str],
        cicd_variables: dict[str, CICDVariable], all_cicd_variables: dict[str, CICDVariable],
        created_cicd_vars_in_other_pkgs: list[str], extras: tuple[ExtraParam, ...], is_force: bool
) -> ScriptResponse:
    with open(PACKAGE_API_RESULT, 'w') as file:
        json.dump({
                'template': used_template,
                'template_variables': template_variables,
                'cicd_variables': [value for key, value in cicd_variables.items()]
            },
            file
        )

    system_params = SystemParameters(
        project=project, created_cicd_vars_names=created_cicd_vars_in_other_pkgs,
        script_dir=path.parent.absolute(), is_force=is_force
    )
    extras = get_remodeled_extras(extras)
    params = Parameters(
        _Parameters__system_params=system_params,  # use private class field
        system=get_system_info(project, extras),
        workdir=workdir.absolute(),
        extras=extras,
        cicd_variables=cicd_variables,
        all_cicd_variables=all_cicd_variables,
        used_template=used_template,
        template_variables=template_variables
    )
    module.main(params)

    with open(PACKAGE_API_RESULT, 'r') as file:
        content: ScriptResponse = json.load(file)
    return content


def get_remodeled_extras(extras: tuple[ExtraParam, ...]) -> ExtraParams:
    """ Get remodeled extra parameters for convenience of taking parameter by name

    from model: (
        ExtraParam(name='first_var', value='first_value', masked=True),
        ExtraParam(name='second_var', value='second_value', masked=False)
    )

    to model: {
        'first_var': ExtraParam(name='first_var', value='first_value', masked=True),
        'second_var': ExtraParam(name='second_var', value='second_value', masked=False)
    }

    :param extras: extra parameters to be passed to package api
    :return: remodeled extra parameters
    """
    return {extra.name: extra for extra in extras}
