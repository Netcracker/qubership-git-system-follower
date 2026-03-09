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

import os
import yaml
import shutil
from pathlib import Path
from outlify.list import TitledList
from unittest.mock import PropertyMock
from git_system_follower.install import (
    get_packages as install_get_packages,
    managing_branch as install_managing_branch
)
from git_system_follower.uninstall import (
    validate_packages_dependencies,
    get_packages as uninstall_get_packages,
    managing_branch as uninstall_managing_branch
)
from tests.config import project, BRANCHES, ENV_VARS, USER_EMAIL
from git_system_follower.states import ChangeStatus
from git_system_follower.typings.cli import PackageCLISource
from git_system_follower.logger import logger

IS_FORCE = False

# Package Operation Helpers
def get_git_push_mock(mock_push):
    mock_origin = mock_push.return_value.remotes.origin
    mock_origin.push.return_value = "ok"
    return mock_origin

def get_create_merge_mr_mock(_, __):
    return True

def get_process(mock_branch):
    mock_branch.status.return_value = ChangeStatus.changed
    return mock_branch

def get_git_repo_mock(mock_get_git_clone):
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    dst_dir = os.path.join(current_file_dir, ".git-system-follower/repositories/gsf-test")
    os.makedirs(dst_dir, exist_ok=True)
    src_dir = os.path.join(os.path.dirname(current_file_dir), "test_repo")
    shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
    type(mock_get_git_clone).working_tree_dir = PropertyMock(return_value=dst_dir)
    type(mock_get_git_clone).working_dir = PropertyMock(return_value=dst_dir)
    mock_get_git_clone.head.commit.hexsha = "abc123"
    return mock_get_git_clone

def get_packages_by_action(packages, states, registry, action):
    if action == 'install':
        return install_get_packages(packages, states, 'test_repo', BRANCHES, registry=registry)
    return uninstall_get_packages(packages, states, registry=registry)

def update_package_yaml(package_path, name, version):
    """Update package.yaml name and version"""
    with open(package_path / 'package.yaml', 'r') as file:
        data = yaml.safe_load(file)
    data['name'] = name
    data['version'] = version
    with open(package_path / 'package.yaml', 'w') as file:
        yaml.dump(data, file, default_flow_style=False)

def get_package_path(gear_type):
    """Get package path for gear type"""
    return Path(__file__).parent.parent / "gears" / gear_type / 'git-system-follower-package'

def install(gear_dir, registry, extras, states):
    packages = get_packages_by_action(
        [PackageCLISource(path=gear_dir)], states, registry, action="install"
    )
    logger.info(TitledList([f"{p['name']}@{p['version']}" for p in packages.install], title="Packages"))
    logger.info(TitledList([f"{p['name']}@{p['version']}" for p in packages.rollback], title="Rollback"))

    for i, branch in enumerate(BRANCHES, 1):
        logger.info(f"[{i}/{len(BRANCHES)}] Processing {branch}")
        logger.debug(f"State:\n{states[branch]}")
        states[branch] = install_managing_branch(
            project, branch, ENV_VARS["GITLAB_TOKEN"], packages, states[branch], 'test-repo',
            extras=extras, commit_message="Installed gear(s) test",
            username="dummy_user", user_email=USER_EMAIL, is_force=IS_FORCE
        )
    logger.success("Installation complete")

def uninstall(gear_dir, registry, extras, states):
    packages = get_packages_by_action(
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
        valid_packages = validate_packages_dependencies(packages, states[branch]),
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
