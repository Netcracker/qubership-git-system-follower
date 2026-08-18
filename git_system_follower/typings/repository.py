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

from dataclasses import dataclass
from typing import Optional
from gitlab.v4.objects import Project
from git import Repo
from git_system_follower.utils.singleton import Singleton

__all__ = ['RepositoryInfo']


@dataclass(frozen=True)
class RepositoryInfoData:
    gitlab: Project
    git: Repo
    repo_url: str
    token: str


class RepositoryInfo(Singleton):
    def __init__(self):
        if not hasattr(self, '_data'):
            self._data: Optional[RepositoryInfoData] = None

    def initialize(self, gitlab: Project, git: Repo, repo_url: str, token: str) -> 'RepositoryInfo':
        if self._data is not None:
            raise RuntimeError("RepositoryInfo already initialized")
        self._data = RepositoryInfoData(gitlab, git, repo_url, token)
        return self

    @property
    def gitlab(self) -> Project:
        if self._data is None:
            raise RuntimeError("RepositoryInfo not initialized")
        return self._data.gitlab
    @property
    def git(self) -> Repo:
        if self._data is None:
            raise RuntimeError("RepositoryInfo not initialized")
        return self._data.git
    @property
    def repo_url(self) -> str:
        if self._data is None:
            raise RuntimeError("RepositoryInfo not initialized")
        return self._data.repo_url
    @property
    def token(self) -> str:
        if self._data is None:
            raise RuntimeError("RepositoryInfo not initialized")
        return self._data.token
