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
from git_system_follower.plugins.cli.packages import hookimpl, Result



class SourcePlugin:
    @hookimpl
    def process_gear(self, value: str) -> Result:
        path = Path(value)
        if path.is_dir():
            return Result(package=PackageCLISource(path=path), is_processed=True)
        return Result(package=None, is_processed=False)


class TarGzPlugin:
    suffix = '.tar.gz'

    @hookimpl
    def process_gear(self, value: str) -> Result:
        path = Path(value)
        if path.name.endswith(self.suffix):
            return Result(package=PackageCLITarGz(path=path), is_processed=True)
        return Result(None, False)


class ImagePlugin:
    pattern = r'^(?P<registry>[^:/]+(:\d+)?)\/(?P<path>.+)\/(?P<image_name>[^:]+)(:(?P<image_version>.+))?$'

    @hookimpl
    def process_gear(self, value: str) -> Result:
        if re.match(self.pattern, value):
            return Result(package=self.parse_image(value), is_processed=True)
        return Result(None, False)

    def parse_image(self, package: str) -> PackageCLIImage:
        match = re.match(self.pattern, package)
        if not match:
            raise ParsePackageNameError(f'Failed to parse {package} package name with regular expression')

        registry, repository = match.group('registry'), match.group('path')
        image, tag = match.group('image_name'), match.group('image_version')
        if tag is None:
            return PackageCLIImage(registry=registry, repository=repository, image=image)
        return PackageCLIImage(registry=registry, repository=repository, image=image, tag=tag)
