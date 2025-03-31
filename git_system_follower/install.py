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

""" Module with api for `install` command """
from pathlib import Path
from pprint import pformat

from gitlab.v4.objects import Project

from git_system_follower.logger import logger
from git_system_follower.errors import InstallationError, PackageNotFoundError, PackageNamePolicyError
from git_system_follower.typings.cli import (
    PackageCLI, PackageCLIImage, PackageCLITarGz, PackageCLISource, ExtraParam
)
from git_system_follower.typings.registry import RegistryInfo
from git_system_follower.typings.package import PackageLocalData, PackagesTo
from git_system_follower.download import download
from git_system_follower.git_api.gitlab_api import (
    get_gitlab, get_project, get_states, create_mr, merge_mr
)
from git_system_follower.git_api.git_api import checkout_to_new_branch, push_installed_packages
from git_system_follower.git_api.utils import get_packages_str, get_git_repo
from git_system_follower.typings.repository import RepositoryInfo
from git_system_follower.states import (
    ChangeStatus, PackageState, StateFile,
    get_installed_packages, update_created_cicd_variables,
)
from git_system_follower.utils.output import print_list
from git_system_follower.utils.retry import retry
from git_system_follower.utils.versions import normalize_version
from git_system_follower.package.initer import init
from git_system_follower.package.updater import update
# from git_system_follower.package.rollbacker import rollback
from git_system_follower.typings.script import ScriptResponse


__all__ = ['install']


def install(
        packages: tuple[PackageCLIImage | PackageCLITarGz | PackageCLISource, ...],
        repo_url: str, branches: tuple[str, ...], token: str, *,
        extras: tuple[ExtraParam, ...], commit_message: str,
        username: str, user_email: str,
        registry: RegistryInfo, is_force: bool,
) -> None:
    gitlab_instance = get_gitlab(repo_url, token)
    project = get_project(gitlab_instance, repo_url)
    states = get_states(project, branches)

    packages = get_packages(packages, states, registry=registry)
    print_list(packages.install, title='Packages', output_func=logger.info,
               key=lambda package: f"{package['name']}@{package['version']}")
    print_list(packages.rollback, title='Additional rollback packages', output_func=logger.info,
               key=lambda package: f"{package['name']}@{package['version']}")
    logger.info('Processing branches')
    for i, branch in enumerate(branches, 1):
        logger.info(f'[{i}/{len(branches)}] Processing {branch} branch')
        logger.debug(f'Current state in {branch} branch:\n{states[branch]}')
        states[branch] = managing_branch(
            project, branch, token, packages, states[branch], extras=extras,
            commit_message=commit_message, username=username, user_email=user_email, is_force=is_force
        )
    logger.success('Installation complete')


def get_packages(
        packages_cli: tuple[PackageCLIImage | PackageCLITarGz | PackageCLISource, ...],
        states: dict[str, StateFile], *,
        registry: RegistryInfo
) -> PackagesTo:
    """ Getting information about packages to install and rollback (delete+init)

    :param packages_cli: listing packages to be installed
    :param states: current states in GitLab repository branches
    :param registry: registry information like credentials for auth, insecure mode, etc.

    :return: packages info tuples in PackageTo class
    """
    packages = PackagesTo(
        install=_get_packages_to_install(packages_cli, registry=registry),
        rollback=()
    )
    installed_packages = get_installed_packages(states)
    packages.rollback = _get_packages_to_rollback(packages_cli, installed_packages, registry=registry)
    return packages


def _get_packages_to_install(
        packages_cli: tuple[PackageCLIImage | PackageCLITarGz | PackageCLISource, ...], *,
        registry: RegistryInfo
) -> tuple[PackageLocalData, ...]:
    """ Getting information about packages to install

    :param packages_cli: listing packages to be installed
    :param registry: registry information like credentials for auth, insecure mode, etc.
    :return: packages info to install tuple
    """
    packages = tuple(download(packages_cli, is_deps_first=True, registry=registry))
    for i, package in enumerate(packages):
        for j, comparison_package in enumerate(packages):
            if i != j and package['name'] == comparison_package['name']:
                package_str = f"{package['name']}@{package['version']}"
                comparison_package_str = f"{comparison_package['name']}@{comparison_package['version']}"
                raise PackageNamePolicyError(f'Package names match ({package_str} and {comparison_package_str}). '
                                             f'One package of different versions cannot be installed in one repository')
    return packages


def _get_packages_to_rollback(
        packages_cli: tuple[PackageCLIImage | PackageCLITarGz | PackageCLISource, ...],
        installed_packages: set[PackageCLI], *,
        registry: RegistryInfo
) -> tuple[PackageLocalData, ...]:
    """ Getting information about packages to rollback (delete+init)

    :param packages_cli: listing packages to be installed
    :param installed_packages: listing installed packages
    :param registry: registry information like credentials for auth, insecure mode, etc.
    :return: packages info to rollback tuple
    """
    packages_to_rollback = []
    for package_cli in packages_cli:
        for installed_package in installed_packages:
            if _is_necessary_package_to_rollback(package_cli, installed_package):
                packages_to_rollback.append(installed_package)
    return tuple(download(packages_to_rollback, is_deps_first=False, registry=registry))


def _is_necessary_package_to_rollback(package_cli: PackageCLI, installed_package: PackageCLI) -> bool:
    """ Is it necessary to get information for a package to rollback or will existing packages suffice

    :param package_cli: package to install
    :param installed_package: installed package
    """
    return package_cli.name == installed_package.name and package_cli.version < installed_package.version


@retry(output_func=logger.info, error_output_func=logger.error)
def managing_branch(
        project: Project, branch: str, token: str, packages: PackagesTo, state: StateFile, *,
        extras: tuple[ExtraParam, ...], commit_message: str, username: str, user_email: str,
        is_force: bool
) -> StateFile:
    repo = RepositoryInfo(gitlab=project, git=get_git_repo(project, token))
    checkout_to_new_branch(repo.git, branch)

    logger.info(':: Installing packages')
    state = processing_branch(
        packages, repo, state, extras=extras, is_force=is_force,
        commit_message=commit_message, username=username, user_email=user_email
    )
    if state.status() == ChangeStatus.no_change:
        logger.info(f'No changes in {repo.git.active_branch.name} branch. Skip create/merge merge request')
        return state
    logger.info(':: Creating merge request')
    mr = create_mr(
        repo.gitlab, repo.git.active_branch.name, branch, title=commit_message,
        description=f'Installed package(s): {get_packages_str(packages.install)}'
    )
    logger.info(':: Merging merge request')
    merge_mr(repo.gitlab, mr)
    return state


def processing_branch(
        packages: PackagesTo, repo: RepositoryInfo, state: StateFile, *,
        extras: tuple[ExtraParam, ...], commit_message: str, username: str, user_email: str,
        is_force: bool
) -> StateFile:
    state = install_packages(packages, repo, state, extras=extras, is_force=is_force)

    if state.status() == ChangeStatus.changed:
        logger.debug(f'Updated state in {repo.git.active_branch.name} branch:\n{state}')
        directory = Path(repo.git.working_dir)
        state.save(directory)

        push_installed_packages(repo, commit_message, name=username, email=user_email)
        branch_url = repo.gitlab.branches.get(str(repo.git.active_branch)).web_url
        logger.success(f'Changes have been pushed to {repo.git.active_branch.name} branch (url: {branch_url})')
    else:
        logger.info(f'No changes in {repo.git.active_branch.name} branch. Skip push')
    return state


def install_packages(
        packages: PackagesTo, repo: RepositoryInfo, state: StateFile, *,
        extras: tuple[ExtraParam, ...], is_force: bool
) -> StateFile:
    created_cicd_variables = state.get_all_created_cicd_variables()
    for i, package in enumerate(packages.install, 1):
        logger.info(f"({i}/{len(packages.install)}) Installing {package['name']}@{package['version']} package")
        package_state = state.get_package(package, for_delete=False)
        try:
            response = install_package(
                package, packages.rollback, repo, package_state,
                created_cicd_variables=created_cicd_variables, extras=extras, is_force=is_force
            )
            state.add_package(package, response, package_state)
            created_cicd_variables = update_created_cicd_variables(created_cicd_variables, response)
        except Exception:
            logger.critical(f"An error came out at one stage of installation. "
                            f"Installation {package['name']}@{package['version']} aborted.")
            raise InstallationError('Installation failed in one of the steps. Please check log above')
    return state


def install_package(
        package: PackageLocalData, additional_packages: tuple[PackageLocalData, ...],
        repo: RepositoryInfo, state: PackageState | None, *,
        created_cicd_variables: tuple[str, ...], extras: tuple[ExtraParam, ...], is_force: bool
) -> ScriptResponse | None:
    """ Install package in repository

    :param package: package to be installed
    :param additional_packages: additional packages for when needing to make a rollback
    :param repo: repository information
    :param state: current state for this package
    :param created_cicd_variables: list of created CI/CD variables in previous package installations
    :param extras: extra parameters to be passed to package api
    :param is_force: forced installation
    :return: script response
    """
    if state is None:
        response = init(package, repo, created_cicd_variables=created_cicd_variables, extras=extras, is_force=is_force)
        return response

    state_version = normalize_version(state['version'])
    package_version = normalize_version(package['version'])
    if state_version == package_version:
        logger.info(f"{package['name']}@{package['version']} package is already installed")
        return None

    if state_version < package_version:
        logger.debug(f"Installation version is higher the version installed in the repository "
                     f"({package['version']} > {state['version']}). Update version")
        response = update(
            package, repo, state, created_cicd_variables=created_cicd_variables, extras=extras, is_force=is_force
        )
        return response

    logger.debug(f"Installation version is lower the version installed in the repository "
                 f"({package['version']} < {state['version']}). Rollback version")
    old_package = None
    for additional_package in additional_packages:
        if additional_package['name'] == state['name'] and additional_package['version'] == state['version']:
            old_package = additional_package
            break
    if old_package is None:
        raise PackageNotFoundError(f"Package {package['name']}@{package['version']} not found in "
                                   f"Additional rollback package list:\n{pformat(additional_packages)}")

    raise NotImplementedError("Gear's downgrade is in development")
    # response = rollback(
    #     package, old_package, repo, state,
    #     created_cicd_variables=created_cicd_variables, extras=extras, is_force=is_force
    # )
    # return response
