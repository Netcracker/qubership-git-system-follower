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

# git_system_follower/develop/api/v2/project.py

""" v2 API for project metadata operations """
from git_system_follower.package.project_metadata import sync_project_metadata as _sync
from git_system_follower.develop.api.common.types import Parameters

__all__ = ['sync_project_metadata']

def sync_project_metadata(parameters: Parameters) -> None:
    """Sync project metadata from package.yaml."""
    system_params = parameters._Parameters__system_params
    return _sync(parameters, system_params.script_dir)
