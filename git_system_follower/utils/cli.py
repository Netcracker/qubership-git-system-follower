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

from sys import stdin

import click

from git_system_follower.typings.cli import PackageCLISource, PackageCLITarGz, PackageCLIImage, ExtraParam, Credentials
from git_system_follower.plugins.managers import cli_packages_pm as plugin_manager
from git_system_follower.plugins.cli.packages.specs import HookSpec


__all__ = [
    'Package', 'PackageType', 'ExtraParamTuple',
    'resolve_credentials',
    'add_options', 'get_gears'
]


class PackageType(click.ParamType):
    """ Class for checking parameters from click cli """
    name = 'package'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def convert(self, value: str, param, ctx) -> PackageCLIImage | PackageCLITarGz | PackageCLISource:
        return plugin_manager.process(value, **ctx.params)


Package = PackageType()


class ExtraParamTuple(click.Tuple):
    name = 'extra_param'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def convert(self, value, param, ctx):
        values = super().convert(value, param, ctx)
        return ExtraParam(name=values[0], value=values[1], masked=True if values[2] == 'masked' else False)


def resolve_credentials(cli_username: str | None, cli_password: str | None) -> Credentials | None:
    stdin_username, stdin_password = read_stdin_credentials()
    username, password = cli_username or stdin_username, cli_password or stdin_password
    if username is None and password is None:
        return None

    if username is None:
        username = click.prompt('Registry username', type=str)
    if password is None:
        password = click.prompt('Registry password', type=str, hide_input=True)
    return Credentials(username, password)


def read_stdin_credentials() -> tuple[str | None, str | None]:
    """ Reads username and password from standard input.

    :returns: Credentials or None if stdin is empty
    """
    if stdin.isatty():
        return None, None

    input_lines = stdin.read().strip().splitlines()
    if len(input_lines) < 2:
        return None, None
    return input_lines[0], input_lines[1]


""" --------------- For plugins --------------- """


def get_gears(hooks: tuple[HookSpec, ...]) -> tuple[PackageCLISource | PackageCLITarGz | PackageCLIImage, ...]:
    """ Add gears from plugin """
    gears = []
    for hook in hooks:
        gears.extend(hook.gears)
    return tuple(gears)


def add_options(command: object, managers: list):
    """ Dynamically add options to click command """
    for manager in managers:
        options = manager.get_plugin_options()
        for plugin_name, opts in options.items():
            for opt in opts:
                params = extract_click_option_params(opt)

                help_msg = params.get('help', '')
                params['help'] = f'{manager.group}:{plugin_name}:{help_msg}'
                command = opt(command)

    return command


def extract_click_option_params(option: click.option) -> dict:
    """ Extract click.option params """
    closure = option.__closure__
    if not closure:
        return {}

    for cell in closure:
        if isinstance(cell.cell_contents, dict):
            return cell.cell_contents

    return {}
