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
from git_system_follower.utils.versions import normalize_version


__all__ = ['update']


def update(
        package: PackageLocalData, repo: RepositoryInfo, state: PackageState, *,
        created_cicd_variables: tuple[str, ...], extras: tuple[ExtraParam, ...], is_force: bool
) -> ScriptResponse:
    logger.info('==> Package update')
    workdir = Path(repo.git.working_dir)
    versions = get_version_dirs(package, state['version'])
    response = None
    for version_dir in versions:
        current_cicd_variables = get_cicd_variables(repo.gitlab)
        response = run_update_script(
            version_dir, workdir, repo.gitlab, current_cicd_variables, state,
            created_cicd_variables=created_cicd_variables, extras=extras, is_force=is_force
        )
        logger.info(f"Updated to {package['name']}@{version_dir.name} version")
    return response


def get_version_dirs(package: PackageLocalData, start_version: str) -> tuple[Path, ...]:
    path = package['path'] / PACKAGE_DIRNAME / SCRIPTS_DIR
    if not path.exists():
        raise FileNotFoundError(f'Scripts directory is missing ({path.absolute()})')

    start_version = normalize_version(start_version)
    end_version = normalize_version(package['version'])
    versions = []
    files = path.glob('*')
    for file in files:
        if file.is_file():
            continue
        file_version = normalize_version(file.name)
        if start_version < file_version <= end_version:
            versions.append(file)
    versions = sorted(versions, key=lambda v: normalize_version(v.name))
    return tuple(versions)


def run_update_script(
        script_dir: Path, workdir: Path, project: Project, current_cicd_variables: dict[str, CICDVariable],
        state: PackageState, *,
        created_cicd_variables: tuple[str, ...], extras: tuple[ExtraParam, ...], is_force: bool
) -> ScriptResponse:
    logger.info('\tRunning update package api')
    path = script_dir / 'update.py'
    response = run_script(
        path, workdir, project, current_cicd_variables, state['used_template'],
        created_cicd_variables=created_cicd_variables, extras=extras, is_force=is_force, state=state
    )
    return response
