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

from enum import IntFlag

import gitlab
from git import Repo

from git_system_follower.logger import logger
from git_system_follower.typings.repository import RepositoryInfo


__all__ = ['checkout_to_new_branch', 'push_installed_packages']


class PushFlags(IntFlag):
    NEW_TAG = 1
    NEW_HEAD = 2
    NO_MATCH = 4
    REJECTED = 8
    REMOTE_REJECTED = 16
    REMOTE_FAILURE = 32
    DELETED = 64
    FORCED_UPDATE = 128
    FAST_FORWARD = 256
    UP_TO_DATE = 512
    ERROR = 1024

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
    result = interpret_push_info(repo.git.remotes.origin.push(repo.git.active_branch.name)[0])
    if not result['flags']:
        logger.critical(f"[{result['reason']}] Push to remote repository failed with reason: {result['summary']}")
        raise SystemExit

def interpret_push_info(push_info) -> dict:
    """ Interpret GitPython push_info flags and return structured result.
    For more details see https://gitpython.readthedocs.io/en/stable/reference.html#git.remote.PushInfo

    :param push_info: A GitPython PushInfo object
    :return: dict with status flags, reason, and summary
    """
    flags = PushFlags(push_info.flags)
    summary = push_info.summary

    status_checks = [
        (PushFlags.ERROR not in flags, True, "SUCCESS"),
        (PushFlags.UP_TO_DATE in flags, True, "UP_TO_DATE"),
        (PushFlags.NEW_HEAD in flags, True, "NEW_HEAD"),
        (PushFlags.NEW_TAG in flags, True, "NEW_TAG"),
        (PushFlags.FAST_FORWARD in flags, True, "FAST_FORWARD"),
        (PushFlags.FORCED_UPDATE in flags, True, "FORCED_UPDATE"),
        (PushFlags.DELETED in flags, False, "DELETED"),
        (PushFlags.REJECTED in flags, False, "REJECTED"),
        (PushFlags.NO_MATCH in flags, False, "NO_MATCH"),
        (PushFlags.REMOTE_FAILURE in flags, False, "REMOTE_FAILURE"),
        (PushFlags.REMOTE_REJECTED in flags, False, "REMOTE_REJECTED"),
        (PushFlags.ERROR in flags, False, "ERROR"),
    ]

    for condition, is_success, reason in status_checks:
        if condition:
            return {
                "flags": is_success,
                "reason": reason,
                "summary": summary
            }

    return {
        "flags": False,
        "reason": "OTHERS",
        "summary": summary
    }
