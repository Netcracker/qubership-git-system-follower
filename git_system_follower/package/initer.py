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
from git_system_follower.typings.cli import ExtraParam
from git_system_follower.typings.script import ScriptResponse
from git_system_follower.package.script import run_script
from git_system_follower.package.cicd_variables import CICDVariable, get_cicd_variables


__all__ = ['init']


def init(
        package: PackageLocalData, repo: RepositoryInfo, *,
        created_cicd_variables: tuple[str, ...], extras: tuple[ExtraParam, ...], is_force: bool
) -> ScriptResponse:
    logger.info('==> Package initialization')
    workdir = Path(repo.git.working_dir)
    scripts_dir = package['path'] / PACKAGE_DIRNAME / SCRIPTS_DIR / package['version']
    if not scripts_dir.exists():
        raise FileNotFoundError(f'Scripts directory is missing ({scripts_dir.absolute()})')

    current_cicd_variables = get_cicd_variables(repo.gitlab)
    response = run_init_script(
        scripts_dir, workdir, repo.gitlab, current_cicd_variables,
        created_cicd_variables=created_cicd_variables, extras=extras, is_force=is_force
    )
    logger.success(f"Installed {package['name']}@{package['version']} package")
    return response


def run_init_script(
        script_dir: Path, workdir: Path, project: Project, current_cicd_variables: dict[str, CICDVariable], *,
        created_cicd_variables: tuple[str, ...], extras: tuple[ExtraParam, ...], is_force: bool
) -> ScriptResponse:
    logger.info('\tRunning init package api')
    path = script_dir / 'init.py'
    response = run_script(
        path, workdir, project, current_cicd_variables,
        used_template=None, created_cicd_variables=created_cicd_variables, extras=extras, is_force=is_force
    )
    return response
