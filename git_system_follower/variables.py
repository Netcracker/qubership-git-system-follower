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

from pathlib import Path
import os


ROOT_DIR = Path('.git-system-follower').absolute()
REPOS_PATH = ROOT_DIR / 'repositories'
PACKAGES_PATH = ROOT_DIR / 'packages'
if not PACKAGES_PATH.exists():
    os.makedirs(PACKAGES_PATH)

PACKAGE_API_RESULT = ROOT_DIR / 'package-api-result.json'
IMAGE_PACKAGE_MAP = ROOT_DIR / 'image-package-map.json'

PACKAGE_DIRNAME = 'git-system-follower-package'
SCRIPTS_DIR = 'scripts'
PACKAGE_DESCRIPTION_FILE_API = {
    'v1': {
        'mandatory_sections': ('apiVersion', 'type', 'name', 'version'),
        'optional_sections': ('dependencies',),
        'section_types': (str, str, str, str, {list: str}),
        'package_types': ('gitlab-ci-pipeline',)
    }
}
