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

""" Module with cli types """
from dataclasses import dataclass
from typing import NamedTuple
from pathlib import Path
from enum import Enum


__all__ = [
    'PackageCLITypes', 'PackageCLI',
    'PackageCLIImage', 'PackageCLITarGz', 'PackageCLISource',
    'ExtraParam', 'Credentials'
]


# Types for packages
class PackageCLITypes(Enum):
    unknown = 0
    image = 1
    targz = 2
    source = 3


@dataclass(frozen=True, kw_only=True)
class PackageCLI:
    type: PackageCLITypes = PackageCLITypes.unknown
    name: str | None = None
    version: str | None = None

    def __str__(self):
        return f'{self.name}@{self.version}'


@dataclass(frozen=True, kw_only=True)
class PackageCLIImage(PackageCLI):
    type: PackageCLITypes = PackageCLITypes.image

    registry: str
    repository: str
    image: str
    tag: str = 'latest'

    def get_image_path(self) -> str:
        """ Get image path (without registry) """
        path = f'{self.repository}/' if self.repository else ''
        return f'{path}{self.image}:{self.tag}'

    def __str__(self):
        return f'{self.registry}/{self.get_image_path()}'


@dataclass(frozen=True, kw_only=True)
class PackageCLITarGz(PackageCLI):
    type: PackageCLITypes = PackageCLITypes.targz

    path: Path

    def __str__(self):
        return str(self.path)


@dataclass(frozen=True, kw_only=True)
class PackageCLISource(PackageCLI):
    type: PackageCLITypes = PackageCLITypes.source

    path: Path

    def __str__(self):
        return str(self.path)


class ExtraParam(NamedTuple):
    name: str
    value: str
    masked: bool


class Credentials(NamedTuple):
    username: str
    password: str
    # for adding token necessary to think use this class or create several class,
    # e.g. Token = str, Auth = Optional[Union[Credentials, Token]]
