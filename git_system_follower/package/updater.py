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

from gitlab.v4.objects import Project

from git_system_follower.logger import logger
from git_system_follower.variables import PACKAGE_DIRNAME, SCRIPTS_DIR
from git_system_follower.typings.repository import RepositoryInfo
from git_system_follower.typings.package import PackageLocalData
from git_system_follower.states import PackageState
from git_system_follower.typings.cli import ExtraParam
from git_system_follower.typings.script import ScriptResponse
from git_system_follower.package.script import run_script
from git_system_follower.package.cicd_variables import CICDVariable, get_cicd_variables
from git_system_follower.package.webhooks import Webhook, get_webhooks
from git_system_follower.utils.utility import get_package_dependency
from git_system_follower.utils.version_comparer import VersionComparer


__all__ = ['update']


def update(
        package: PackageLocalData, repo: RepositoryInfo, state: PackageState, *,
        created_cicd_variables: tuple[str, ...], created_webhooks: tuple[str, ...],
        extras: tuple[ExtraParam, ...], is_autoheal: bool, is_force: bool
) -> ScriptResponse:
    logger.info('==> Package update')
    workdir = Path(repo.git.working_dir)
    versions, current_version = get_version_dirs(package, state['version'])
    response = None
    for version_dir in versions:
        current_cicd_variables = get_cicd_variables(repo.gitlab)
        current_webhooks = get_webhooks(repo.gitlab)
        response = run_update_script(
            version_dir, workdir, repo.gitlab, current_cicd_variables, current_webhooks, state,
            current_version_dir=current_version, created_cicd_variables=created_cicd_variables,
            created_webhooks=created_webhooks, extras=extras, is_autoheal=is_autoheal, is_force=is_force
        )
        logger.info(f"Updated to {package['name']}@{version_dir.name} version")
        current_version = version_dir
    return response


def get_version_dirs(package: PackageLocalData, start_version: str) -> tuple[tuple[Path, ...], Path]:
    path = package['path'] / PACKAGE_DIRNAME / SCRIPTS_DIR
    if not path.exists():
        raise FileNotFoundError(f'Scripts directory is missing ({path.absolute()})')

    comparer = VersionComparer()
    versions = []
    current_version = Path()

    # Check if upgrading from quarterly to semver
    is_quarterly_to_semver = (comparer.is_quarterly(start_version) and
                               not comparer.is_quarterly(package['version']))

    files = path.glob('*')
    for file in files:
        if file.is_file():
            continue

        # Check for current version match
        if comparer.compare(start_version, file.name) == 0:
            current_version = file

        # Determine if this version should be included in update path
        if is_quarterly_to_semver:
            # For quarterly -> semver: include all quarterly > start, plus the target semver
            if comparer.is_quarterly(file.name):
                # Include quarterly versions > start
                if comparer.compare(start_version, file.name) < 0:
                    versions.append(file)
            else:
                # Include only the exact target semver version
                if comparer.compare(file.name, package['version']) == 0:
                    versions.append(file)
        else:
            # Normal case: start_version < file_version <= end_version
            is_greater_than_start = comparer.compare(start_version, file.name) < 0
            is_less_equal_end = comparer.compare(file.name, package['version']) <= 0
            if is_greater_than_start and is_less_equal_end:
                versions.append(file)

    # Sort versions using VersionComparer
    versions = sorted(versions, key=lambda v: (comparer.compare('0.0.0', v.name), v.name))
    return tuple(versions), current_version


def run_update_script(
        script_dir: Path, workdir: Path, project: Project, current_cicd_variables: dict[str, CICDVariable],
        current_webhooks: dict[str, Webhook], state: PackageState, *, current_version_dir: Path,
        created_cicd_variables: tuple[str, ...], created_webhooks: tuple[str, ...],
        extras: tuple[ExtraParam, ...], is_autoheal: bool, is_force: bool
) -> ScriptResponse:
    logger.info('\tRunning update package api')
    path = script_dir / 'update.py'
    get_package_dependency(script_dir)
    response = run_script(
        path, workdir, project, current_cicd_variables, current_webhooks, state['used_template'],
        current_version_dir=current_version_dir, created_cicd_variables=created_cicd_variables,
        created_webhooks=created_webhooks, extras=extras, is_autoheal=is_autoheal, is_force=is_force,
        state=state
    )
    return response
