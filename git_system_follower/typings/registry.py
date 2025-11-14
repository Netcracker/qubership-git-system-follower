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

from enum import Enum
from dataclasses import dataclass
from typing import Optional

from git_system_follower.typings.cli import Credentials


__all__ = ['RegistryTypes', 'RegistryInfo']


class RegistryTypes(Enum):
    auto = 'Autodetect'
    dockerhub = 'Dockerhub'
    nexus = 'Nexus'
    artifactory = 'Artifactory'
    awsecr = 'AwsEcr'


@dataclass
class RegistryInfo:
    credentials: Optional[Credentials]
    type: RegistryTypes
    is_insecure: bool
