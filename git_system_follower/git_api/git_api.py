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

from git import Repo

import gitlab

from git_system_follower.logger import logger
from git_system_follower.typings.repository import RepositoryInfo


__all__ = ['checkout_to_new_branch', 'push_installed_packages']


def checkout_to_new_branch(repo: Repo, base_branch: str) -> str:
    new_branch = f'{base_branch}.temp-manage-packages'
    repo.git.checkout(base_branch)
    repo.remotes.origin.pull(base_branch)

    for branch in repo.heads:
        if branch.name == new_branch:
            repo.delete_head(new_branch, force=True)
            logger.debug(f'Local branch {new_branch} deleted')
            break

    repo.git.checkout('-b', new_branch)
    logger.success(f'Created new {new_branch} local branch (local repo: {repo.git.working_dir})')
    return new_branch


def push_installed_packages(repo: RepositoryInfo, msg: str, *, name: str, email: str) -> None:
    """ Push changes to remote repository

    :param repo: repo information
    :param msg: commit message
    :param name: user name for commit changes
    :param email: user email for commit changes
    """
    try:
        repo.gitlab.branches.delete(repo.git.active_branch.name)
    except gitlab.exceptions.GitlabDeleteError:
        # if temp branch does not exist
        pass

    repo.git.git.add(A=True)

    repo.git.config_writer().set_value('user', 'name', name).release()
    repo.git.config_writer().set_value('user', 'email', email).release()
    repo.git.index.commit(msg)

    repo.git.remotes.origin.push(repo.git.active_branch.name)
