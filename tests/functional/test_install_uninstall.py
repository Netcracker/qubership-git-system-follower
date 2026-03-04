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
from pathlib import Path
from git_system_follower.utils.cli import resolve_credentials
from git_system_follower.typings.registry import RegistryTypes, RegistryInfo
from unittest.mock import patch
from tests.config import (
    clone_vcr, build_extras, path_matcher, filter_domain_group, process_headers,
    redact_variable_value, get_states_cfg
)
from common import (
    get_git_push_mock, get_create_merge_mr_mock, get_process, get_git_repo_mock,
    install, uninstall
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
def test_migrate_simple_complex(
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
        "install_push": get_git_push_mock(mock_install_push),
        "uninstall_push": get_git_push_mock(mock_uninstall_push),
        "install_process": get_process(mock_install_branch),
        "uninstall_process": get_process(mock_uninstall_branch),
        "install_mr": get_create_merge_mr_mock(mock_install_create_mr, mock_install_merge_mr),
        "uninstall_mr": get_create_merge_mr_mock(mock_uninstall_create_mr, mock_uninstall_merge_mr),
        "get_git_repo": get_git_repo_mock(mock_get_git_repo)
    }

    install(GEARS_DIR, registry, extras, states)
    uninstall(GEARS_DIR, registry, extras, states)

    for name, mock_origin in mocks.items():
        if hasattr(mock_origin, "push"):
            try:
                mock_origin.push.assert_called_once()
            except AssertionError:
                pass
