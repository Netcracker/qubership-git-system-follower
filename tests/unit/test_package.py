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
from pathlib import Path
from unittest.mock import patch, PropertyMock

import pytest

from git_system_follower.typings.repository import RepositoryInfo
from git_system_follower.git_api.utils import get_git_repo
from git_system_follower.package.initer import init
from git_system_follower.package.updater import update
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
def bump_patch_version(version: str) -> str:
    return re.sub(
        r"^(\d+\.\d+\.)(\d+)$",
        lambda m: m.group(1) + str(int(m.group(2)) + 1),
        version
    )

def get_repo_info(project) -> RepositoryInfo:
    return RepositoryInfo(
        gitlab=project,
        git=get_git_repo(project, ENV_VARS["GITLAB_TOKEN"])
    )

def install_package(states, branch, package, is_force, project, extras):
    response = init(
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
    assert states[branch]._StateFile__get_hash(
        response['cicd_variables']
    ) == states[branch].get_package(
        package, for_delete=False
    )['cicd_variables']['hash'], "Issue with get_hash"

def update_package(states, branch, package, is_force, project, extras):
    package['version'] = bump_patch_version(package['version'])
    package_state = states[branch].get_package(package, for_delete=False)
    response = update(
        package=package,
        repo=get_repo_info(project),
        state=package_state,
        created_cicd_variables=states[branch].get_all_created_cicd_variables(),
        extras=extras,
        is_force=is_force
    )
    states[branch].add_package(
        package, response, package_state,
        structure_type=get_gear_info(package['path'])['structure_type']
    )
    package_state_updated = states[branch].get_package(package, for_delete=False)
    assert package_state['version'], "Get package failed"
    assert package_state['version'] != package_state_updated['version'], "Add package failed"

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

@pytest.mark.unit
@pytest.mark.parametrize("gear_type, name, value, masked, is_force, states", [
    ('complex', 'test1', '1', False, False, get_states_cfg()),
    ('complex', 'test2', '2', False, False, get_states_cfg()),
])
@patch("test_package.get_git_repo")
@vcr_instance.use_cassette('test_package')
def test_package(
    mock_get_git_clone,
    gear_type, name, value, masked, is_force, states):
    mock_git_clone = _get_git_clone_mock(mock_get_git_clone.return_value)
    mock_get_git_clone.return_value = mock_git_clone
    GEARS_DIR = Path(__file__).parent.parent / "gears"
    package_path = GEARS_DIR / gear_type / 'git-system-follower-package'
    package = get_package_details(path=package_path)
    package['dependencies'] = []
    extras = build_extras(name, value, masked)
    for branch in BRANCHES:
        install_package(states, branch, package, is_force, project, extras)
        update_package(states, branch, package, is_force, project, extras)
        uninstall_package(states, branch, package, is_force, project, extras)


@pytest.mark.unit
@pytest.mark.parametrize(
    "gear_type, name, value, masked, is_force, states",
    [
        ('complex', 'test1', '1', False, False, get_states_cfg()),
    ]
)
@patch("test_package.get_git_repo")
@patch("git_system_follower.package.templates.logger.warning")
@vcr_instance.use_cassette('test_package')
def test_templates_copy_files(
    mock_logger_warning, mock_get_git_clone,
    gear_type, name, value, masked, is_force, states):
    mock_git_clone = _get_git_clone_mock(mock_get_git_clone.return_value)
    mock_get_git_clone.return_value = mock_git_clone
    GEARS_DIR = Path(__file__).parent.parent / "gears"
    package_path = GEARS_DIR / gear_type / 'git-system-follower-package'
    package = get_package_details(path=package_path)
    package['dependencies'] = []
    extras = build_extras(name, value, masked)
    for branch in BRANCHES:
        install_package(states, branch, package, is_force, project, extras)

    custom_file_path = package_path / "scripts" / package['version'] \
        / "templates/default" / "{{ cookiecutter.gsf_repository_name }}" \
        / '.gitlab-ci.yml'
    with open(custom_file_path, "a", encoding="utf-8") as f:
        f.write("\n" + "# This is custom gear")

    try:
        for branch in BRANCHES:
            install_package(states, branch, package, is_force, project, extras)
    except Exception:
        pass
    mock_logger_warning.assert_called_once_with(
        "\t\tUser changes found for file .gitlab-ci.yml. Cannot copy. Skip operations"
    )
    print("Success: User changes discovered.")

    with open(custom_file_path, "r", encoding="utf-8", newline="") as f:
        text = f.read()
    lines = text.splitlines(keepends=False)
    if len(lines) >= 2:
        lines = lines[:-2]
    out = "\r\n".join(lines)
    out += "\r\n"
    with open(custom_file_path, "w", encoding="utf-8", newline="") as f:
        f.write(out)
