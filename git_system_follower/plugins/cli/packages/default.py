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
import re

from git_system_follower.errors import ParsePackageNameError
from git_system_follower.typings.cli import PackageCLISource, PackageCLITarGz, PackageCLIImage
from git_system_follower.plugins.cli.packages import hookimpl
from git_system_follower.plugins.cli.packages.specs import HookSpec


__all__ = ['SourcePlugin', 'TarGzPlugin', 'ImagePlugin']


class SourcePlugin(HookSpec):
    @hookimpl
    def match(self, value: str) -> bool:
        path = Path(value)
        return path.is_dir()

    @hookimpl
    def get_gears(self, value: str, **kwargs) -> list[PackageCLISource]:
        return [PackageCLISource(path=Path(value))]

    def __str__(self) -> str:
        return self.value


class TarGzPlugin(HookSpec):
    suffix = '.tar.gz'

    @hookimpl
    def match(self, value: str) -> bool:
        path = Path(value)
        return path.name.endswith(self.suffix)

    @hookimpl
    def get_gears(self, value: str, **kwargs) -> list[PackageCLITarGz]:
        return [PackageCLITarGz(path=Path(value))]

    def __str__(self) -> str:
        return self.value


class ImagePlugin(HookSpec):
    pattern = r'^(?P<registry>[^:/]+(:\d+)?)\/(?P<path>.+)\/(?P<image_name>[^:]+)(:(?P<image_version>.+))?$'

    @hookimpl
    def match(self, value: str) -> bool:
        if re.match(self.pattern, value):
            return True
        return False

    @hookimpl
    def get_gears(self, value: str, **kwargs) -> list[PackageCLIImage]:
        return [self.parse_image(value)]

    def parse_image(self, package: str) -> PackageCLIImage:
        match = re.match(self.pattern, package)
        if not match:
            raise ParsePackageNameError(f'Failed to parse {package} package name with regular expression')

        registry, repository = match.group('registry'), match.group('path')
        image, tag = match.group('image_name'), match.group('image_version')
        if tag is None:
            return PackageCLIImage(registry=registry, repository=repository, image=image)
        return PackageCLIImage(registry=registry, repository=repository, image=image, tag=tag)

    def __str__(self) -> str:
        return self.value
