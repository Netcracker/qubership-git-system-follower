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

""" Module with package types (package.yaml in package root folder) """
from enum import Enum
from typing import TypedDict
from pathlib import Path
from dataclasses import dataclass

from git_system_follower.typings.cli import (
    PackageCLI, PackageCLIImage, PackageCLITarGz, PackageCLISource
)


__all__ = ['PackageType', 'PackageData', 'PackageLocalData', 'PackagesTo']


class PackageType(Enum):
    gitlab_ci_pipeline = 1


class PackageData(TypedDict):
    """ Class for type hinting for python code: data from package.yaml """
    apiVersion: str
    type: PackageType
    name: str
    version: str

    dependencies: tuple[PackageCLI | PackageCLIImage | PackageCLITarGz | PackageCLISource, ...]


class PackageLocalData(PackageData):
    """ Class for type hinting for python code: data from package.yaml with local data """
    path: Path


@dataclass
class PackagesTo:
    # Packages to be installed. Is set by user using cli
    install: tuple[PackageLocalData, ...]
    # Packages to be deleted. Is set by this tool using state files.
    # It is necessary for case when user want to install a lower package version. New versions know
    # how to install/update/delete old versions, and old versions don't know about new versions
    rollback: tuple[PackageLocalData, ...]
