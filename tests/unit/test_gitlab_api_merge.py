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

"""Tests for merge_mr's tolerance of an already-closed MR in git_api.gitlab_api."""

from unittest.mock import Mock, patch

import gitlab.exceptions
import pytest

from git_system_follower.errors import RemoteRepositoryError
from git_system_follower.git_api.gitlab_api import merge_mr, wait_for_validation_pipeline
from git_system_follower.utils.retry import NeedRetry


def _make_mr(**overrides):
    mr = Mock()
    mr.merge_status = 'can_be_merged'
    mr.has_conflicts = False
    mr.iid = 1
    mr.source_branch = 'main.temp-manage-packages'
    mr.target_branch = 'main'
    mr.web_url = 'http://gitlab/project/-/merge_requests/1'
    mr.user = {'can_merge': True}
    for key, value in overrides.items():
        setattr(mr, key, value)
    return mr


def _make_pipeline(status, iid=1):
    pipeline = Mock(id=iid)
    pipeline.status = status
    pipeline.source = 'merge_request_event'
    return pipeline


@pytest.mark.unit
def test_merge_succeeds_normally():
    project = Mock()
    mr = _make_mr()
    mr.merge.return_value = {'merged': True}

    response = merge_mr(project, mr)

    assert response == {'merged': True}
    mr.merge.assert_called_once()


@pytest.mark.unit
def test_conflicts_raise_needretry_without_attempting_merge():
    project = Mock()
    mr = _make_mr(has_conflicts=True)

    with pytest.raises(NeedRetry):
        merge_mr(project, mr)

    mr.merge.assert_not_called()


@pytest.mark.unit
def test_closed_but_already_merged_mr_is_treated_as_success():
    """A concurrent/retried run may have already merged this MR; don't fail on that."""
    project = Mock()
    mr = _make_mr()
    mr.merge.side_effect = gitlab.exceptions.GitlabMRClosedError('closed')
    fresh_mr = _make_mr(state='merged')
    project.mergerequests.get.return_value = fresh_mr

    response = merge_mr(project, mr)

    assert response == {}


@pytest.mark.unit
def test_closed_without_merging_raises_remote_repository_error():
    """Closed (not merged) means an external process interfered; fail fast, don't retry."""
    project = Mock()
    mr = _make_mr()
    mr.merge.side_effect = gitlab.exceptions.GitlabMRClosedError('closed')
    fresh_mr = _make_mr(state='closed')
    project.mergerequests.get.return_value = fresh_mr
    project.branches.get.return_value = Mock()

    with pytest.raises(RemoteRepositoryError):
        merge_mr(project, mr)


@pytest.mark.unit
def test_closed_with_missing_source_branch_raises_remote_repository_error():
    """Closed because its source branch is gone (other run deleted it) -> fast-fail."""
    project = Mock()
    mr = _make_mr()
    mr.merge.side_effect = gitlab.exceptions.GitlabMRClosedError('closed')
    fresh_mr = _make_mr(state='closed')
    project.mergerequests.get.return_value = fresh_mr
    project.branches.get.side_effect = gitlab.exceptions.GitlabGetError('not found')

    with pytest.raises(RemoteRepositoryError):
        merge_mr(project, mr)


@pytest.mark.unit
def test_waits_while_merge_status_is_checking():
    project = Mock()
    checking_mr = _make_mr(merge_status='checking')
    mergeable_mr = _make_mr(merge_status='can_be_merged')
    mergeable_mr.merge.return_value = {}
    project.mergerequests.get.return_value = mergeable_mr

    with patch('git_system_follower.git_api.gitlab_api.sleep'):
        merge_mr(project, checking_mr)

    mergeable_mr.merge.assert_called_once()


@pytest.mark.unit
def test_lacking_merge_permission_raises_remote_repository_error_without_waiting():
    """A token without merge rights should fail fast, not burn the checking-loop budget."""
    project = Mock()
    mr = _make_mr(user={'can_merge': False})

    with pytest.raises(RemoteRepositoryError):
        merge_mr(project, mr)

    mr.merge.assert_not_called()
    project.mergerequests.get.assert_not_called()


@pytest.mark.unit
def test_missing_user_field_does_not_block_merge():
    """Older GitLab responses without a `user` field shouldn't be treated as denied."""
    project = Mock()
    mr = _make_mr(user=None)
    mr.merge.return_value = {'merged': True}

    response = merge_mr(project, mr)

    assert response == {'merged': True}


@pytest.mark.unit
def test_waiting_too_long_for_mergeable_status_raises_remote_repository_error():
    project = Mock()
    checking_mr = _make_mr(merge_status='checking')
    project.mergerequests.get.return_value = checking_mr

    with patch('git_system_follower.git_api.gitlab_api.sleep'):
        with pytest.raises(RemoteRepositoryError):
            merge_mr(project, checking_mr)


@pytest.mark.unit
def test_wait_validation_pipeline_proceeds_without_pipeline():
    """No MR validation pipeline -> nothing to wait on, proceeds with merge."""
    project = Mock()
    mr = _make_mr(merge_status='can_be_merged')
    mr.pipelines.list.return_value = []

    with patch('git_system_follower.git_api.gitlab_api.sleep'):
        wait_for_validation_pipeline(project, mr)

    mr.pipelines.list.assert_called()
    project.pipelines.get.assert_not_called()


@pytest.mark.unit
def test_wait_validation_pipeline_waits_for_success():
    project = Mock()
    mr = _make_mr()
    running = _make_pipeline('running')
    success = _make_pipeline('success')
    mr.pipelines.list.return_value = [running]
    project.pipelines.get.side_effect = [running, success]

    with patch('git_system_follower.git_api.gitlab_api.sleep'):
        wait_for_validation_pipeline(project, mr)

    project.pipelines.get.assert_called()


@pytest.mark.unit
def test_wait_validation_pipeline_raises_needretry_on_failure():
    project = Mock()
    mr = _make_mr()
    failed = _make_pipeline('failed')
    mr.pipelines.list.return_value = [failed]
    project.pipelines.get.return_value = failed

    with patch('git_system_follower.git_api.gitlab_api.sleep'):
        with pytest.raises(NeedRetry):
            wait_for_validation_pipeline(project, mr)


@pytest.mark.unit
def test_wait_validation_pipeline_exits_early_on_mergeable_no_pipeline():
    """MR is already mergeable with no pipeline -> no CI gating, exit immediately."""
    project = Mock()
    mr = _make_mr(merge_status='can_be_merged')
    mr.pipelines.list.return_value = []

    with patch('git_system_follower.git_api.gitlab_api.sleep'):
        wait_for_validation_pipeline(project, mr)

    mr.pipelines.list.assert_called()
    project.mergerequests.get.assert_not_called()
    project.pipelines.get.assert_not_called()


@pytest.mark.unit
def test_wait_validation_pipeline_keeps_polling_while_checking():
    """merge_status is 'checking' -> keep polling; becomes 'can_be_merged' with no pipeline -> exit."""
    project = Mock()
    mr = _make_mr(merge_status='checking')
    merged_mr = _make_mr(merge_status='can_be_merged')
    mr.pipelines.list.return_value = []
    project.mergerequests.get.return_value = merged_mr

    with patch('git_system_follower.git_api.gitlab_api.sleep'):
        wait_for_validation_pipeline(project, mr)

    project.mergerequests.get.assert_called()
    project.pipelines.get.assert_not_called()


@pytest.mark.unit
def test_wait_validation_pipeline_waits_for_pipeline_even_if_mergeable():
    """merge_status is 'can_be_merged' but a pipeline IS found -> pipeline takes priority."""
    project = Mock()
    mr = _make_mr(merge_status='can_be_merged')
    running = _make_pipeline('running')
    success = _make_pipeline('success')
    mr.pipelines.list.return_value = [running]
    project.pipelines.get.side_effect = [running, success]

    with patch('git_system_follower.git_api.gitlab_api.sleep'):
        wait_for_validation_pipeline(project, mr)

    project.pipelines.get.assert_called()
    assert success.status == 'success'


@pytest.mark.unit
def test_wait_validation_pipeline_proceeds_after_timeout():
    """No pipeline and merge_status stays 'checking' -> proceeds after grace period."""
    project = Mock()
    mr = _make_mr(merge_status='checking')
    project.mergerequests.get.return_value = mr
    mr.pipelines.list.return_value = []

    with patch('git_system_follower.git_api.gitlab_api.sleep'):
        wait_for_validation_pipeline(project, mr)

    mr.pipelines.list.assert_called()
    project.pipelines.get.assert_not_called()
