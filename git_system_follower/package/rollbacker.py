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

from git_system_follower.logger import logger
from git_system_follower.package_manager.typings.repository import RepositoryInfo
from git_system_follower.package_manager.typings.package import PackageLocalData
from git_system_follower.package_manager.states import PackageState
from git_system_follower.package_manager.typings.cli import ExtraParam
from git_system_follower.package_manager.typings.script import ScriptResponse
from git_system_follower.package_manager.package.deleter import delete
from git_system_follower.package_manager.package.initer import init


__all__ = ['rollback']


def rollback(
        package: PackageLocalData, old_package: PackageLocalData, repo: RepositoryInfo, state: PackageState, *,
        created_cicd_variables: list[str], extras: tuple[ExtraParam, ...], is_force: bool
) -> ScriptResponse:
    logger.info('==> Package rollback')
    delete(old_package, repo, state, created_cicd_variables=created_cicd_variables, extras=extras, is_force=is_force)
    response = init(package, repo, created_cicd_variables=created_cicd_variables, extras=extras, is_force=is_force)
    return response
