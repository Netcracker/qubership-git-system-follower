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
from time import monotonic, sleep
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
    'merge_mr', 'merge_mr_and_wait', 'wait_for_pipeline', 'wait_for_validation_pipeline',
    'delete_tag', 'create_tag',
    'close_stale_mrs', 'close_mr_and_delete_branch']


# variables for waiting for an update in a remote repository
WAIT = 15
# GitLab can keep merge_status == 'checking' for a long time while it determines
# mergeability. Give it a generous hard budget (1 hour); the wait normally ends
# earlier because the check completes and merge_status flips.
MAX_WAIT = 3600
PIPELINE_WAIT = 20
PIPELINE_MAX_WAIT = 1800
PIPELINE_APPEAR_WAIT = 60
PIPELINE_VALIDATION_APPEAR_WAIT = 300  # MR validation pipeline grace period (5 min)
PIPELINE_VALIDATION_POLL_WAIT = 20  # poll interval once the validation pipeline is found
PIPELINE_VALIDATION_MAX_WAIT = 3600  # max time to wait for a found pipeline to finish (1 hour)
RUNNING_STATUSES = ('created', 'waiting_for_resource', 'preparing', 'pending', 'running')
# Merge statuses that indicate the MR is NOT blocked by pending CI or other checks.
# When no validation pipeline has appeared yet and the MR is already in one of these
# states, it means no CI pipeline is gating the merge and we can proceed immediately.
MERGE_NOT_BLOCKED = ('can_be_merged', 'mergeable', 'preparing', 'approved')


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


def close_stale_mrs(project: Project, source: str, target: str) -> None:
    """ Close open merge requests for the same source -> target pair.

    Such MRs may be left behind by a previously failed/retried run. Without this,
    re-running creates duplicate open MRs pointing at the same temp branch.

    :param project: GitLab project
    :param source: source branch
    :param target: target branch
    """
    stale_mrs = project.mergerequests.list(
        state='opened', source_branch=source, target_branch=target, get_all=True
    )
    for mr in stale_mrs:
        _close_mr(mr)


def close_mr_and_delete_branch(project: Project, mr: ProjectMergeRequest | None, branch: str) -> None:
    """ Best-effort cleanup of an un-merged MR and its source branch.

    Called when the create/merge flow fails so that neither the open merge request
    nor the temporary branch is left orphaned in the remote repository.

    :param project: GitLab project
    :param mr: merge request to close (None if the MR could not be created)
    :param branch: source/temporary branch to delete
    """
    if mr is not None:
        _close_mr(mr)
    _delete_branch(project, branch)


def _close_mr(mr: ProjectMergeRequest) -> None:
    try:
        if mr.state == 'merged':
            return
        mr.state_event = 'close'
        mr.save()
        logger.info(f'Closed merge request {mr.source_branch} -> {mr.target_branch} (url: {mr.web_url})')
    except Exception as e:
        logger.warning(f'Failed to close merge request ({mr.iid}): {e}')


def _delete_branch(project: Project, branch: str) -> None:
    try:
        project.branches.delete(branch)
        logger.info(f'Deleted temporary branch {branch}')
    except gitlab.exceptions.GitlabDeleteError:
        # if temp branch does not exist
        pass
    except Exception as e:
        logger.warning(f'Failed to delete temporary branch {branch}: {e}')


def _merge_mr(project: Project, mr: ProjectMergeRequest) -> dict:
    """ Wait until the MR is mergeable and merge it, tolerating an already-closed MR.

    GitLab auto-closes an MR when its source branch is deleted. Our own cleanup
    (close_stale_mrs / close_mr_and_delete_branch) may therefore close an MR that a
    retried/overlapping run is about to merge, making `merge()` raise
    GitlabMRClosedError (405). Instead of crashing, re-fetch the MR and:

      * if it is already merged -> treat as success
      * if it is closed without merging -> this MR was closed by our cleanup or by
        an overlapping run; a freshly re-created MR hits the same race, so fail
        fast instead of burning retry attempts.

    Also fails fast if the token lacks permission to merge, instead of waiting
    out the full MAX_WAIT budget only to have `merge()` reject it at the end.

    :param project: GitLab project
    :param mr: merge request to merge
    :return: merge response dict (possibly empty for an already-merged MR)
    """
    if mr.user and mr.user.get('can_merge') is False:
        raise RemoteRepositoryError(
            f'Token/user lacks permission to merge {mr.source_branch} -> {mr.target_branch} '
            f'(url: {mr.web_url})'
        )

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
    try:
        response = mr.merge()
    except gitlab.exceptions.GitlabMRClosedError:
        fresh_mr = project.mergerequests.get(mr.iid)
        if fresh_mr.state == 'merged':
            logger.info(f'Merge request {fresh_mr.source_branch} -> {fresh_mr.target_branch} '
                        f'was already merged (url: {fresh_mr.web_url})')
            return {}
        _raise_external_close(project, fresh_mr)
    logger.success(f'Merged {mr.source_branch} -> {mr.target_branch} (url: {mr.web_url})')
    logger.debug(f'Response:\n{pformat(response)}')
    return response


def _raise_external_close(project: Project, mr: ProjectMergeRequest) -> None:
    """ Abort immediately when a merge request is closed without being merged.

    A freshly created MR should be in an open state. When it is already closed,
    either the source branch was deleted (GitLab auto-closes MRs whose source
    branch is gone) or another process closed it. Retrying would re-create the
    same MR on the same temp branch and fail identically, so report the external
    interference instead of retrying.

    :param project: GitLab project
    :param mr: the freshly fetched (closed, un-merged) merge request
    """
    branch_exists = True
    try:
        project.branches.get(mr.source_branch)
    except gitlab.exceptions.GitlabGetError:
        branch_exists = False
    if branch_exists:
        msg = (f'Merge request {mr.source_branch} -> {mr.target_branch} is already closed without being merged '
               f'(url: {mr.web_url}).')
    else:
        msg = (f'Merge request {mr.source_branch} -> {mr.target_branch} was closed because its source branch '
               f'{mr.source_branch} no longer exists on the remote (url: {mr.web_url}).')
    logger.error(msg)
    raise RemoteRepositoryError(msg) from None


def merge_mr(project: Project, mr: ProjectMergeRequest) -> dict:
    response = _merge_mr(project, mr)
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
    response = _merge_mr(project, mr)
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


def wait_for_validation_pipeline(project: Project, mr: ProjectMergeRequest) -> None:
    """ Wait for the MR's own (merge_request_event) validation pipeline to finish.

    GitLab's "pipelines must succeed" setting gates a merge on the MR pipeline, but
    we can't rely on that project setting being enabled. Block on the MR validation
    pipeline ourselves: if it exists, wait for it to succeed before merging.

    A project without MR validation pipelines has nothing to wait on, so we proceed
    with merging after a grace period.  To avoid the full grace-period delay when a
    project genuinely has no MR pipelines, we also watch the MR's merge_status: once
    GitLab marks it as mergeable (meaning no pending checks are blocking the merge),
    we can safely proceed immediately without waiting out the full timeout.

    :param project: GitLab project
    :param mr: merge request whose validation pipeline must pass
    """
    start = monotonic()
    total = 0
    pipeline = None
    logger.info(f'Waiting for a validation pipeline on merge request {mr.source_branch} -> {mr.target_branch} '
                f'(polling every {PIPELINE_VALIDATION_POLL_WAIT} sec):')
    logger.info(f'Will proceed once merge request is mergeable with no pipeline, or merge after '
                f'{_format_elapsed(PIPELINE_VALIDATION_APPEAR_WAIT)} if no pipeline appears, '
                f'or wait up to {_format_elapsed(PIPELINE_VALIDATION_MAX_WAIT)} for a pipeline to succeed if found')

    while pipeline is None:
        sleep(PIPELINE_VALIDATION_POLL_WAIT)
        total += PIPELINE_VALIDATION_POLL_WAIT
        if total > PIPELINE_VALIDATION_APPEAR_WAIT:
            logger.info(f'No validation pipeline appeared for merge request {mr.source_branch} -> {mr.target_branch} '
                        f'within {_format_elapsed(monotonic() - start)}; proceeding to merge')
            return

        # The merge request's own pipelines endpoint only lists pipelines created for this
        # merge request (source == 'merge_request_event'), so no ref/source filtering needed
        # and we avoid paginating the whole branch pipeline history.
        pipelines = mr.pipelines.list(
            order_by='id',
            sort='desc',
            per_page=1,
            get_all=False,
        )
        elapsed = _format_elapsed(monotonic() - start)
        if pipelines:
            pipeline = project.pipelines.get(pipelines[0].id)
            logger.info(f'Found validation pipeline {pipeline.id} for merge request {mr.source_branch} -> '
                        f'{mr.target_branch} after {elapsed}')
        else:
            # No pipeline yet — check whether GitLab already considers the merge request
            # mergeable.  If so, no CI pipeline is gating this merge and there is
            # nothing to wait for.
            if mr.merge_status in MERGE_NOT_BLOCKED:
                logger.info(f'Merge request {mr.source_branch} -> {mr.target_branch} is already '
                            f'{mr.merge_status} with no validation pipeline; '
                            f'proceeding to merge after {elapsed}')
                return
            if mr.merge_status == 'checking':
                # Re-fetch to get the latest status from GitLab.
                mr = project.mergerequests.get(mr.iid)
                if mr.merge_status in MERGE_NOT_BLOCKED:
                    logger.info(f'Merge request {mr.source_branch} -> {mr.target_branch} became '
                                f'{mr.merge_status} with no validation pipeline; '
                                f'proceeding to merge after {elapsed}')
                    return
            logger.info(f'Still no validation pipeline for merge request {mr.source_branch} -> {mr.target_branch} '
                        f'(merge_status={mr.merge_status}); elapsed {elapsed}')

    while pipeline.status in RUNNING_STATUSES:
        logger.info(f'Validation pipeline {pipeline.id} status: {pipeline.status}, '
                    f'elapsed {_format_elapsed(monotonic() - start)}')
        sleep(PIPELINE_VALIDATION_POLL_WAIT)
        total += PIPELINE_VALIDATION_POLL_WAIT
        if total > PIPELINE_VALIDATION_MAX_WAIT:
            raise NeedRetry(f'Validation pipeline {pipeline.id} did not finish within '
                            f'{PIPELINE_VALIDATION_MAX_WAIT} sec')
        pipeline = project.pipelines.get(pipeline.id)

    if pipeline.status != 'success':
        raise NeedRetry(f'Validation pipeline {pipeline.id} finished with status: {pipeline.status} '
                        f'after {_format_elapsed(monotonic() - start)}')
    logger.success(f'Validation pipeline {pipeline.id} finished successfully '
                  f'in {_format_elapsed(monotonic() - start)}')


def _format_elapsed(seconds: float) -> str:
    """ Format elapsed seconds as 'Xm Ys' (or 'Ys' when under a minute). """
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if minutes:
        return f'{minutes}m {secs}s'
    return f'{secs}s'

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
