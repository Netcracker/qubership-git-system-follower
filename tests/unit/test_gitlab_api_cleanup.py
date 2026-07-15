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

"""Tests for failed-MR-merge cleanup helpers in git_api.gitlab_api."""

from unittest.mock import Mock, patch

import pytest

from git_system_follower.git_api.gitlab_api import (
    close_mr_and_delete_branch,
    close_stale_mrs,
)


def _make_mr(mock, *, state="opened"):
    mr = Mock()
    mr.state = state
    mr.iid = 1
    mr.source_branch = "main.temp-manage-packages"
    mr.target_branch = "main"
    mr.web_url = "http://gitlab/project/-/merge_requests/1"
    mr.save = mock
    return mr


@pytest.mark.unit
def test_close_stale_mrs_closes_open_mrs_only():
    project = Mock()
    stale = [_make_mr(Mock()), _make_mr(Mock())]
    project.mergerequests.list.return_value = stale

    close_stale_mrs(project, "main.temp-manage-packages", "main")

    project.mergerequests.list.assert_called_once_with(
        state="opened", source_branch="main.temp-manage-packages", target_branch="main", get_all=True
    )
    for mr in stale:
        assert mr.state_event == "close"
        mr.save.assert_called_once()


@pytest.mark.unit
def test_close_stale_mrs_empty_list_is_noop():
    project = Mock()
    project.mergerequests.list.return_value = []

    close_stale_mrs(project, "main.temp-manage-packages", "main")  # should not raise


@pytest.mark.unit
def test_close_mr_and_delete_branch_closes_and_deletes():
    project = Mock()
    mr = _make_mr(Mock())
    branch = "main.temp-manage-packages"

    close_mr_and_delete_branch(project, mr, branch)

    assert mr.state_event == "close"
    mr.save.assert_called_once()
    project.branches.delete.assert_called_once_with(branch)


@pytest.mark.unit
def test_close_mr_and_delete_branch_with_none_mr_still_deletes_branch():
    """create_mr may itself fail -> no MR to close, but the temp branch must still be removed."""
    project = Mock()

    close_mr_and_delete_branch(project, None, "main.temp-manage-packages")

    project.branches.delete.assert_called_once_with("main.temp-manage-packages")


@pytest.mark.unit
def test_close_mr_skips_already_merged_mr():
    project = Mock()
    mr = _make_mr(Mock(), state="merged")

    close_mr_and_delete_branch(project, mr, "main.temp-manage-packages")

    mr.save.assert_not_called()
    project.branches.delete.assert_called_once()


@pytest.mark.unit
def test_cleanup_failures_are_swallowed_with_warnings():
    """Best-effort cleanup must not mask the original error."""
    project = Mock()
    project.branches.delete.side_effect = Exception("network down")
    mr = _make_mr(Mock())

    with patch("git_system_follower.git_api.gitlab_api.logger.warning") as mock_warn:
        close_mr_and_delete_branch(project, mr, "main.temp-manage-packages")  # should not raise
    assert mock_warn.called


@pytest.mark.unit
def test_delete_branch_ignores_already_missing_branch():
    project = Mock()
    import gitlab.exceptions

    project.branches.delete.side_effect = gitlab.exceptions.GitlabDeleteError

    with patch("git_system_follower.git_api.gitlab_api.logger.warning") as mock_warn:
        close_mr_and_delete_branch(project, None, "main.temp-manage-packages")  # should not raise
    mock_warn.assert_not_called()
