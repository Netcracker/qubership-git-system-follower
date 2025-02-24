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
from urllib.parse import urlparse, urlunparse

from git import Repo
from git.config import GitConfigParser
from gitlab.v4.objects import Project

from git_system_follower.logger import logger
from git_system_follower.variables import REPOS_PATH
from git_system_follower.typings.cli import PackageCLI
from git_system_follower.typings.package import PackageLocalData


__all__ = ['get_config', 'get_packages_str', 'get_git_repo']


def get_config(path: str):
    path = Path(path).expanduser()
    return GitConfigParser(path, read_only=True)


def get_packages_str(packages: tuple[PackageLocalData | PackageCLI, ...]) -> str:
    if isinstance(packages[0], dict):
        return ', '.join([f"{package['name']}@{package['version']}" for package in packages])
    return ', '.join([str(package) for package in packages])


def get_git_repo(project: Project, token: str) -> Repo:
    """ Clone/get git repo

    :param project: gitlab project
    :param token: access token
    """
    url = project.http_url_to_repo
    directory = get_repo_directory_path(url)
    if directory.exists():
        logger.debug(f'Local repository {directory} is used')
        repo = Repo(directory)
        repo.remotes.origin.fetch()
        return repo
    url = get_url_with_token(url, token)
    repo = Repo.clone_from(url, directory)
    logger.debug(f'Repository cloned into {directory} folder')
    return repo


def get_repo_directory_path(repo_url: str) -> Path:
    name = repo_url.split('/')[-1].replace('.git', '')
    return REPOS_PATH / name


def get_url_with_token(url: str, token: str) -> str:
    url = urlparse(url)
    url = url._replace(netloc=f'auth2:{token}@{url.netloc}')
    return str(urlunparse(url))
