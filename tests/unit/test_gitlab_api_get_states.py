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

"""Tests for get_states branch-existence check in git_api.gitlab_api.

The branch-existence check was changed from listing all branches
(``project.branches.list(get_all=True)``) to direct per-branch ref resolution
(``project.branches.get(branch)``) with a bounded wait/retry, because the list
endpoint can lag behind a freshly pushed ref and can drop branches from a
stitched snapshot under concurrent create/delete.
"""

from unittest.mock import Mock, patch

import gitlab.exceptions
import pytest

from git_system_follower.errors import RemoteRepositoryError
from git_system_follower.git_api.gitlab_api import (
    BRANCH_MAX_WAIT,
    BRANCH_POLL_WAIT,
    get_states,
)

BRANCH = 'feature-123-autotest'


def _make_project(*, branches_get_return_value=Mock(), raw_side_effect=None):
    project = Mock()
    project.branches.get.return_value = branches_get_return_value
    # By default there is no .state.yaml on the branch -> empty StateFile path.
    project.files.raw.side_effect = (
        raw_side_effect if raw_side_effect is not None
        else gitlab.exceptions.GitlabGetError('404')
    )
    return project


@patch('git_system_follower.git_api.gitlab_api.get_cicd_variables_safely', return_value={})
@patch('git_system_follower.git_api.gitlab_api.get_webhooks_safely', return_value={})
@patch('git_system_follower.git_api.gitlab_api.sleep')
def test_get_states_branch_found_immediately(mock_sleep, mock_webhooks, mock_cicd):
    """Existing branch is found on first direct get; no list call, no waiting."""
    project = _make_project()

    result = get_states(project, (BRANCH,))

    assert BRANCH in result
    project.branches.get.assert_called_once_with(BRANCH)
    project.branches.list.assert_not_called()
    mock_sleep.assert_not_called()


@patch('git_system_follower.git_api.gitlab_api.get_cicd_variables_safely', return_value={})
@patch('git_system_follower.git_api.gitlab_api.get_webhooks_safely', return_value={})
@patch('git_system_follower.git_api.gitlab_api.sleep')
def test_get_states_waits_for_branch_to_appear(mock_sleep, mock_webhooks, mock_cicd):
    """Freshly pushed branch: first direct get fails, second succeeds after one wait."""
    project = _make_project()
    project.branches.get.side_effect = [
        gitlab.exceptions.GitlabGetError('404 Branch not found'),
        Mock(),
    ]

    result = get_states(project, (BRANCH,))

    assert BRANCH in result
    assert project.branches.get.call_count == 2
    project.branches.list.assert_not_called()
    mock_sleep.assert_called_once()


@patch('git_system_follower.git_api.gitlab_api.get_cicd_variables_safely', return_value={})
@patch('git_system_follower.git_api.gitlab_api.get_webhooks_safely', return_value={})
@patch('git_system_follower.git_api.gitlab_api.sleep')
def test_get_states_raises_when_branch_never_appears(mock_sleep, mock_webhooks, mock_cicd):
    """Branch that never appears raises RemoteRepositoryError after the wait budget."""
    project = _make_project()
    project.branches.get.side_effect = gitlab.exceptions.GitlabGetError(
        '404 Branch not found'
    )

    with pytest.raises(RemoteRepositoryError, match=f'Branch {BRANCH} not found'):
        get_states(project, (BRANCH,))

    project.branches.list.assert_not_called()
    # Budget exhausted: one poll per BRANCH_POLL_WAIT seconds up to BRANCH_MAX_WAIT.
    assert mock_sleep.call_count == BRANCH_MAX_WAIT // BRANCH_POLL_WAIT


@patch('git_system_follower.git_api.gitlab_api.get_cicd_variables_safely', return_value={})
@patch('git_system_follower.git_api.gitlab_api.get_webhooks_safely', return_value={})
@patch('git_system_follower.git_api.gitlab_api.sleep')
def test_get_states_empty_state_when_no_state_file(mock_sleep, mock_webhooks, mock_cicd):
    """Branch exists but has no .state.yaml -> empty StateFile is created."""
    project = _make_project()
    project.files.raw.side_effect = gitlab.exceptions.GitlabGetError('404')

    result = get_states(project, (BRANCH,))

    assert BRANCH in result
    assert result[BRANCH].get_packages() == []


@patch('git_system_follower.git_api.gitlab_api.get_cicd_variables_safely', return_value={})
@patch('git_system_follower.git_api.gitlab_api.get_webhooks_safely', return_value={})
@patch('git_system_follower.git_api.gitlab_api.sleep')
def test_get_states_multiple_branches(mock_sleep, mock_webhooks, mock_cicd):
    """Each branch is resolved independently via direct get."""
    project = _make_project()
    project.branches.get.side_effect = [Mock(), Mock()]

    result = get_states(project, ('main', BRANCH))

    assert set(result) == {'main', BRANCH}
    project.branches.get.assert_any_call('main')
    project.branches.get.assert_any_call(BRANCH)
    project.branches.list.assert_not_called()
