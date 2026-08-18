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

""" Package developer api for package description file api version v2.

The v2 surface is a thin re-export over the shared implementation in
git_system_follower.develop.api.common. Package scripts of a v2 gear should
import from here, e.g.::

    from git_system_follower.develop.api.v2.types import Parameters
    from git_system_follower.develop.api.v2.cicd_variables import create_variable
    from git_system_follower.develop.api.v2.templates import create_template
    from git_system_follower.develop.api.v2.webhooks import create_webhook
"""
