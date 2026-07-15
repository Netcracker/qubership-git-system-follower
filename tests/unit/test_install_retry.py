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

"""Tests for the retry behavior around managing_branch and install()'s CI/CD revert."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from git_system_follower.install import install, managing_branch
from git_system_follower.states import ChangeStatus
from git_system_follower.typings.repository import RepositoryInfo
from git_system_follower.utils.retry import NeedRetry, MaxRetries


def _make_repo():
    repo = Mock(spec=RepositoryInfo)
    repo.git.active_branch.name = 'main.temp-manage-packages'
    repo.gitlab = Mock()
    return repo


def _make_packages():
    return SimpleNamespace(install=[{'name': 'migrate', 'version': '0.0.1', 'dependencies': ()}], rollback=())


@pytest.mark.unit
@patch('git_system_follower.install.close_mr_and_delete_branch')
@patch('git_system_follower.install.merge_mr')
@patch('git_system_follower.install.wait_for_validation_pipeline')
@patch('git_system_follower.install.create_mr')
@patch('git_system_follower.install.close_stale_mrs')
def test_managing_branch_retries_on_needretry_then_succeeds(
    mock_close_stale, mock_create, mock_wait, mock_merge, mock_cleanup
):
    """A transient NeedRetry (e.g. conflicts) should not fail the whole install - just this attempt."""
    repo = _make_repo()
    project = Mock()
    state = Mock()
    state.status.return_value = ChangeStatus.changed
    mock_create.return_value = Mock()
    mock_merge.side_effect = [NeedRetry('conflicts'), NeedRetry('conflicts'), {}]

    with (
        patch('git_system_follower.install.checkout_to_new_branch'),
        patch('git_system_follower.install.processing_branch', return_value=state),
    ):
        result = managing_branch(
            project, 'main', repo, 'token', _make_packages(), Mock(), (),
            extras=(), commit_message='msg', username='u', user_email='e',
            is_skip_force_rollback=False, is_autoheal=False, is_force=False,
        )

    assert result is state
    assert mock_merge.call_count == 3
    assert mock_create.call_count == 3
    # Each failed attempt tears down its own MR/branch before the next attempt starts
    assert mock_cleanup.call_count == 2


@pytest.mark.unit
@patch('git_system_follower.install.close_mr_and_delete_branch')
@patch('git_system_follower.install.merge_mr')
@patch('git_system_follower.install.wait_for_validation_pipeline')
@patch('git_system_follower.install.create_mr')
@patch('git_system_follower.install.close_stale_mrs')
def test_managing_branch_raises_maxretries_after_exhausting_attempts(
    mock_close_stale, mock_create, mock_wait, mock_merge, mock_cleanup
):
    repo = _make_repo()
    project = Mock()
    state = Mock()
    state.status.return_value = ChangeStatus.changed
    mock_create.return_value = Mock()
    mock_merge.side_effect = NeedRetry('conflicts')

    with (
        patch('git_system_follower.install.checkout_to_new_branch'),
        patch('git_system_follower.install.processing_branch', return_value=state),
    ):
        with pytest.raises(MaxRetries):
            managing_branch(
                project, 'main', repo, 'token', _make_packages(), Mock(), (),
                extras=(), commit_message='msg', username='u', user_email='e',
                is_skip_force_rollback=False, is_autoheal=False, is_force=False,
            )

    assert mock_merge.call_count == 5  # default max_retries in @retry
    assert mock_cleanup.call_count == 5


@pytest.mark.unit
@patch('git_system_follower.install.revert_cicd_changes')
@patch('git_system_follower.install.capture_existing_cicd')
@patch('git_system_follower.install.managing_branch')
@patch('git_system_follower.install.get_packages')
@patch('git_system_follower.install.get_states')
@patch('git_system_follower.install.RepositoryInfo')
@patch('git_system_follower.install.get_git_repo')
@patch('git_system_follower.install.get_project')
@patch('git_system_follower.install.get_gitlab')
def test_install_reverts_cicd_once_after_retries_exhausted(
    mock_get_gitlab, mock_get_project, mock_get_git_repo, mock_repo_info_cls,
    mock_get_states, mock_get_packages, mock_managing_branch, mock_capture, mock_revert
):
    """Capture happens once per branch, revert happens once (not once per retry attempt)."""
    repo = Mock()
    repo.gitlab = Mock()
    mock_repo_info_cls.return_value.initialize.return_value = repo
    state = Mock()
    mock_get_states.return_value = {'main': state}
    mock_get_packages.return_value = SimpleNamespace(install=[], rollback=())
    mock_capture.return_value = {'TEST_VAR': {'value': 'test', 'masked': False}}
    mock_managing_branch.side_effect = MaxRetries('Max retries reached. Operation failed')

    with pytest.raises(SystemExit):
        install(
            (), (), 'http://gitlab/group/project', ('main',), 'token',
            extras=(), commit_message='msg', username='u', user_email='e',
            registry=Mock(), is_skip_force_rollback=False, is_skip_project_description=False,
            is_skip_project_icon=False, is_autoheal=False, is_force=False,
        )

    mock_capture.assert_called_once_with(repo.gitlab)
    mock_managing_branch.assert_called_once()
    mock_revert.assert_called_once_with(repo.gitlab, mock_capture.return_value, state)


@pytest.mark.unit
@patch('git_system_follower.install.revert_cicd_changes')
@patch('git_system_follower.install.capture_existing_cicd')
@patch('git_system_follower.install.managing_branch')
@patch('git_system_follower.install.get_packages')
@patch('git_system_follower.install.get_states')
@patch('git_system_follower.install.RepositoryInfo')
@patch('git_system_follower.install.get_git_repo')
@patch('git_system_follower.install.get_project')
@patch('git_system_follower.install.get_gitlab')
def test_install_does_not_revert_cicd_on_success(
    mock_get_gitlab, mock_get_project, mock_get_git_repo, mock_repo_info_cls,
    mock_get_states, mock_get_packages, mock_managing_branch, mock_capture, mock_revert
):
    repo = Mock()
    repo.gitlab = Mock()
    mock_repo_info_cls.return_value.initialize.return_value = repo
    state = Mock()
    mock_get_states.return_value = {'main': state}
    mock_get_packages.return_value = SimpleNamespace(install=[], rollback=())
    mock_managing_branch.return_value = state

    install(
        (), (), 'http://gitlab/group/project', ('main',), 'token',
        extras=(), commit_message='msg', username='u', user_email='e',
        registry=Mock(), is_skip_force_rollback=False, is_skip_project_description=False,
        is_skip_project_icon=False, is_autoheal=False, is_force=False,
    )

    mock_revert.assert_not_called()
