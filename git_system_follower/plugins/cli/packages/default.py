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

from git_system_follower.typings.cli import PackageCLISource, PackageCLITarGz, PackageCLIImage
from git_system_follower.plugins.cli.packages import hookimpl
from git_system_follower.plugins.cli.packages.specs import HookSpec


__all__ = ['SourcePlugin', 'TarGzPlugin', 'ImagePlugin']


class SourcePlugin(HookSpec):
    @hookimpl
    def match(self, value: str) -> bool:
        path = Path(value)
        return path.is_dir() and path.exists()

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
        return path.name.endswith(self.suffix) and path.exists()

    @hookimpl
    def get_gears(self, value: str, **kwargs) -> list[PackageCLITarGz]:
        return [PackageCLITarGz(path=Path(value))]

    def __str__(self) -> str:
        return self.value


class ImagePlugin(HookSpec):
    default_registry = "docker.io"
    default_repository = "library"
    default_tag = "latest"

    @hookimpl
    def match(self, value: str) -> bool:
        # always returns True, as it is the last possible option for passing Gears.
        # If there are problems with parsing the image, it will fail at this
        return True

    @hookimpl
    def get_gears(self, value: str, **kwargs) -> list[PackageCLIImage]:
        return [self.parse_image(value)]

    def parse_image(self, package: str) -> PackageCLIImage:
        name, ref = self._resolve_nameref(package)

        parts = name.split("/")
        if self._is_registry(parts[0]):
            registry, parts = parts[0], parts[1:]
        else:
            registry = self.default_registry

        if not parts:
            err = f"Invalid image reference: {ref}"
            raise ValueError(err)

        # docker.io case: separate services for different things:
        #   api - registry-1.docker.io,
        #   auth - auth.docker.io,
        #   etc.
        if registry == self.default_registry and len(parts) == 1:
            repository, image = self.default_repository, parts[0]
        else:
            repository, image = "/".join(parts[:-1]), parts[-1]

        return PackageCLIImage(registry=registry, repository=repository, image=image, ref=ref)

    def _resolve_nameref(self, image: str) -> tuple[str, str]:
        if "@" in image:
            return image.rsplit("@", 1)
        if ":" in image and "/" in image and image.rfind(":") > image.rfind("/"):
            return image.rsplit(":", 1)
        if ":" in image and "/" not in image:
            return image.rsplit(":", 1)
        return image, self.default_tag

    @staticmethod
    def _is_registry(component: str) -> bool:
        return any(x in component for x in (".", ":")) or component == "localhost"

    def __str__(self) -> str:
        return self.value
