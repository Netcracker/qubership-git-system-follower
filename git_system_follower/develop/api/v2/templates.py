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

""" v2 api to work with templates for package developers """
import json
from git_system_follower.develop.api.common.templates import (
    __all__ as __all__,
)
from git_system_follower.variables import PACKAGE_API_RESULT as __PACKAGE_API_RESULT
from git_system_follower.develop.api.v2.project_metadata import sync_project_metadata
from git_system_follower.develop.api.v2.types import ProjectMetadata
from git_system_follower.logger import logger

def create_template(parameters, name, variables=None, *, is_force=False, skip_files=()):
    """Create files using cookiecutter template (v2).
    v2 adds automatic project metadata sync from package.yaml.
    """
    from git_system_follower.develop.api.common.templates import create_template as _create_template_base
    _create_template_base(parameters, name, variables, is_force=is_force, skip_files=skip_files)
    try:
        sync_project_metadata(parameters)
        _add_metadata()
        logger.info("\tProject metadata synchronized successfully")
    except Exception as e:
        logger.warning(f"Failed to sync project metadata: {e}")


def update_template(parameters, variables=None, *, is_force=False, skip_files=()):
    """Update files using cookiecutter template (v2).
    v2 adds automatic project metadata sync from package.yaml.
    """
    from git_system_follower.develop.api.common.templates import update_template as _update_template_base
    _update_template_base(parameters, variables, is_force=is_force, skip_files=skip_files)
    try:
        sync_project_metadata(parameters)
        _add_metadata()
        logger.info("\tProject metadata synchronized successfully")
    except Exception as e:
        logger.warning(f"\tFailed to sync project metadata: {e}")

def delete_template(parameters, *, is_force=False, skip_files=()):
    """Delete files using cookiecutter template (v2).
    v2 adds automatic project metadata sync from package.yaml.
    """
    from git_system_follower.develop.api.common.templates import delete_template as _delete_template_base
    _delete_template_base(parameters, is_force=is_force, skip_files=skip_files)
    _delete_metadata()

def _add_metadata() -> None:
    ctx = ProjectMetadata()
    with open(__PACKAGE_API_RESULT, 'r') as file:
        content = json.load(file)
    content['project_metadata'] = (
        { **ctx._data.__dict__,
         'cicd_catalog': ctx._cicd_catalog,
         'icon_hash': ctx._icon_hash
        }
        if ctx._data else None
    )
    with open(__PACKAGE_API_RESULT, 'w') as file:
        json.dump(content, file)

def _delete_metadata() -> None:
    with open(__PACKAGE_API_RESULT, 'r') as file:
        content = json.load(file)
    content['project_metadata'] = None
    with open(__PACKAGE_API_RESULT, 'w') as file:
        json.dump(content, file)
