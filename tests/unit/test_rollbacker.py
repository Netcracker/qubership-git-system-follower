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

import pytest
from unittest.mock import Mock, patch

from git_system_follower.package.rollbacker import rollback


@pytest.mark.unit
def test_rollback_deletes_release_tag_for_component():
    package = {"name": "comp", "version": "1.0.0"}
    old_package = {"name": "comp", "version": "2.0.0", "subtype": "component"}
    repo = Mock()

    with patch("git_system_follower.package.rollbacker.delete") as mock_delete, \
            patch("git_system_follower.package.rollbacker.init", return_value={"status": "ok"}) as mock_init, \
            patch("git_system_follower.package.rollbacker.delete_tag") as mock_delete_tag:
        rollback(
            package, old_package, repo, Mock(),
            created_cicd_variables=(), extras=(), is_autoheal=False,
            is_skip_force_rollback=True, is_force=False
        )

    mock_delete.assert_called_once()
    mock_init.assert_called_once()
    mock_delete_tag.assert_called_once_with(repo.gitlab, "2.0.0")


@pytest.mark.unit
def test_rollback_does_not_delete_tag_for_non_component():
    package = {"name": "simple", "version": "0.1.0"}
    old_package = {"name": "simple", "version": "1.0.0"}

    with patch("git_system_follower.package.rollbacker.delete"), \
            patch("git_system_follower.package.rollbacker.init", return_value={"status": "ok"}), \
            patch("git_system_follower.package.rollbacker.delete_tag") as mock_delete_tag:
        rollback(
            package, old_package, Mock(), Mock(),
            created_cicd_variables=(), extras=(), is_autoheal=False,
            is_skip_force_rollback=True, is_force=False
        )

    mock_delete_tag.assert_not_called()


@pytest.mark.unit
def test_rollback_force_reinstall_still_deletes_component_release_tag():
    package = {"name": "comp", "version": "1.0.0"}
    old_package = {"name": "comp", "version": "2.0.0", "subtype": "component"}
    repo = Mock()

    with patch("git_system_follower.package.rollbacker.init", return_value={"status": "ok"}) as mock_init, \
            patch("git_system_follower.package.rollbacker.delete_tag") as mock_delete_tag:
        rollback(
            package, old_package, repo, Mock(),
            created_cicd_variables=(), extras=(), is_autoheal=False,
            is_skip_force_rollback=False, is_force=False
        )

    mock_init.assert_called_once()
    mock_delete_tag.assert_called_once_with(repo.gitlab, "2.0.0")
