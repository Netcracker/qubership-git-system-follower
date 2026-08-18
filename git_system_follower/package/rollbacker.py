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
from git_system_follower.typings.repository import RepositoryInfo
from git_system_follower.typings.package import PackageLocalData
from git_system_follower.states import PackageState
from git_system_follower.typings.cli import ExtraParam
from git_system_follower.typings.script import ScriptResponse
from git_system_follower.package.deleter import delete
from git_system_follower.package.initer import init
from git_system_follower.git_api.gitlab_api import delete_tag


__all__ = ['rollback']


def rollback(
        package: PackageLocalData, old_package: PackageLocalData, repo: RepositoryInfo, state: PackageState, *,
        created_cicd_variables: tuple[str, ...], extras: tuple[ExtraParam, ...], is_autoheal: bool,
        is_skip_force_rollback: bool, is_force: bool
) -> ScriptResponse:
    logger.info('==> Package rollback')
    if is_skip_force_rollback:
        # rollback with validation does a delete and init
        delete(old_package, repo, state, created_cicd_variables=created_cicd_variables, created_webhooks=tuple([]),
               extras=extras, is_force=is_force)
        response = init(package, repo, state, created_cicd_variables=tuple([]), created_webhooks=tuple([]),
                       extras=extras, is_autoheal=is_autoheal, is_force=is_force)
    else:
        # rollback by default without validation does a force reinstall
        response = init(package, repo, state, created_cicd_variables=tuple([]), created_webhooks=tuple([]),
                       extras=extras, is_autoheal=is_autoheal, is_force=True)
    _delete_release_tag_if_component(repo, old_package)
    return response


def _delete_release_tag_if_component(repo: RepositoryInfo, old_package: PackageLocalData) -> None:
    """ Remove the release tag of the rolled back (removed) version.

    Component gears publish a release tag on install; when a rollback removes that
    version, the tag must be deleted too — mirroring what `uninstall` does.
    """
    if old_package.get('subtype') != 'component':
        return
    release_version = old_package['version']
    release_name = old_package.get('name') or release_version
    try:
        delete_tag(repo.gitlab, release_version)
        logger.success(f":: Release removed {release_name}@{release_version}")
    except Exception as e:
        logger.warning(e)
