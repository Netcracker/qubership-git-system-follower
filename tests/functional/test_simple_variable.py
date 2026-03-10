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

import re
import os
import json
import shutil
import yaml
from pathlib import Path
from typing import Tuple
from unittest.mock import patch, PropertyMock

import pytest

from git_system_follower.typings.repository import RepositoryInfo
from git_system_follower.git_api.utils import get_git_repo
from git_system_follower.package.initer import init
from git_system_follower.package.deleter import delete
from git_system_follower.states import PackageState
from git_system_follower.develop.api.types import ExtraParams
from git_system_follower.package.package_info import get_gear_info
from git_system_follower.errors import PackageCICDVariablePolicyError
from tests.config import (
    clone_vcr, project, build_extras, get_package_details,
    path_matcher, filter_domain_group, process_headers,
    redact_variable_value, get_states_cfg, ENV_VARS, BRANCHES
)


# Commit Redaction Helpers
REDACT_KEYS = [
    "title", "message", "author_name", "author_email",
    "authored_date", "committer_name", "committer_email", "committed_date"
]

gear_type = "simple"
is_force = False
states = get_states_cfg()

def redact_commit_fields(commit: dict):
    for key in REDACT_KEYS:
        if key in commit:
            commit[key] = f"Dummy {key}"


# VCR Redactor Override
def before_record_response(response):
    body = response.get("body", {}).get("string")
    if body:
        response["body"]["string"] = process_body(body)
    process_headers(response.get("headers", {}))
    return response

def process_body(raw_body):
    try:
        filtered_body = filter_domain_group(raw_body)
        data = json.loads(filtered_body)

        if isinstance(data, list):
            for item in data:
                if isinstance(item.get("commit"), dict):
                    redact_commit_fields(item["commit"])
                redact_variable_value(item)
        elif isinstance(data, dict):
            redact_variable_value(data)
        return json.dumps(data).encode("utf-8")
    except Exception as e:
        print(f"Failed to process response body: {e}")
        return raw_body


# Package Operation Helpers
def bump_patch_version(version: str, bump_by: str) -> str:
    return re.sub(
        r"^(\d+\.\d+\.)(\d+)$",
        lambda m: m.group(1) + str(int(m.group(2)) + int(bump_by)),
        version
    )

def get_repo_info(project) -> RepositoryInfo:
    return RepositoryInfo(
        gitlab=project,
        git=get_git_repo(project, ENV_VARS["GITLAB_TOKEN"])
    )

def install_package(states, branch, package, is_force, project, extras,
    state_cond=None):
    state = states[branch].get_packages()[0] if state_cond else None
    response = init(
        state=state,
        package=package,
        repo=get_repo_info(project),
        created_cicd_variables=states[branch].get_all_created_cicd_variables(),
        extras=extras,
        is_force=is_force
    )
    states[branch].add_package(
        package, response, None,
        structure_type=get_gear_info(package['path'])['structure_type']
    )

def uninstall_package(states, branch, package, is_force, project, extras):
    delete(
        package=package,
        repo=get_repo_info(project),
        state=states[branch].get_package(package, for_delete=True),
        created_cicd_variables=states[branch].get_all_created_cicd_variables(),
        extras=extras,
        is_force=is_force
    )
    states[branch].delete_package(states[branch].get_package(package, for_delete=True))

def _get_git_clone_mock(mock_get_git_clone):
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    dst_dir = os.path.join(current_file_dir, ".git-system-follower/repositories/gsf-test")
    os.makedirs(dst_dir, exist_ok=True)
    src_dir = os.path.join(os.path.dirname(current_file_dir), "test_repo")
    shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
    type(mock_get_git_clone).working_tree_dir = PropertyMock(return_value=dst_dir)
    type(mock_get_git_clone).working_dir = PropertyMock(return_value=dst_dir)
    mock_get_git_clone.head.commit.hexsha = "abc123"
    return mock_get_git_clone

# Test Entry Point
vcr_instance = clone_vcr(before_record_response=before_record_response)
vcr_instance.register_matcher("uri_no_host", path_matcher)

def create_gear2(package_path: Path):
    path = Path(package_path / "package.yaml")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if "name" in data:
        data["name"] = data["name"] + "2"
    yaml_str = yaml.safe_dump(data, sort_keys=False, default_flow_style=False).rstrip()
    path.write_text(yaml_str, encoding="utf-8")

def delete_gear2(package_path: Path):
    path = Path(package_path / "package.yaml")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if "name" in data:
        data["name"] = data["name"][:-1]
    yaml_str = yaml.safe_dump(data, sort_keys=False, default_flow_style=False).rstrip()
    yaml_str_crlf = yaml_str.replace('\n', '\r\n')
    path.write_text(yaml_str_crlf, encoding="utf-8")

def scaffold(mock_get_git_clone) -> Tuple[ExtraParams, PackageState, Path]:
    mock_git_clone = _get_git_clone_mock(mock_get_git_clone.return_value)
    mock_get_git_clone.return_value = mock_git_clone
    GEARS_DIR = Path(__file__).parent.parent / "gears"
    package_path = GEARS_DIR / gear_type / 'git-system-follower-package'
    package = get_package_details(path=package_path)
    package['dependencies'] = []
    extras = build_extras('test1', '1', False) + build_extras(
        'test2', '2', False)
    return extras, package, package_path

@pytest.mark.functional
@patch("test_simple_variable.get_git_repo")
@vcr_instance.use_cassette('test_simple_variable_A')
def test_simple_A(mock_get_git_clone):
    """
    Install gear1 with variables: var1, var2 - OK
    Uninstall this gear1 - OK
    """
    extras, package, package_path = scaffold(mock_get_git_clone)
    for branch in BRANCHES:
        install_package(states, branch, package, is_force, project, extras)
        uninstall_package(states, branch, package, is_force, project, extras)

@pytest.mark.functional
@patch("test_simple_variable.get_git_repo")
@vcr_instance.use_cassette('test_simple_variable_B')
def test_simple_B(mock_get_git_clone):
    """
    install gear1 with var1, var2 - OK
    install gear2 with var3, var4 - OK
    uninstall gear1 or gear2
    """
    extras, package, package_path = scaffold(mock_get_git_clone)
    extras2 = build_extras('test3', '3', False) + build_extras(
        'test4', '4', False)
    for branch in BRANCHES:
        install_package(states, branch, package, is_force, project, extras)

        create_gear2(package_path=package_path)
        package = get_package_details(path=package_path)
        package['dependencies'] = []

        install_package(states, branch, package, is_force, project, extras2)
        uninstall_package(states, branch, package, is_force, project, extras2)

        delete_gear2(package_path=package_path)
        package = get_package_details(path=package_path)
        package['dependencies'] = []

        uninstall_package(states, branch, package, is_force, project, extras)

@pytest.mark.functional
@patch("test_simple_variable.get_git_repo")
@vcr_instance.use_cassette('test_simple_variable_C')
def test_simple_C(mock_get_git_clone):
    """
    Install gear1 with var1, var2 - OK
    Install gear2 with var3, var2 - Exception
    """
    extras, package, package_path = scaffold(mock_get_git_clone)
    extras2 = build_extras('test2', '2', False) + build_extras(
        'test3', '3', False)
    for branch in BRANCHES:
        install_package(states, branch, package, is_force, project, extras)

        create_gear2(package_path=package_path)
        package = get_package_details(path=package_path)
        package['dependencies'] = []
        with pytest.raises(PackageCICDVariablePolicyError):
            print("Exception tested for PackageCICDVariablePolicyError")
            install_package(states, branch, package, is_force, project, extras2)

        delete_gear2(package_path=package_path)
        package = get_package_details(path=package_path)
        package['dependencies'] = []
        uninstall_package(states, branch, package, is_force, project, extras)

@pytest.mark.functional
@patch("test_simple_variable.get_git_repo")
@vcr_instance.use_cassette('test_simple_variable_D')
def test_simple_D(mock_get_git_clone):
    """
    Install gear1 with var1, var2 - OK
    Update gear1 with update var1 - OK
    """
    extras, package, package_path = scaffold(mock_get_git_clone)
    extras = build_extras('test1', '1', False) + build_extras(
        'test2', '2', False)
    extras2 = build_extras('test1', '1', False) + build_extras(
        'test2', '3', False)
    for branch in BRANCHES:
        install_package(states, branch, package, is_force, project, extras)
        install_package(states, branch, package, is_force, project, extras2, True)
        uninstall_package(states, branch, package, is_force, project, extras2)

