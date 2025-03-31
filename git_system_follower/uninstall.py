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

""" Module with api for `uninstall` command """
from pathlib import Path

from gitlab.v4.objects import Project

from git_system_follower.logger import logger
from git_system_follower.errors import UninstallationError
from git_system_follower.typings.cli import (
    PackageCLI, ExtraParam, PackageCLIImage, PackageCLITarGz, PackageCLISource
)
from git_system_follower.typings.registry import RegistryInfo
from git_system_follower.typings.package import PackageLocalData
from git_system_follower.download import download
from git_system_follower.git_api.gitlab_api import (
    get_gitlab, get_project, get_states, create_mr, merge_mr
)
from git_system_follower.git_api.git_api import checkout_to_new_branch, push_installed_packages
from git_system_follower.git_api.utils import get_packages_str, get_git_repo
from git_system_follower.typings.repository import RepositoryInfo
from git_system_follower.utils.output import print_list
from git_system_follower.utils.retry import retry
from git_system_follower.states import (
    ChangeStatus, PackageState, StateFile,
    get_installed_packages
)
from git_system_follower.package.deleter import delete


__all__ = ['uninstall']


def uninstall(
        packages_cli: tuple[PackageCLIImage | PackageCLITarGz | PackageCLISource, ...],
        repo_url: str, branches: tuple[str, ...], token: str, *,
        extras: tuple[ExtraParam, ...], commit_message: str,
        username: str, user_email: str,
        registry: RegistryInfo, is_force: bool
) -> None:
    gitlab_instance = get_gitlab(repo_url, token)
    project = get_project(gitlab_instance, repo_url)
    states = get_states(project, branches)

    packages = get_packages(packages_cli, states, registry=registry)
    if not packages:
        logger.info('No packages of these versions found in state file')
        return
    print_list(packages, title='Packages', output_func=logger.info,
               key=lambda package: f"{package['name']}@{package['version']}")
    logger.info('Processing branches')
    for i, branch in enumerate(branches, 1):
        logger.info(f'[{i}/{len(branches)}] Processing {branch} branch')
        logger.debug(f'Current state in {branch} branch:\n{states[branch]}')
        validated_packages = validate_packages_dependencies(packages, states[branch])
        print_list(validated_packages, title=f'Uninstallation packages in {branch} branch', output_func=logger.info,
                   key=lambda package: f"{package['name']}@{package['version']}")
        if not validated_packages:
            logger.info(f'There are no packages to delete. Skip deletion for {branch} branch')
            continue
        states[branch] = managing_branch(
            project, branch, token, validated_packages, states[branch], extras=extras,
            commit_message=commit_message, username=username, user_email=user_email, is_force=is_force
        )
    logger.success('Uninstallation complete')


def get_packages(
        packages_cli: tuple[PackageCLIImage | PackageCLITarGz | PackageCLISource, ...],
        states: dict[str, StateFile], *,
        registry: RegistryInfo
) -> tuple[PackageLocalData, ...]:
    installed_packages = get_installed_packages(states)
    downloaded_packages = download(packages_cli, is_deps_first=False, registry=registry)
    packages = []
    for download_package in downloaded_packages:
        for installed_package in installed_packages:
            if _is_necessary_package_to_delete(download_package, installed_package):
                packages.append(download_package)
    return tuple(packages)


def _is_necessary_package_to_delete(download_package: PackageLocalData, installed_package: PackageCLI) -> bool:
    """ Does package need to be deleted: initial check for which packages need to be deleted
    at all (without dependencies)

    :param download_package: downloaded package (package from cli)
    :param installed_package: installed packages from state file
    """
    if download_package['version'] is None:
        return download_package['name'] == installed_package.name
    return (download_package['name'] == installed_package.name and
            download_package['version'] == installed_package.version)


def validate_packages_dependencies(
        packages: tuple[PackageLocalData, ...], state: StateFile
) -> tuple[PackageLocalData, ...]:
    """ Validate packages on which packages should be deleted and which packages should not be deleted.
    To avoid errors when you delete dependencies of one package and the second package uses the same dependency(ies)

    :param packages: packages to be deleted
    :param state: packages specified in branch in state file

    :return: validated packages without dependencies that are used in multiple packages
    """
    result = []
    for i, package in enumerate(packages):
        if _whether_to_delete(package, packages[:i] + packages[i + 1:], state):
            result.append(package)
    return tuple(result)


def _whether_to_delete(
        package: PackageLocalData, packages: tuple[PackageLocalData, ...], state: StateFile
) -> bool:
    """ Does this package need to be removed from the package deletion list

    :param package: package we are looking at
    :param packages: remaining package deletion list (without <package>)
    :param state: current installed package list

    :return: True - if <package> is dependency of another package and this other package should not be deleted;
             False - if <package> is dependency of another package and this other package should be deleted or
                     <package> is not dependency of another package
    """
    is_dependency, for_packages = _is_package_a_dependency(package, state.get_packages())
    if not is_dependency:
        return True
    msg_packages = ', '.join([f"{for_package['name']}@{for_package['version']}" for for_package in for_packages])
    logger.debug(f"{package['name']}@{package['version']} is a dependency for installed packages: {msg_packages}")
    is_delete_main_packages = _whether_to_delete_main_packages(packages, for_packages)

    if is_delete_main_packages:
        logger.debug(f"All packages ({msg_packages}) with {package['name']}@{package['version']} as a dependency "
                     f"will be uninstalled. So uninstall {package['name']}@{package['version']} package")
        return True
    return False


def _is_package_a_dependency(
        package: PackageLocalData, installed_packages: list[PackageState]
) -> tuple[bool, list[PackageState]]:
    """ Whether a package is a dependency of another package

    :param package: package we are looking at
    :param installed_packages: current installed package list

    :return: is dependency of another package; list of another packages which have <package> as dependency
    """
    is_dependency, for_packages = False, []
    for installed_package in installed_packages:
        for dependency in installed_package['dependencies']:
            if dependency == f"{package['name']}@{package['version']}":
                is_dependency = True
                for_packages.append(installed_package)
    return is_dependency, for_packages


def _whether_to_delete_main_packages(
        packages_to_delete: tuple[PackageLocalData, ...], another_packages_with_deps: list[PackageState]
) -> bool:
    """ Whether all packages with dependencies are included in list to be deleted

    :param packages_to_delete: remaining package deletion list (without <package>)
    :param another_packages_with_deps: list of another packages which have <package> as dependency

    :return: whether main packages that contain <package> as a dependency will be deleted
    """
    packages_to_delete_with_deps = [package for package in packages_to_delete if package['dependencies']]

    checked = []
    for another_package_with_deps in another_packages_with_deps:
        for package_to_delete_with_deps in packages_to_delete_with_deps:
            if (another_package_with_deps['name'] == package_to_delete_with_deps['name'] and
                    another_package_with_deps['version'] == package_to_delete_with_deps['version']):
                checked.append(another_package_with_deps)

    for package in another_packages_with_deps:
        if package not in checked:
            logger.debug(f"{package['name']}@{package['version']} with this dependency will not be uninstalled, "
                         f"exclude dependency from uninstallation list")
            break
    return another_packages_with_deps == checked


@retry(output_func=logger.info, error_output_func=logger.error)
def managing_branch(
        project: Project, branch: str, token: str, packages: tuple[PackageLocalData, ...], state: StateFile, *,
        extras: tuple[ExtraParam, ...], commit_message: str, username: str, user_email: str,
        is_force: bool
) -> StateFile:
    repo = RepositoryInfo(gitlab=project, git=get_git_repo(project, token))
    checkout_to_new_branch(repo.git, branch)

    logger.info(':: Uninstalling packages')
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
        description=f'Installed package(s): {get_packages_str(packages)}'
    )
    logger.info(':: Merging merge request')
    merge_mr(repo.gitlab, mr)
    return state


def processing_branch(
        packages: tuple[PackageLocalData, ...], repo: RepositoryInfo, state: StateFile, *,
        extras: tuple[ExtraParam, ...], commit_message: str, username: str, user_email: str,
        is_force: bool
) -> StateFile:
    state = uninstall_packages(packages, repo, state, extras=extras, is_force=is_force)

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


def uninstall_packages(
        packages: tuple[PackageLocalData, ...], repo: RepositoryInfo, state: StateFile, *,
        extras: tuple[ExtraParam, ...], is_force: bool
) -> StateFile:
    if not state.get_packages():
        logger.info('No packages installed')
        return state
    created_cicd_variables = state.get_all_created_cicd_variables()
    for i, package in enumerate(packages, 1):
        logger.info(f"({i}/{len(packages)}) Uninstalling {package['name']}@{package['version']} package")
        package_state = state.get_package(package, for_delete=True)
        if package_state is None:
            logger.info(f"{package['name']}@{package['version']} package is not installed")
            continue
        try:
            delete(
                package, repo, package_state,
                created_cicd_variables=created_cicd_variables, extras=extras, is_force=is_force
            )
            state.delete_package(package_state)
        except Exception:
            logger.critical(f"An error came out at one stage of uninstallation. "
                            f"Uninstallation {package['name']}@{package['version']} aborted")
            raise UninstallationError('Uninstallation failed in one of the steps. Please check log above')
    return state
