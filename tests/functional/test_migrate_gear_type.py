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
import json
import yaml
import shutil
from pathlib import Path
from unittest.mock import patch, PropertyMock

import pytest
from git_system_follower.install import install_package as ins_install_package
from git_system_follower.typings.repository import RepositoryInfo
from git_system_follower.git_api.utils import get_git_repo
from git_system_follower.package.initer import init
from git_system_follower.package.deleter import delete
from git_system_follower.package.package_info import get_gear_info
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
def get_repo_info(project) -> RepositoryInfo:
    return RepositoryInfo(
        gitlab=project,
        git=get_git_repo(project, ENV_VARS["GITLAB_TOKEN"])
    )

def install_package_non_empty_state(states, branch, package, is_force, project, extras):
    ins_install_package(
        package=package,
        additional_packages=[],
        repo=get_repo_info(project),
        state=states[branch].get_package(package, for_delete=False),
        created_cicd_variables=states[branch].get_all_created_cicd_variables(),
        extras=extras,
        is_force=is_force
    )

def install_package(states, branch, package, is_force, project, extras):
    response = init(
        package=package,
        repo=get_repo_info(project),
        state=states[branch].get_package(package, for_delete=False),
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
    assert states[branch].get_package(package, for_delete=True) is None, "Delete package failed"

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

def install_gear_and_assert(states, gear_type, migrate_version, package_path, is_force, caplog, extras):
    update_package_yaml(package_path, 'migrate', migrate_version)
    package = get_package_details(path=package_path)
    package['dependencies'] = []
    if not is_force:
        try:
            for branch in BRANCHES:
                install_package_non_empty_state(states, branch, package, is_force, project, extras)
        except (SystemExit, Exception):
            assert "State and gear structure type mismatch detected." in caplog.text
    else:
        for branch in BRANCHES:
            install_package_non_empty_state(states, branch, package, is_force, project, extras)
        message_parts = [
                "Since --force was passed",
                "Please review the affected files",
                "before moving forward"]
        assert all(part in caplog.text for part in message_parts)

def install_gear(states, gear_type, migrate_version, reset_version, is_force, project, extras):
    package_path = get_package_path(gear_type)
    update_package_yaml(package_path, 'migrate', migrate_version)
    package = get_package_details(path=package_path)
    package['dependencies'] = []
    for branch in BRANCHES:
        install_package(states, branch, package, is_force, project, extras)
    update_package_yaml(package_path, gear_type, reset_version)

def _get_git_clone_mock(mock_get_git_clone):
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    dst_dir = os.path.join(current_file_dir, ".git-system-follower/repositories/gsf-test")
    os.makedirs(dst_dir, exist_ok=True)
    src_dir = os.path.join(os.path.dirname(current_file_dir), "test_repo")
    # print(src_dir)
    # print(dst_dir)
    shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
    type(mock_get_git_clone).working_tree_dir = PropertyMock(return_value=dst_dir)
    type(mock_get_git_clone).working_dir = PropertyMock(return_value=dst_dir)
    mock_get_git_clone.head.commit.hexsha = "abc123"
    return mock_get_git_clone

# Test Entry Point
vcr_instance = clone_vcr(before_record_response=before_record_response)
vcr_instance.register_matcher("uri_no_host", path_matcher)

@pytest.mark.functional
@patch("test_migrate_gear_type.get_git_repo")
@vcr_instance.use_cassette('test_migrate_gear_type')
def test_migrate_simple_complex(mock_get_git_clone, caplog):
    mock_git_clone = _get_git_clone_mock(mock_get_git_clone.return_value)
    mock_get_git_clone.return_value = mock_git_clone
    extras = build_extras('test1', '1', False)
    for is_force in [False, True]:
        states = get_states_cfg()
        install_gear(states, 'simple', '0.0.1', '1.0.0', is_force, project, extras)
        package_path = get_package_path('complex')
        install_gear_and_assert(states, 'complex', '0.0.2', package_path, is_force, caplog, extras)
        update_package_yaml(package_path, 'complex', '0.0.1')


@pytest.mark.functional
@patch("test_migrate_gear_type.get_git_repo")
@vcr_instance.use_cassette('test_migrate_gear_type')
def test_migrate_complex_simple(mock_get_git_clone, caplog):
    mock_git_clone = _get_git_clone_mock(mock_get_git_clone.return_value)
    mock_get_git_clone.return_value = mock_git_clone
    extras = build_extras('test1', '1', False)
    for is_force in [False, True]:
        states = get_states_cfg()
        install_gear(states, 'complex', '0.0.1', '0.0.1', is_force, project, extras)
        package_path = get_package_path('simple')
        install_gear_and_assert(states, 'simple', '0.0.2', package_path, is_force, caplog, extras)
        update_package_yaml(package_path, 'simple', '1.0.0')
