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

""" Module for working with GitLab REST API """
from urllib.parse import urlparse
from time import sleep
from pprint import pformat

from gitlab import Gitlab
from gitlab.v4.objects import Project, ProjectMergeRequest
import gitlab.exceptions

from git_system_follower.logger import logger
from git_system_follower.errors import RemoteRepositoryError, HashesMismatch
from git_system_follower.states import StateFile
from git_system_follower.package.cicd_variables import get_cicd_variables
from git_system_follower.utils.retry import NeedRetry


__all__ = ['get_gitlab', 'get_project', 'get_states', 'create_mr', 'merge_mr']


# variables for waiting for an update in a remote repository
WAIT = 4
MAX_WAIT = 60


def get_gitlab(url: str, token: str) -> Gitlab:
    """ Get gitlab instance for working with GitLab REST API
    :param url: any gitlab url
    :param token: gitlab access token
    """
    url = _shorten_url(url)
    instance = Gitlab(url, private_token=token)
    instance.auth()
    return instance


def _shorten_url(url: str) -> str:
    parsed = urlparse(url)
    return f'{parsed.scheme}://{parsed.netloc}'


def get_project(instance: Gitlab, url: str) -> Project:
    project_with_namespace = urlparse(url).path[1:].replace('.git', '')
    try:
        project = instance.projects.get(project_with_namespace)
    except gitlab.exceptions.GitlabGetError:
        raise RemoteRepositoryError(f'Project/repository {url} not found')
    except gitlab.exceptions.GitlabAuthenticationError:
        raise RemoteRepositoryError(f'Failed to auth in {url} repository')
    return project


def get_states(project: Project, branches: tuple[str, ...]) -> dict[str, StateFile]:
    """ Get states files using GitLab REST API

    :param project: GitLab project
    :param branches: branch names listing

    :return: return dictionary with key - branch name, value - state file for this branch
    """
    states = {}
    remote_branches = [branch.name for branch in project.branches.list(get_all=True)]
    cicd_variables = get_cicd_variables(project)
    for branch in branches:
        if branch not in remote_branches:
            raise RemoteRepositoryError(f'Branch {branch} not found')

        try:
            raw = project.files.raw(file_path='.state.yaml', ref=branch)
            states[branch] = StateFile(raw=raw, current_cicd_variables=cicd_variables)
        except gitlab.exceptions.GitlabGetError:
            states[branch] = StateFile()
        except HashesMismatch as error:
            logger.critical(f'Hashes do not match for {branch} branch. Most likely, someone changed the state file '
                            f'manually, this is forbidden by package manager policy. Please reset everything back to '
                            f'its original state and start again. '
                            f'State file hash: {error.state_file_hash} != {error.generated_hash}: Generated hash')
            raise
    return states


def create_mr(
        project: Project, source: str, target: str, *,
        title: str = 'Install package(s)', description: str = ''
) -> ProjectMergeRequest:
    # Merge Request is auto closed when a branch is deleted
    mr = project.mergerequests.create({
        'source_branch': source,
        'target_branch': target,
        'title': title,
        'description': description,
        'squash': True,
        'remove_source_branch': True
    })
    logger.success(f'Created merge requests {source} -> {target} (url: {mr.web_url})')
    logger.debug(f'Response:\n{mr.pformat()}')
    mr = project.mergerequests.get(mr.iid)
    return mr


def merge_mr(project: Project, mr: ProjectMergeRequest) -> dict:
    total = 0
    while mr.merge_status == 'checking':
        logger.debug(f'Waiting to be able to merge ({WAIT} sec)')
        sleep(WAIT)
        mr = project.mergerequests.get(mr.iid)
        total += WAIT
        if total > MAX_WAIT:
            raise RemoteRepositoryError(f'Waiting too long for a merger opportunity ({MAX_WAIT} sec)')

    if mr.has_conflicts:
        raise NeedRetry(f'Cannot merge {mr.source_branch} -> {mr.target_branch} because there are conflicts')
    response = mr.merge()
    logger.success(f'Merged {mr.source_branch} -> {mr.target_branch} (url: {mr.web_url})')
    logger.debug(f'Response:\n{pformat(response)}')
    return response
