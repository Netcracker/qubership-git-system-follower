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
import re

import click

from git_system_follower.errors import ParsePackageNameError


__all__ = [
    'Package', 'PackageCLITypes', 'PackageCLI', 'parse_image',
    'PackageCLIImage', 'PackageCLITarGz', 'PackageCLISource',
    'ExtraParamTuple', 'ExtraParam',
    'PACKAGE_SUFFIX'
]


PACKAGE_SUFFIX = '.tar.gz'
IMAGE_PATTERN = r'^(?P<registry>[^:/]+(:\d+)?)\/(?P<path>.+)\/(?P<image_name>[^:]+)(:(?P<image_version>.+))?$'


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
        path = f'{self.repository}/{self.image}'
        path += f':{self.tag}' if self.tag is not None else ''
        return path

    def __str__(self):
        return f'{self.registry}/{self.repository}/{self.image}:{self.tag}'


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


class PackageType(click.ParamType):
    """ Class for checking parameters from click cli """
    name = 'package'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def convert(self, value: str, param, ctx) -> PackageCLIImage | PackageCLITarGz | PackageCLISource:
        if re.match(IMAGE_PATTERN, value):
            return parse_image(value)
        if is_targz(value):
            return PackageCLITarGz(path=Path(value))
        if is_source(value):
            return PackageCLISource(path=Path(value))
        raise ParsePackageNameError(
            f'Failed to determine package type of {value}. '
            f'Available types:\n'
            f'1. docker image (regexp: "{IMAGE_PATTERN}"),\n'
            f'2. .tar.gz archive (passed as path),\n'
            f'3. source directory (passed as path)\n'
            f'If you specified an .tar.gz archive or directory, please make sure it exist'
        )

    @staticmethod
    def _is_valid(value: str) -> bool:
        # TODO: implement validation
        return True


def parse_image(package: str) -> PackageCLIImage:
    match = re.match(IMAGE_PATTERN, package)
    if not match:
        raise ParsePackageNameError(f'Failed to parse {package} package name with regular expression')

    registry, repository = match.group('registry'), match.group('path')
    image, tag = match.group('image_name'), match.group('image_version')
    if tag is None:
        return PackageCLIImage(registry=registry, repository=repository, image=image)
    return PackageCLIImage(registry=registry, repository=repository, image=image, tag=tag)


def is_targz(package: str) -> bool:
    path = Path(package)
    return path.name.endswith(PACKAGE_SUFFIX)


def is_source(package: str) -> bool:
    path = Path(package)
    if not path.is_dir():
        return False
    return True


Package = PackageType()


class ExtraParam(NamedTuple):
    name: str
    value: str
    masked: bool


class ExtraParamTuple(click.Tuple):
    name = 'extra_param'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def convert(self, value, param, ctx):
        values = super().convert(value, param, ctx)
        return ExtraParam(name=values[0], value=values[1], masked=True if values[2] == 'masked' else False)
