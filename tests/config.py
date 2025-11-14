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
import re
import json
import yaml
import vcr
import shutil
import logging
from pathlib import Path
from urllib.parse import urlparse
from gitlab import Gitlab

from git_system_follower.typings.cli import ExtraParam
from git_system_follower.git_api.gitlab_api import get_states
from git_system_follower.typings.package import PackageLocalData

# Constants & Environment
BRANCHES = ['test']
USER_EMAIL = 'GITLAB_USER_EMAIL_ID'

# Required environment variables
ENV_VARS = {
    "GITLAB_URL": "https://git.dummy.com",
    "GITLAB_TOKEN": "glpat-dummytoken",
    "GITLAB_GROUP": "dummy",
    "GITLAB_PROJECT_ID": "42352"
}


if not all(ENV_VARS.values()):
    raise EnvironmentError("Missing one or more required environment variables.")

CASSETTE_DIR = Path(__file__).parent / "cassettes"
HOSTNAME = urlparse(ENV_VARS["GITLAB_URL"]).netloc

# Utility Functions
def build_extras(name, value, masked) -> list:
    return [ExtraParam(name=name, value=value, masked=masked)]

def get_package_details(path) -> PackageLocalData:
    with open(path / 'package.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return PackageLocalData(**data, path=path.parent)


# VCR Global Utility Functions
def filter_domain_group(element):
    def _replace(text):
        text = re.sub(HOSTNAME, "gitlab.dummy.org", text, flags=re.IGNORECASE)
        return re.sub(ENV_VARS["GITLAB_GROUP"], "dummy_path", text, flags=re.IGNORECASE)

    if isinstance(element, bytes):
        try:
            return _replace(element.decode("utf-8")).encode("utf-8")
        except UnicodeDecodeError:
            return element
    elif isinstance(element, str):
        return _replace(element)
    return element

def redact_variable_value(item: dict):
    if "key" in item and "test" not in item["key"].lower():
        item["key"] = "Dummy key"
        item["value"] = "Dummy value"

def redact_states(data: list[dict]) -> list[dict]:
    data = [d for d in data if d.get("name") in BRANCHES]
    redact_map = {
        "author_name": "DUMMY_name",
        "author_email": "DUMMY_email",
        "committer_name": "DUMMY_name",
        "committer_email": "DUMMY_email",
    }
    for d in data:
        commit = d.get("commit", {})
        for key, dummy in redact_map.items():
            if key in commit:
                commit[key] = dummy
    return data

def process_body(raw_body):
    try:
        filtered_body = filter_domain_group(raw_body)
        data = json.loads(filtered_body)
        states_check = False
        if isinstance(data, list):
            for item in data:
                redact_variable_value(item)
            states_check = all("name" in d and "commit" in d for d in data)
        if states_check:
            return json.dumps(redact_states(data)).encode("utf-8")
        elif isinstance(data, dict):
            redact_variable_value(data)
        return json.dumps(data).encode("utf-8")
    except Exception as e:
        print(f"Failed to process response body: {e}")
        return raw_body  # fallback

def process_headers(headers):
    if "Link" in headers:
        headers["Link"] = [filter_domain_group(link) for link in headers["Link"]]


# VCR Hooks & Matchers
def before_record_request(request):
    parsed = urlparse(request.uri)
    request.uri = request.uri.replace(f"{parsed.scheme}://{parsed.netloc}", "")
    return request

def before_record_response(response):
    body = response.get("body", {}).get("string")
    if body:
        response["body"]["string"] = process_body(body)
    process_headers(response.get("headers", {}))
    return response

def path_matcher(r1, r2):
    return (
        urlparse(r1.uri).path == urlparse(r2.uri).path and
        r1.method == r2.method and
        r1.body == r2.body
    )


# VCR Configuration
def setup_vcr_logger():
    log_path = Path(__file__).parent / "vcr_debug.log"
    open(log_path, "w").close()

    logger = logging.getLogger("vcr")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    logger.handlers.clear()

    handler = logging.FileHandler(log_path)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)


# Test Repo setup
def setup_test_repo_dir():
    directory_path = Path(__file__).parent / "test_repo"
    if os.path.exists(directory_path):
        shutil.rmtree(directory_path)
    os.makedirs(directory_path, exist_ok=True)


setup_vcr_logger()
setup_test_repo_dir()

VCR_CONFIG = {
    "record_mode": "once",
    "cassette_library_dir": str(CASSETTE_DIR),
    "path_transformer": vcr.VCR.ensure_suffix(".yaml"),
    "before_record_request": before_record_request,
    "before_record_response": before_record_response,
    "match_on": ["uri_no_host"],
    "filter_headers": ["authorization", "PRIVATE-TOKEN"]
}

vcr_instance = vcr.VCR(**VCR_CONFIG)
vcr_instance.register_matcher("uri_no_host", path_matcher)

def clone_vcr(**overrides):
    return vcr.VCR(**{**VCR_CONFIG, **overrides})

# GitLab Initialization
with vcr_instance.use_cassette('gitlab_project'):
    gl = Gitlab(url=ENV_VARS["GITLAB_URL"], private_token=ENV_VARS["GITLAB_TOKEN"])
    project = gl.projects.get(ENV_VARS["GITLAB_PROJECT_ID"])

@vcr_instance.use_cassette('states')
def get_states_cfg():
    return get_states(project, BRANCHES)
