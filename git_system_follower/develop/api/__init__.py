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

""" Module with api to work with templates for package developers

Backwards-compatible shim: the implementation now lives in
git_system_follower.develop.api.common. New packages should import from the
versioned surface (git_system_follower.develop.api.v1 / .v2) instead.
"""

# Templates (available in all versions)
from git_system_follower.develop.api.common.templates import (
    __all__ as __templates_all__,
)

# Project metadata (only available in v2, but shim provides fallback)
try:
    from git_system_follower.develop.api.v2.project_metadata import sync_project_metadata
    __project_available = True
except ImportError:
    def sync_project_metadata(*args, **kwargs):
        """Fallback: project metadata sync not available in this version."""
        import logging
        logging.warning("Project metadata sync not available in this version")
        return None
    __project_available = False

# Combine exports
__all__ = __templates_all__ + ['sync_project_metadata']
