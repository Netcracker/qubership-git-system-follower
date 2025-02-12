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

import click

from git_system_follower.typings.cli import PackageCLISource, PackageCLITarGz, PackageCLIImage, ExtraParam
from git_system_follower.plugins.plugin_managers import cli_packages_pm as plugin_manager


__all__ = ['Package', 'PackageType', 'ExtraParamTuple']


class PackageType(click.ParamType):
    """ Class for checking parameters from click cli """
    name = 'package'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def convert(self, value: str, param, ctx) -> PackageCLIImage | PackageCLITarGz | PackageCLISource:
        return plugin_manager.process(value)


Package = PackageType()


class ExtraParamTuple(click.Tuple):
    name = 'extra_param'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def convert(self, value, param, ctx):
        values = super().convert(value, param, ctx)
        return ExtraParam(name=values[0], value=values[1], masked=True if values[2] == 'masked' else False)
