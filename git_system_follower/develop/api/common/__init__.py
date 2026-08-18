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

""" Shared implementation of the package developer api.

This subpackage holds the actual api implementation that is common to all
package description file api versions (v1, v2, ...). Versioned subpackages
(git_system_follower.develop.api.v1, .v2) re-export the appropriate surface
from here so that repetition is avoided.
"""
