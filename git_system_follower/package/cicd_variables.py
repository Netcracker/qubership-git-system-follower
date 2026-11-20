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
import re
from typing import TypedDict

from gitlab.v4.objects import Project
from gitlab.base import RESTObject
from gitlab.exceptions import GitlabCreateError, GitlabError

from git_system_follower.logger import logger


__all__ = ['CICDVariable', 'get_cicd_variables', 'create_variable', 'delete_variable']


class _CICDVariableOptional(TypedDict, total=False):
    expanded: bool | None


class CICDVariable(_CICDVariableOptional):
    """ Gitlab CI/CD variables

    Dictionary items:
        - name : str | variable name
        - value : str | variable value
        - env : str | Gitlab environment in which to create variable
        - masked : bool | whether to mask variables in log messages (in Gitlab, in git-system-follower log messages)
        - expanded : bool | None | whether variable references are expanded (raw=false) or treated as raw (raw=true).
            If omitted/None, default is chosen by GitLab version: expanded before 18.6, raw since 18.6
    """
    name: str
    value: str
    env: str
    masked: bool


def get_default_expanded(project: Project) -> bool | None:
    """ Default `expanded` matching GitLab server default for `raw` (expanded before 18.6, raw since 18.6)

    :return: default value or None if GitLab version can't be determined (`raw` is then not sent)
    """
    try:
        version = project.manager.gitlab.version()[0]
        major, minor = (int(part) for part in re.match(r'(\d+)\.(\d+)', version).groups())
    except Exception:
        logger.debug('Unable to determine GitLab version. Server default for variable expansion will be used')
        return None
    return (major, minor) < (18, 6)


def get_cicd_variables(project: Project) -> dict[str, CICDVariable]:
    """ Get CI/CD variables from remote repository

    :param project: GitLab project

    :return: CI/CD variables dict: key - variable name, value - variable information
    """
    gitlab_variables = project.variables.list(iterator=True)
    variables = {}
    for variable in gitlab_variables:
        variables[variable.key] = CICDVariable(
            name=variable.key, value=variable.value, env=variable.environment_scope,
            masked=variable.masked, expanded=not variable.raw
        )
    return variables


def get_cicd_variables_safely(project: Project) -> dict[str, CICDVariable] | None:
    """ Get CI/CD variables tolerating insufficient token permissions

    Reading project CI/CD variables requires at least the Maintainer role. When
    the token cannot read them (e.g. a Developer token for a gear that does not
    use variables at all) this returns None instead of failing, so the run can
    proceed. The actual need for Maintainer is enforced at the execution point
    by git_system_follower.package.permissions.check_token_permissions.

    :param project: GitLab project
    :return: CI/CD variables dict or None if they could not be read
    """
    try:
        return get_cicd_variables(project)
    except GitlabError as e:
        logger.debug(f"Failed to read CI/CD variables ({e}). Treating them as unavailable.")
        return None


def create_variable(
        project: Project, variable: CICDVariable, *,
        is_force: bool
) -> CICDVariable:
    """ Creating CI/CD variable

    :param project: Gitlab project
    :param variable: CI/CD variable to be created
    :param is_force: forced creation
    :return: Gitlab REST API response
    """
    logger.info('\t-> Creating CI/CD variables')
    is_masked = variable['masked']
    masked_value = '*****' if is_masked else variable['value']

    remote_variables: list[RESTObject] = project.variables.list(iterator=True)
    for remote_var in remote_variables:
        remote_masked_value = '*****' if remote_var.masked else remote_var.value
        if variable['name'] != remote_var.key:
            continue

        if variable['value'] == remote_var.value:
            logger.info(f"\t\tVariable with this name ({variable['name']}) and "
                        f"value ({masked_value}) already exist. Skip creation")
            return _serialize_var(remote_var)
        if is_force:
            remote_var.value = variable['value']
            remote_var.save()
            logger.warning(f"\t\tVariable with this name ({variable['name']}) already exist with different value "
                           f"(old value: {remote_masked_value}, new value: {masked_value}). "
                           f"Force flag enabled. Overwrote CI/CD variable")
            return _serialize_var(remote_var)
        logger.warning(f"\t\tVariable with this name ({variable['name']}) already exist with different value "
                       f"(old value: {remote_masked_value}, new value: {masked_value}). "
                       f"Force flag disabled. Skip creation/update")
        return _serialize_var(remote_var)
    expanded = variable.get('expanded')
    if expanded is None:
        expanded = get_default_expanded(project)
    payload = {
        'key': variable['name'], 'value': variable['value'], 'environment_scope': variable['env'],
        'masked': variable['masked']
    }
    if expanded is not None:
        payload['raw'] = not expanded
    try:
        variable = project.variables.create(payload)
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
    return _serialize_var(variable)


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

    remote_variables: list[RESTObject] = project.variables.list(iterator=True)
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

def _serialize_var(remote_var: RESTObject)-> CICDVariable:
    return CICDVariable(
        name = remote_var.key,
        value = remote_var.value,
        env = remote_var.environment_scope,
        masked = remote_var.masked,
        expanded = not remote_var.raw
    )
