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

import pluggy
import click

from git_system_follower.plugins.cli.packages import NAME
from git_system_follower.typings.cli import PackageCLISource, PackageCLITarGz, PackageCLIImage


__all__ = ['HookSpec']


hookspec = pluggy.HookspecMarker(NAME)


class HookSpec:
    value: str | None
    gears: list[PackageCLISource | PackageCLITarGz | PackageCLIImage] | None

    def __init__(self):
        self.value = None

    def process(self, value, **kwargs) -> bool:
        match = self.match(value)
        if match:
            self.value = value
            self.gears = self.get_gears(value, **kwargs)
        return match

    def __str__(self) -> str:
        gears = [str(gear) for gear in self.gears]
        msg = ', '.join(gears) if gears else 'No Gears inside'
        return f'{self.value} ({msg})'

    @hookspec
    def plugin_options(self) -> list[click.option]:
        """ Get plugin options for CLI options """
        return []

    @hookspec
    def match(self, value: str) -> bool:
        """ Is this value a package of this type

        :param value: GSF cli argument
        :return: true/false
        """
        return False

    @hookspec
    def get_gears(self, value: str, **kwargs) -> list[PackageCLISource | PackageCLITarGz | PackageCLIImage]:
        """ Get Gears from this CLI argument type """
        return []
