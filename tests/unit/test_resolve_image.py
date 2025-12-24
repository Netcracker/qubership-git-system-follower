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

import pytest

from git_system_follower.typings.cli import PackageCLIImage
from git_system_follower.plugins.cli.packages.default import ImagePlugin


@pytest.mark.parametrize(
    "image,result", [
        ("alpine", PackageCLIImage(registry="docker.io", repository="library", image="alpine", ref="latest")),
        ("alpine:1.2.3", PackageCLIImage(registry="docker.io", repository="library", image="alpine", ref="1.2.3")),
        (
            "alpine@sha256:a738d442f54893d4f45cf5675e965d2d16f90adb4d1a1bf22e540513c1ce8e83",
            PackageCLIImage(
                registry="docker.io", repository="library", image="alpine",
                ref="sha256:a738d442f54893d4f45cf5675e965d2d16f90adb4d1a1bf22e540513c1ce8e83"
        )),
        ("mcp/time", PackageCLIImage(registry="docker.io", repository="mcp", image="time", ref="latest")),
        ("ghcr.io/org/app:v1", PackageCLIImage(registry="ghcr.io", repository="org", image="app", ref="v1")),
        ("localhost/app", PackageCLIImage(registry="localhost", repository="", image="app", ref="latest")),
        (
            "nexus.company.com:5000/alpine",
            PackageCLIImage(registry="nexus.company.com:5000", repository="", image="alpine", ref="latest")
        ),
    ]
)
def test_resolve_image(image: str, result: PackageCLIImage):
    assert ImagePlugin().parse_image(image) == result
