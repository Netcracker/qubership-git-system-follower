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

""" Module with plugin managers

It is necessary to load all managers at the start of the program to catch any plugin-related errors immediately.
Therefore, they are declared right away rather than when they are needed
"""

from git_system_follower.plugins.cli.packages.manager import PluginManager as CliPackagesPluginManager


__all__ = ['managers', 'cli_packages_pm']


cli_packages_pm = CliPackagesPluginManager()

managers = [cli_packages_pm]
