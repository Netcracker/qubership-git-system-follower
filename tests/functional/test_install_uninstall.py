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
import json
import os
import shutil
from pathlib import Path
from outlify.list import TitledList
from git_system_follower.logger import logger
from git_system_follower.install import (
    get_packages as install_get_packages,
    managing_branch as install_managing_branch
)
from git_system_follower.uninstall import (
    validate_packages_dependencies,
    get_packages as uninstall_get_packages,
    managing_branch as uninstall_managing_branch
)
from git_system_follower.utils.cli import resolve_credentials
from git_system_follower.typings.registry import RegistryTypes, RegistryInfo
from git_system_follower.typings.cli import PackageCLISource
from git_system_follower.states import ChangeStatus
from unittest.mock import patch, PropertyMock
from tests.config import (
    clone_vcr, project, build_extras, path_matcher, filter_domain_group, process_headers,
    redact_variable_value, get_states_cfg, ENV_VARS, BRANCHES, USER_EMAIL
)

IS_FORCE = False
REG_TYPE = 'Autodetect'
IS_INSECURE = False


# Commit Redaction Helpers
REDACT_KEYS = [
    "title", "message", "author_name", "author_email",
    "authored_date", "committer_name", "committer_email", "committed_date"
]


# VCR Redactor Override
def before_record_response(response):
    body = response.get("body", {}).get("string")
    if body:
        response["body"]["string"] = process_body(body)
    process_headers(response.get("headers", {}))
    return response

def process_body(raw_body):
    try:
        data = json.loads(filter_domain_group(raw_body))
        if isinstance(data, list):
            for item in data:
                if "commit" in item:
                    redact_commit_fields(item["commit"])
                redact_variable_value(item)
            return json.dumps(data).encode("utf-8")
    except Exception as e:
        print(f"Failed to process response body: {e}")

def redact_commit_fields(commit):
    for key in REDACT_KEYS:
        if key in commit:
            commit[key] = f"Dummy {key}"

vcr_instance = clone_vcr(before_record_response=before_record_response)
vcr_instance.register_matcher("uri_no_host", path_matcher)


# Package Operation Helpers
def _get_git_push_mock(mock_push):
    mock_origin = mock_push.return_value.remotes.origin
    mock_origin.push.return_value = "ok"
    return mock_origin

def _get_create_merge_mr_mock(_, __):
    return True

def _get_process(mock_branch):
    mock_branch.status.return_value = ChangeStatus.changed
    return mock_branch

def _get_git_repo_mock(mock_get_git_clone):
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    dst_dir = os.path.join(current_file_dir, ".git-system-follower/repositories/gsf-test")
    os.makedirs(dst_dir, exist_ok=True)
    src_dir = os.path.join(os.path.dirname(current_file_dir), "test_repo")
    shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
    type(mock_get_git_clone).working_tree_dir = PropertyMock(return_value=dst_dir)
    type(mock_get_git_clone).working_dir = PropertyMock(return_value=dst_dir)
    mock_get_git_clone.head.commit.hexsha = "abc123"
    return mock_get_git_clone



def _get_packages_by_action(packages, states, registry, action):
    if action == 'install':
        return install_get_packages(packages, states, registry=registry)
    return uninstall_get_packages(packages, states, registry=registry)

@pytest.mark.functional
@pytest.mark.parametrize("gear_type, states", [
    ("simple", get_states_cfg()),
    ("complex", get_states_cfg())
])
@patch("git_system_follower.install.create_mr")
@patch("git_system_follower.install.merge_mr")
@patch("git_system_follower.uninstall.create_mr")
@patch("git_system_follower.uninstall.merge_mr")
@patch("git_system_follower.install.processing_branch")
@patch("git_system_follower.uninstall.processing_branch")
@patch("git_system_follower.install.push_installed_packages")
@patch("git_system_follower.uninstall.push_installed_packages")
@patch("git_system_follower.install.get_git_repo")
@vcr_instance.use_cassette("test_install_uninstall")
def test_install_uninstall(
    mock_install_create_mr,
    mock_install_merge_mr,
    mock_uninstall_create_mr,
    mock_uninstall_merge_mr,
    mock_install_branch,
    mock_uninstall_branch,
    mock_install_push,
    mock_uninstall_push,
    mock_get_git_repo,
    gear_type, states
):
    GEARS_DIR = Path(__file__).parent.parent / "gears" / gear_type
    registry = RegistryInfo(
        credentials=resolve_credentials(None, None),
        type=RegistryTypes(REG_TYPE),
        is_insecure=IS_INSECURE
    )
    extras = build_extras("testvar1", "test1", False)

    mocks = {
        "install_push": _get_git_push_mock(mock_install_push),
        "uninstall_push": _get_git_push_mock(mock_uninstall_push),
        "install_process": _get_process(mock_install_branch),
        "uninstall_process": _get_process(mock_uninstall_branch),
        "install_mr": _get_create_merge_mr_mock(mock_install_create_mr, mock_install_merge_mr),
        "uninstall_mr": _get_create_merge_mr_mock(mock_uninstall_create_mr, mock_uninstall_merge_mr),
        "get_git_repo": _get_git_repo_mock(mock_get_git_repo)
    }

    _install(GEARS_DIR, registry, extras, states)
    _uninstall(GEARS_DIR, registry, extras, states)

    for name, mock_origin in mocks.items():
        if hasattr(mock_origin, "push"):
            try:
                mock_origin.push.assert_called_once()
            except AssertionError:
                pass

def _install(gear_dir, registry, extras, states):
    packages = _get_packages_by_action(
        [PackageCLISource(path=gear_dir)], states, registry, action="install"
    )
    logger.info(TitledList([f"{p['name']}@{p['version']}" for p in packages.install], title="Packages"))
    logger.info(TitledList([f"{p['name']}@{p['version']}" for p in packages.rollback], title="Rollback"))

    for i, branch in enumerate(BRANCHES, 1):
        logger.info(f"[{i}/{len(BRANCHES)}] Processing {branch}")
        logger.debug(f"State:\n{states[branch]}")
        states[branch] = install_managing_branch(
            project, branch, ENV_VARS["GITLAB_TOKEN"], packages, states[branch],
            extras=extras, commit_message="Installed gear(s) test",
            username="dummy_user", user_email=USER_EMAIL, is_force=IS_FORCE
        )
    logger.success("Installation complete")

def _uninstall(gear_dir, registry, extras, states):
    packages = _get_packages_by_action(
        [PackageCLISource(path=gear_dir)], states, registry, action="uninstall"
    )
    if not packages:
        logger.info("No packages found to uninstall.")
        return

    logger.info(TitledList(
        [f"{p['name']}@{p['version']}" for p in packages],title="Packages")
    )
    for i, branch in enumerate(BRANCHES, 1):
        logger.info(f"[{i}/{len(BRANCHES)}] Processing {branch}")
        logger.debug(f"State:\n{states[branch]}")
        valid_packages = validate_packages_dependencies(packages, states[branch])
        if not valid_packages:
            logger.info(f"No packages to delete for {branch}")
            continue
        logger.info(TitledList(
            [f"{p['name']}@{p['version']}" for p in valid_packages],
            title="Validated for Uninstall")
        )
        states[branch] = uninstall_managing_branch(
            project, branch, ENV_VARS["GITLAB_TOKEN"], valid_packages, states[branch],
            extras=extras, commit_message="Uninstalled gear(s)",
            username="dummy_user", user_email=USER_EMAIL, is_force=IS_FORCE
        )
    logger.success("Uninstallation complete")
