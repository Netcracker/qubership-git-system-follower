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

"""Tests for failed-MR-merge cleanup in the managing_branch flow (install)."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from git_system_follower.install import managing_branch
from git_system_follower.states import ChangeStatus
from git_system_follower.typings.repository import RepositoryInfo


def _make_repo():
    repo = Mock(spec=RepositoryInfo)
    repo.git.active_branch.name = "main.temp-manage-packages"
    repo.gitlab = Mock()
    return repo


def _make_packages():
    return SimpleNamespace(install=[{"name": "migrate", "version": "0.0.1", "dependencies": ()}])


@pytest.mark.unit
@patch("git_system_follower.install.close_mr_and_delete_branch")
@patch("git_system_follower.install.merge_mr")
@patch("git_system_follower.install.wait_for_validation_pipeline")
@patch("git_system_follower.install.create_mr")
@patch("git_system_follower.install.close_stale_mrs")
def test_merge_failure_cleans_up_mr_and_branch(mock_close_stale, mock_create, mock_wait, mock_merge, mock_cleanup):
    """When merge fails, the open MR and temp branch must be removed."""
    repo = _make_repo()
    project = Mock()
    state = Mock()
    state.status.return_value = ChangeStatus.changed
    mr = Mock()
    mr.iid = 42
    mr.source_branch = "main.temp-manage-packages"
    mr.target_branch = "main"
    mock_create.return_value = mr
    mock_merge.side_effect = RuntimeError("merge conflict")

    with (
        patch("git_system_follower.install.checkout_to_new_branch"),
        patch("git_system_follower.install.processing_branch", return_value=state),
    ):
        with pytest.raises(RuntimeError):
            managing_branch(
                project,
                "main",
                repo,
                "token",
                _make_packages(),
                Mock(),
                (),
                extras=(),
                commit_message="msg",
                username="u",
                user_email="e",
                is_skip_force_rollback=False,
                is_autoheal=False,
                is_force=False,
            )

    mock_cleanup.assert_called_once_with(repo.gitlab, mr, "main.temp-manage-packages")


@pytest.mark.unit
@patch("git_system_follower.install.close_mr_and_delete_branch")
@patch("git_system_follower.install.merge_mr")
@patch("git_system_follower.install.wait_for_validation_pipeline")
@patch("git_system_follower.install.create_mr")
@patch("git_system_follower.install.close_stale_mrs")
def test_create_mr_failure_still_cleans_up_branch(mock_close_stale, mock_create, mock_wait, mock_merge, mock_cleanup):
    """If create_mr fails there is no MR, but the pushed temp branch must still be removed."""
    repo = _make_repo()
    project = Mock()
    state = Mock()
    state.status.return_value = ChangeStatus.changed
    mock_create.side_effect = RuntimeError("cannot create mr")

    with (
        patch("git_system_follower.install.checkout_to_new_branch"),
        patch("git_system_follower.install.processing_branch", return_value=state),
    ):
        with pytest.raises(RuntimeError):
            managing_branch(
                project,
                "main",
                repo,
                "token",
                _make_packages(),
                Mock(),
                (),
                extras=(),
                commit_message="msg",
                username="u",
                user_email="e",
                is_skip_force_rollback=False,
                is_autoheal=False,
                is_force=False,
            )

    mock_cleanup.assert_called_once_with(repo.gitlab, None, "main.temp-manage-packages")
    mock_merge.assert_not_called()


@pytest.mark.unit
@patch("git_system_follower.install.close_stale_mrs")
@patch("git_system_follower.install.close_mr_and_delete_branch")
@patch("git_system_follower.install.merge_mr")
@patch("git_system_follower.install.wait_for_validation_pipeline")
@patch("git_system_follower.install.create_mr")
def test_stale_mrs_are_closed_before_create(mock_create, mock_wait, mock_merge, mock_cleanup, mock_close_stale):
    """Pre-existing open MRs from a failed/retried run are closed before creating a new one."""
    repo = _make_repo()
    project = Mock()
    state = Mock()
    state.status.return_value = ChangeStatus.changed
    mr = Mock()
    mock_create.return_value = mr
    mock_merge.return_value = {}

    with (
        patch("git_system_follower.install.checkout_to_new_branch"),
        patch("git_system_follower.install.processing_branch", return_value=state),
    ):
        managing_branch(
            project,
            "main",
            repo,
            "token",
            _make_packages(),
            Mock(),
            (),
            extras=(),
            commit_message="msg",
            username="u",
            user_email="e",
            is_skip_force_rollback=False,
            is_autoheal=False,
            is_force=False,
        )

    mock_close_stale.assert_called_once_with(repo.gitlab, "main.temp-manage-packages", "main")
    mock_cleanup.assert_not_called()
    mock_create.assert_called_once()
    mock_merge.assert_called_once()
