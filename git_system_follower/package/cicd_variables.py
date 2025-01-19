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

""" Module with api to work with CI/CD variables """
from typing import TypedDict

from gitlab.v4.objects import Project
from gitlab.base import RESTObject
from gitlab.exceptions import GitlabCreateError

from git_system_follower.logger import logger


__all__ = ['CICDVariable', 'get_cicd_variables', 'create_variable', 'delete_variable']


class CICDVariable(TypedDict):
    """ Gitlab CI/CD variables

    Dictionary items:
        - name : str | variable name
        - value : str | variable value
        - env : str | Gitlab environment in which to create variable
        - masked : bool | whether to mask variables in log messages (in Gitlab, in git-system-follower log messages)
    """
    name: str
    value: str
    env: str
    masked: bool


def get_cicd_variables(project: Project) -> dict[str, CICDVariable]:
    """ Get CI/CD variables from remote repository

    :param project: GitLab project

    :return: CI/CD variables dict: key - variable name, value - variable information
    """
    gitlab_variables = project.variables.list()
    variables = {}
    for variable in gitlab_variables:
        variables[variable.key] = CICDVariable(
            name=variable.key, value=variable.value, env=variable.environment_scope, masked=variable.masked
        )
    return variables


def create_variable(
        project: Project, variable: CICDVariable, *,
        is_force: bool
) -> RESTObject | None:
    """ Creating CI/CD variable

    :param project: Gitlab project
    :param variable: CI/CD variable to be created
    :param is_force: forced creation
    :return: Gitlab REST API response
    """
    logger.info('\t-> Creating CI/CD variables')
    is_masked = variable['masked']
    masked_value = '*****' if is_masked else variable['value']

    remote_variables: list[RESTObject] = project.variables.list()
    for remote_var in remote_variables:
        remote_masked_value = '*****' if remote_var.masked else remote_var.value
        if variable['name'] != remote_var.key:
            continue

        if variable['value'] == remote_var.value:
            logger.info(f"\t\tVariable with this name ({variable['name']}) and "
                        f"value ({masked_value}) already exist. Skip creation")
            return remote_var
        if is_force:
            remote_var.value = variable['value']
            remote_var.save()
            logger.warning(f"\t\tVariable with this name ({variable['name']}) already exist with different value "
                           f"(old value: {remote_masked_value}, new value: {masked_value}). "
                           f"Force flag enabled. Overwrote CI/CD variable")
            return remote_var
        logger.warning(f"\t\tVariable with this name ({variable['name']}) already exist with different value "
                       f"(old value: {remote_masked_value}, new value: {masked_value}). "
                       f"Force flag disabled. Skip creation/update")
        return
    try:
        variable = project.variables.create({
            'key': variable['name'], 'value': variable['value'], 'environment_scope': variable['env'],
            'masked': variable['masked']
        })
    except GitlabCreateError:
        msg = (
            f"Failed to create {variable['name']} CI/CD variable with {masked_value} value. "
            f"Please make sure you follow Gitlab's rules for CI/CD variables "
            f"https://docs.gitlab.com/ee/ci/variables/#add-a-cicd-variable-to-a-project."
        )
        if is_masked:
            msg += (" You are using variable masking. Please make sure you follow Gitlab's rules of variable masking "
                    "https://docs.gitlab.com/ee/ci/variables/#mask-a-cicd-variable")
        logger.critical(msg)
        raise
    logger.info(f"\t\tVariable with name {variable.key} with value {masked_value} has been created "
                f"in {variable.environment_scope} environment")
    logger.debug(f'\t\tResponse:\n{variable.pformat()}')
    return variable


def delete_variable(
        project: Project, variable: CICDVariable, *,
        is_force: bool
) -> None:
    """ Deleting CI/CD variable

    :param project: Gitlab project
    :param variable: CI/CD variable to be deleted
    :param is_force: forced deletion
    """
    logger.info('\t-> Deleting CI/CD variables')
    masked_value = '*****' if variable['masked'] else variable['value']

    remote_variables: list[RESTObject] = project.variables.list()
    for remote_var in remote_variables:
        remote_masked_value = '*****' if remote_var.masked else remote_var.value
        if variable['name'] != remote_var.key:
            continue

        if variable['value'] == remote_var.value:
            project.variables.delete(variable['name'])
            logger.info(f"\t\tVariable with this name ({variable['name']}) and "
                        f"value ({masked_value}) exist. Deleted it")
            return
        if is_force:
            project.variables.delete(variable['name'])
            logger.warning(f"\t\tVariable with this name ({variable['name']}) exist with different value "
                           f"(old value: {remote_masked_value}, new value: {masked_value}). "
                           f"Force flag enabled. Deleted CI/CD variable")
            return
        logger.warning(f"\t\tVariable with this name ({variable['name']}) exist with different value "
                       f"(old value: {remote_masked_value}, new value: {masked_value}). "
                       f"Force flag disabled. Skip deletion")
        return
    logger.info(f"\t\tNot found CI/CD variable with {variable['name']} name for deletion")
