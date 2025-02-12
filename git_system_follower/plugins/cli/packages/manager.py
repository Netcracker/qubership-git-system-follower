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

import importlib.metadata

import pluggy

from git_system_follower.logger import logger
from git_system_follower.errors import ParsePackageNameError
from git_system_follower.typings.cli import PackageCLISource, PackageCLITarGz, PackageCLIImage
from git_system_follower.plugins.cli.packages import NAME, Result
from git_system_follower.plugins.cli.packages.default import SourcePlugin, TarGzPlugin, ImagePlugin
from git_system_follower.utils.output import print_list


hookspec = pluggy.HookspecMarker(NAME)


class HookSpec:
    @hookspec
    def process_gear(self, value: str) -> Result:
        pass


class PluginManager:
    group = 'gsf.plugins.cli'

    def __init__(self):
        self.pm = pluggy.PluginManager(NAME)
        self.pm.add_hookspecs(HookSpec)
        self.load_plugins()

    def load_plugins(self) -> list[object]:
        """ Load user's plugins from entry points """
        plugins = [SourcePlugin, TarGzPlugin, ImagePlugin]
        for plugin in plugins:
            self.register(plugin())

        for entry_point in importlib.metadata.entry_points():
            if entry_point.group == self.group:
                plugin = entry_point.load()
                self.pm.register(plugin())
                plugins.append(plugin)

        print_list(
            plugins,
            f'Loaded plugins for input package processing ({self.group})',
            key=lambda p: p.__name__, output_func=logger.debug
        )
        return plugins

    def register(self, plugin) -> None:
        self.pm.register(plugin)

    def process(self, value: str) -> PackageCLISource | PackageCLITarGz | PackageCLIImage:
        for hook in self.pm.hook.process_gear.get_hookimpls():
            func = hook.plugin.process_gear
            package, is_processed = func(value=value)
            if is_processed:
                return package

        # fix to get plugins in the correct order, not self.pm.get_plugins()
        plugins = [plugin[1].__class__.__name__ for plugin in self.pm.list_name_plugin()]
        raise ParsePackageNameError(
            f'Failed to determine package type of "{value}". Available system types: docker image, '
            f'local .tar.gz archive, local source directory. All plugins: {", ".join(plugins)}. '
            f'If you specified an .tar.gz archive or directory, please make sure it exist'
        )
