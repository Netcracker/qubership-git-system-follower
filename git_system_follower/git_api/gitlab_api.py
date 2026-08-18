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
from typing import Optional
import sys
from gitlab import Gitlab
from gitlab.v4.objects import Project, ProjectMergeRequest
import gitlab.exceptions

from git_system_follower.logger import logger
from git_system_follower.errors import RemoteRepositoryError, HashesMismatch
from git_system_follower.states import StateFile
from git_system_follower.package.cicd_variables import get_cicd_variables_safely
from git_system_follower.package.webhooks import get_webhooks_safely
from git_system_follower.utils.retry import NeedRetry

__all__ = ['get_gitlab', 'get_project', 'get_states', 'create_mr',
    'merge_mr', 'merge_mr_and_wait', 'wait_for_pipeline', 'delete_tag', 'create_tag']


# variables for waiting for an update in a remote repository
WAIT = 4
MAX_WAIT = 60
PIPELINE_WAIT = 10
PIPELINE_MAX_WAIT = 1800
PIPELINE_APPEAR_WAIT = 60
RUNNING_STATUSES = ('created', 'waiting_for_resource', 'preparing', 'pending', 'running')


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


def get_states(project: Project, branches: tuple[str, ...],
    is_skip_project_description: bool = False,
    is_skip_project_icon: bool = False) -> dict[str, StateFile]:
    """ Get states files using GitLab REST API
    :param project: GitLab project
    :param branches: branch names listing
    :param is_skip_project_description: whether to warn instead of exit on project description mismatch
    :param is_skip_project_icon: whether to warn instead of exit on project icon mismatch
    :return: return dictionary with key - branch name, value - state file for this branch
    """
    states = {}
    remote_branches = [branch.name for branch in project.branches.list(get_all=True)]
    cicd_variables = get_cicd_variables_safely(project)
    webhooks = get_webhooks_safely(project)
    for branch in branches:
        if branch not in remote_branches:
            raise RemoteRepositoryError(f'Branch {branch} not found')

        try:
            raw = project.files.raw(file_path='.state.yaml', ref=branch)
            states[branch] = StateFile(raw=raw, current_cicd_variables=cicd_variables,
                current_webhooks=webhooks, project=project,
                is_skip_project_description=is_skip_project_description,
                is_skip_project_icon=is_skip_project_icon)
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

def merge_mr_and_wait(project: Project, mr: ProjectMergeRequest, *, tag_name: str | None = None) -> dict:
    """Merge MR, optionally create a tag, and wait for the triggered pipeline on the target branch"""
    old_pipelines = project.pipelines.list(
        ref=mr.target_branch,
        order_by='id',
        sort='desc',
        per_page=1,
        get_all=False  # Explicitly say you only want 1 item
    )
    old_id = old_pipelines[0].id if old_pipelines else None
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
    if tag_name:
        create_tag(project, mr.target_branch, tag_name)
        wait_ref = tag_name
        wait_ref_type = 'tag'
    else:
        wait_ref = mr.target_branch
        wait_ref_type = 'branch'
    total = 0
    pipeline = None

    while pipeline is None:
        sleep(PIPELINE_WAIT)
        total += PIPELINE_WAIT
        if total > PIPELINE_APPEAR_WAIT:
            raise RemoteRepositoryError(
                f'No new pipeline appeared for {wait_ref_type} {wait_ref} within {PIPELINE_APPEAR_WAIT} sec')

        current_pipelines = project.pipelines.list(
            ref=wait_ref,
            order_by='id',
            sort='desc',
            per_page=5,
            get_all=False
        )
        logger.debug(f'old_id={old_id}, current pipeline ids={[p.id for p in current_pipelines]}')
        for p in current_pipelines:
            if p.id != old_id:
                pipeline = project.pipelines.get(p.id)
                logger.info(f'Found new pipeline {pipeline.id} on {wait_ref_type} {wait_ref}')
                break

    while pipeline.status in RUNNING_STATUSES:
        logger.debug(f'Pipeline {pipeline.id} status: {pipeline.status}, waiting ({PIPELINE_WAIT} sec)')
        sleep(PIPELINE_WAIT)
        total += PIPELINE_WAIT
        if total > PIPELINE_MAX_WAIT:
            raise RemoteRepositoryError(f'Pipeline {pipeline.id} did not finish within {PIPELINE_MAX_WAIT} sec')
        pipeline = project.pipelines.get(pipeline.id)

    if pipeline.status != 'success':
        logger.error(f'Pipeline {pipeline.id} finished with status: {pipeline.status}')
        sys.exit(1)
    logger.success(f'Pipeline {pipeline.id} finished successfully')
    return response

def wait_for_pipeline(project: Project, ref: str, ref_type: str = 'branch',
    pipeline_source: Optional[str] = None) -> None:
    """
    Wait for a pipeline to complete with flexible filtering
    :param project: GitLab project
    :param ref: branch or tag name
    :param ref_type: 'branch' or 'tag'
    :param pipeline_source: 'push', 'web', 'merge_request_event', etc.
    """
    total = 0
    pipeline = None

    logger.info(f'Waiting for pipeline on {ref_type} {ref} to appear')

    while pipeline is None:
        sleep(PIPELINE_WAIT)
        total += PIPELINE_WAIT
        if total > PIPELINE_APPEAR_WAIT:
            raise RemoteRepositoryError(
                f'No pipeline appeared for {ref_type} {ref} within {PIPELINE_APPEAR_WAIT} sec'
            )

        # List pipelines with filters
        pipelines = project.pipelines.list(
            ref=ref,
            order_by='id',
            sort='desc',
            per_page=20
        )

        # Filter by source if specified
        if pipeline_source and pipelines:
            pipelines = [p for p in pipelines if p.source == pipeline_source]

        # Get the most recent relevant pipeline
        if pipelines:
            pipeline = project.pipelines.get(pipelines[0].id)
            logger.info(f'Found pipeline {pipeline.id} for {ref_type} {ref}')
            break

    if pipeline is None:
        raise RemoteRepositoryError(f'No pipeline found for {ref_type} {ref}')

    # Wait for completion
    logger.info(f'Pipeline {pipeline.id} found for {ref}, waiting for completion')
    while pipeline.status in RUNNING_STATUSES:
        logger.debug(f'Pipeline {pipeline.id} status: {pipeline.status}, waiting ({PIPELINE_WAIT} sec)')
        sleep(PIPELINE_WAIT)
        total += PIPELINE_WAIT
        if total > PIPELINE_MAX_WAIT:
            raise RemoteRepositoryError(
                f'Pipeline {pipeline.id} for {ref} did not finish within {PIPELINE_MAX_WAIT} sec'
            )
        pipeline = project.pipelines.get(pipeline.id)

    if pipeline.status != 'success':
        logger.error(f'Pipeline {pipeline.id} for {ref} finished with status: {pipeline.status}')
        sys.exit(1)
    logger.success(f'Pipeline {pipeline.id} for {ref} finished successfully')

def delete_tag(project: Project, version: str) -> dict | None:
    try:
        tag = project.tags.get(version)
    except gitlab.GitlabError as e:
        logger.warning(e)
        return None

    response = tag.delete()
    logger.success(f'Deleted tag {version} on {project.path_with_namespace} (release removed automatically)')
    logger.debug(f'Response:\n{pformat(response)}')
    return response


def create_tag(project: Project, ref: str, tag_name: str) -> None:
    try:
        project.tags.create({'tag_name': tag_name, 'ref': ref})
    except gitlab.GitlabError as e:
        logger.warning(f'Failed to create tag {tag_name} on {ref}: {e}')
        return
    logger.success(f'Created tag {tag_name} on {ref} ({project.path_with_namespace})')
