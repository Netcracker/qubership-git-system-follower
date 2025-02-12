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
from git_system_follower.typings.cli import PackageCLIImage, PackageCLITarGz, PackageCLISource, ExtraParam
from git_system_follower.utils.cli import Package, ExtraParamTuple
from git_system_follower.utils.output import banner, print_params
from git_system_follower.download import download
from git_system_follower.install import install
from git_system_follower.uninstall import uninstall
from git_system_follower import __version__


@click.group()
def cli():
    """ The package manager for Git providers. """


@cli.command(name='download')
@click.argument('gears', nargs=-1, type=Package)
@click.option(
    '-d', '--directory', type=click.Path(exists=True, dir_okay=True, file_okay=False, path_type=Path),
    default=Path('.'),
    help='Directory where gears will be downloaded'
)
@click.option('--debug', 'is_debug', is_flag=True, default=False, help='Show debug level messages')
def download_command(
        gears: tuple[PackageCLIImage | PackageCLITarGz | PackageCLISource, ...], directory: Path,
        is_debug: bool
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
    download(gears, directory, is_deps_first=True)


@cli.command(name='install')
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
    '--ticket', type=str, default='FAKE-0000',
    help='Ticket ID that will be automatically added to the beginning of each commit message'
)
@click.option(
    '--message', type=str, default='Installed gear(s)',
    help='Commit message text after the ticket ID'
)
@click.option(
    '-f', '--force', 'is_force', is_flag=True, default=False,
    help='Forced installation: change of files, CI/CD variables as specified in gear'
)
@click.option('--debug', 'is_debug', is_flag=True, default=False, help='Show debug level messages')
def install_command(
        gears: tuple[PackageCLIImage | PackageCLITarGz | PackageCLISource, ...], repo: str,
        branches: tuple[str, ...], token: str, extras: tuple[ExtraParam], ticket: str, message: str,
        is_force: bool, is_debug: bool
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
        'ticket': ticket,
        'message': message,
        'force': is_force,
        'debug': is_debug
    }, 'Start parameters', hidden_params=('token',), output_func=logger.info)
    if gears == ():
        raise CLIParamsError('Gears for installation are not specified')
    set_level(is_debug)
    install(gears, repo, branches, token, extras=extras, ticket=ticket, message=message, is_force=is_force)


@cli.command(name='uninstall')
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
    '--ticket', type=str, default='FAKE-0000',
    help='Ticket ID that will be automatically added to the beginning of each commit message'
)
@click.option(
    '--message', type=str, default='Uninstalled gear(s)',
    help='Commit message text after the ticket ID'
)
@click.option(
    '-f', '--force', 'is_force', is_flag=True, default=False,
    help='Forced uninstallation: change of files, CI/CD variables as specified in gear'
)
@click.option('--debug', 'is_debug', is_flag=True, default=False, help='Show debug level messages')
def uninstall_command(
        gears: tuple[PackageCLIImage | PackageCLITarGz | PackageCLISource, ...], repo: str,
        branches: tuple[str, ...], token: str, extras: tuple[ExtraParam, ...], ticket: str, message: str,
        is_force: bool, is_debug: bool
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
        'ticket': ticket,
        'message': message,
        'force': is_force,
        'debug': is_debug
    }, 'Start parameters', hidden_params=('token',), output_func=logger.info)
    if gears == ():
        raise CLIParamsError('Gears for uninstallation are not specified')
    set_level(is_debug)
    uninstall(gears, repo, branches, token, extras=extras, ticket=ticket, message=message, is_force=is_force)


@cli.command(name='list')
def list_command():
    """ List installed gears: in develop """


@cli.command(name='version')
def version_command():
    """ Show version """
    print(__version__)


if __name__ == '__main__':
    cli(prog_name='gsf', show_default=True)
