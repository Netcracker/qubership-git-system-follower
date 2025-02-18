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
import click

from git_system_follower.logger import logger
from git_system_follower.errors import ParsePackageNameError, InvalidPlugin
from git_system_follower.plugins.cli.packages import NAME
from git_system_follower.plugins.cli.packages.specs import HookSpec
from git_system_follower.plugins.cli.packages.default import SourcePlugin, TarGzPlugin, ImagePlugin
from git_system_follower.utils.output import print_list


def validate_hooks(method):
    def wrapper(self, plugin):
        requires = ['match', 'process', 'get_gears']
        not_exist = []
        for require in requires:
            if require not in dir(plugin):
                not_exist.append(require)

        if not_exist:
            raise InvalidPlugin(f'Incorrect plugin structure. Missing hooks: {", ".join(not_exist)}')
        return method(self, plugin=plugin)
    return wrapper


class PluginManager:
    group = 'gsf.plugins.cli.packages'

    def __init__(self):
        self.pm = pluggy.PluginManager(NAME)
        self.pm.add_hookspecs(HookSpec)
        self.load_plugins()

    def load_plugins(self) -> list[object]:
        """ Load user's plugins from entry points

        User plugins are loaded first, and only then system plugins. To be able to override the default behavior
        """
        plugins = self._load_entry_points_plugins()

        system_plugins = [ImagePlugin, TarGzPlugin, SourcePlugin]
        for plugin in system_plugins:
            self.register(plugin())
            plugins.append(plugin)

        print_list(
            plugins,
            f'Loaded plugins for input package processing ({self.group})',
            key=lambda p: p.__name__, output_func=logger.debug
        )
        return plugins

    def _load_entry_points_plugins(self) -> list[object]:
        plugins = []

        entry_points = importlib.metadata.entry_points()
        # fix for python < 3.11
        if isinstance(entry_points, dict):
            entry_points = entry_points.get(self.group, [])

        for entry_point in entry_points:
            if entry_point.group == self.group:
                plugin = entry_point.load()
                self.register(plugin())
                plugins.append(plugin)
        return plugins

    @validate_hooks
    def register(self, plugin) -> None:
        self.pm.register(plugin)

    def get_plugin_options(self) -> dict[str, list[click.Option]]:
        options = {}
        for hook in self.pm.hook.plugin_options.get_hookimpls():
            opts = hook.plugin.plugin_options()
            options[hook.plugin.__class__.__name__] = opts
        return options

    def process(self, value: str, **kwargs) -> HookSpec:
        """ Processing input package value from CLI
        if no hook implementation has processed package then raise error

        :param value: package string for processing
        :param kwargs: plugin's parameters
        :return: processed package
        """
        for hook in self.pm.hook.match.get_hookimpls():
            process = hook.plugin.process
            is_processed = process(value=value, **kwargs)
            if is_processed:
                return hook.plugin

        # fix to get plugins in the correct order, not self.pm.get_plugins()
        plugins = [plugin[1].__class__.__name__ for plugin in self.pm.list_name_plugin()]
        raise ParsePackageNameError(
            f'Failed to determine package type of "{value}". Available system types: docker image, '
            f'local .tar.gz archive, local source directory. All plugins: {", ".join(plugins)}. '
            f'If you specified an .tar.gz archive or directory, please make sure it exist'
        )
