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

from pathlib import Path

import click

from git_system_follower.logger import logger, set_level
from git_system_follower.errors import CLIParamsError
from git_system_follower.plugins.cli.packages.specs import HookSpec
from git_system_follower.typings.cli import ExtraParam
from git_system_follower.utils.cli import Package, ExtraParamTuple, add_options, get_gears
from git_system_follower.utils.output import banner, print_params
from git_system_follower.git_api.utils import get_config
from git_system_follower.download import download
from git_system_follower.install import install
from git_system_follower.uninstall import uninstall
from git_system_follower import __version__

from git_system_follower.plugins.managers import managers


config = get_config('~/.gitconfig')
GIT_USERNAME = config.get_value('user', 'name', default='unknown')
GIT_EMAIL = config.get_value('user', 'email', default='unknown@example.com')


@click.command(name='download')
@click.argument('gears', nargs=-1, type=Package)
@click.option(
    '-d', '--directory', type=click.Path(exists=True, dir_okay=True, file_okay=False, path_type=Path),
    default=Path('.'), help='Directory where gears will be downloaded'
)
@click.option('--debug', 'is_debug', is_flag=True, default=False, help='Show debug level messages')
def download_command(
        gears: tuple[HookSpec, ...], directory: Path,
        is_debug: bool,
        *args, **kwargs  # dont delete, these parameters for plugin manager
):
    """ Download gears

    \b
    GEARS                         Download all listed gears as image:
                                  <registry>/<repository>/<name>:<tag>, e.g.
                                  artifactory.company.com/path-to/your-image:1.0.0
    """
    banner(version=__version__, output_func=logger.info)
    print_params({
        'gears': ', '.join([str(gear) for gear in gears]),
        'directory': directory.absolute(),
        'debug': is_debug
    }, 'Start parameters', hidden_params=('token',), output_func=logger.info)
    if gears == ():
        raise CLIParamsError('Gears for downloading are not specified')
    set_level(is_debug)
    gears = get_gears(gears)
    download(gears, directory, is_deps_first=True)


@click.command(name='install')
@click.argument('gears', nargs=-1, type=Package)
@click.option(
    '-r', '--repo', 'repo', type=str, required=True,
    help='Gitlab repository url', metavar='URL'
)
@click.option(
    '-b', '--branch', 'branches', type=str, required=True, multiple=True,
    help='Branches in which to install the gears', metavar='BRANCH...'
)
@click.option(
    '-t', '--token', type=str, envvar='GSF_GIT_TOKEN', required=True,
    help='Gitlab access token'
)
@click.option(
    '--extra', 'extras', type=ExtraParamTuple([
        click.STRING, click.STRING, click.Choice(['masked', 'no-masked'], case_sensitive=False)
    ]),
    multiple=True, help='Extra parameters to be passed to the package API: variable name, value, masked/no-masked',
    metavar='<NAME VALUE CHOICE>...'
)
@click.option(
    '--message', type=str, default='Installed gear(s)',
    help='Commit message'
)
@click.option(
    '--git-username', 'username', type=str, envvar='GSF_GIT_USERNAME', default=GIT_USERNAME,
    help='Username under which the commit will be made to the repository', metavar='USER'
)
@click.option(
    '--git-email', 'email', type=str, envvar='GSF_GIT_EMAIL', default=GIT_EMAIL,
    help='User email under which the commit will be made to the repository', metavar='EMAIL'
)
@click.option(
    '-f', '--force', 'is_force', is_flag=True, default=False,
    help='Forced installation: change of files, CI/CD variables as specified in gear'
)
@click.option('--debug', 'is_debug', is_flag=True, default=False, help='Show debug level messages')
def install_command(
        gears: tuple[HookSpec, ...], repo: str,
        branches: tuple[str, ...], token: str, extras: tuple[ExtraParam],
        message: str, username: str, email: str,
        is_force: bool, is_debug: bool,
        *args, **kwargs  # dont delete, these parameters for plugin manager
):
    """ Install gears to branches in repository

    \b
    GEARS                         Install all listed gears as
                                  1. image: <registry>/<repository>/<name>:<tag>, e.g.
                                  artifactory.company.com/path-to/your-image:1.0.0
                                  2. .tar.gz archive: /path/to/archive.tar.gz, e.g.
                                  your-archive@1.0.0.tar.gz
                                  3. source code files: /path/to/gear directory, e.g.
                                  your-gear@1.0.0
    """
    banner(version=__version__, output_func=logger.info)
    print_params({
        'gears': ', '.join([str(gear) for gear in gears]),
        'repo': repo,
        'branches': ', '.join(branches),
        'token': token,
        'extras': ', '.join([f"{var.name}={'*****' if var.masked else var.value}" for var in extras]),
        'message': message,
        'git-username': username,
        'git-email': email,
        'force': is_force,
        'debug': is_debug
    }, 'Start parameters', hidden_params=('token',), output_func=logger.info)
    if gears == ():
        raise CLIParamsError('Gears for installation are not specified')
    set_level(is_debug)
    gears = get_gears(gears)
    install(
        gears, repo, branches, token, extras=extras,
        commit_message=message, username=username, user_email=email,
        is_force=is_force
    )


@click.command(name='uninstall')
@click.argument('gears', nargs=-1, type=Package)
@click.option(
    '-r', '--repo', 'repo', type=str, required=True,
    help='Gitlab repository url', metavar='URL'
)
@click.option(
    '-b', '--branch', 'branches', type=str, required=True, multiple=True,
    help='Branches in which to uninstall the gears', metavar='BRANCH...'
)
@click.option(
    '-t', '--token', type=str, envvar='GSF_GIT_TOKEN', required=True,
    help='Gitlab access token'
)
@click.option(
    '--extra', 'extras', type=ExtraParamTuple([
        click.STRING, click.STRING, click.Choice(['masked', 'no-masked'], case_sensitive=False)
    ]),
    multiple=True, help='Extra parameters to be passed to the package API: variable name, value, masked/no-masked',
    metavar='<NAME VALUE CHOICE>...'
)
@click.option(
    '--message', type=str, default='Uninstalled gear(s)',
    help='Commit message'
)
@click.option(
    '--git-username', 'username', type=str, envvar='GSF_GIT_USERNAME', default=GIT_USERNAME,
    help='Username under which the commit will be made to the repository', metavar='USER'
)
@click.option(
    '--git-email', 'email', type=str, envvar='GSF_GIT_EMAIL', default=GIT_EMAIL,
    help='User email under which the commit will be made to the repository', metavar='EMAIL'
)
@click.option(
    '-f', '--force', 'is_force', is_flag=True, default=False,
    help='Forced uninstallation: change of files, CI/CD variables as specified in gear'
)
@click.option('--debug', 'is_debug', is_flag=True, default=False, help='Show debug level messages')
def uninstall_command(
        gears: tuple[HookSpec, ...], repo: str,
        branches: tuple[str, ...], token: str, extras: tuple[ExtraParam, ...],
        message: str, username: str, email: str,
        is_force: bool, is_debug: bool,
        *args, **kwargs  # dont delete, these parameters for plugin manager
):
    """ Uninstall gears from branches in repository

    It is necessary to have gears, since the manager interacts with the delete package api

    \b
    GEARS                         Uninstall all listed gears as
                                  1. image: <registry>/<repository>/<name>:<tag>, e.g.
                                  artifactory.company.com/path-to/your-image:1.0.0
                                  2. .tar.gz archive: /path/to/archive.tar.gz, e.g.
                                  your-archive@1.0.0.tar.gz
                                  3. source code files: /path/to/gear directory, e.g.
                                  your-gear@1.0.0
    """
    banner(version=__version__, output_func=logger.info)
    print_params({
        'gears': ', '.join([str(gear) for gear in gears]),
        'repo': repo,
        'branches': ', '.join(branches),
        'token': token,
        'extras': ', '.join([f"{var.name}={'*****' if var.masked else var.value}" for var in extras]),
        'message': message,
        'git-username': username,
        'git-email': email,
        'force': is_force,
        'debug': is_debug
    }, 'Start parameters', hidden_params=('token',), output_func=logger.info)
    if gears == ():
        raise CLIParamsError('Gears for uninstallation are not specified')
    set_level(is_debug)
    gears = get_gears(gears)
    uninstall(
        gears, repo, branches, token, extras=extras,
        commit_message=message, username=username, user_email=email,
        is_force=is_force
    )


@click.command(name='list')
def list_command():
    """ List installed gears: in develop """


@click.command(name='version')
def version_command():
    """ Show version """
    print(__version__)


@click.group()
def cli():
    """ The package manager for Git providers. """


# Dynamic addition so that plugins can add their own parameters
download_command = add_options(download_command, managers)
install_command = add_options(install_command, managers)
uninstall_command = add_options(uninstall_command, managers)

cli.add_command(download_command, name='download')
cli.add_command(install_command, name='install')
cli.add_command(uninstall_command, name='uninstall')
cli.add_command(list_command, name='list')
cli.add_command(version_command, name='version')


if __name__ == '__main__':
    cli(prog_name='gsf', show_default=True)
