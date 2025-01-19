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

""" Module with api with types for package developers  """
from dataclasses import dataclass
from pathlib import Path

from gitlab.v4.objects import Project

from git_system_follower.typings.cli import ExtraParam
from git_system_follower.package.cicd_variables import CICDVariable


__all__ = [
    'Parameters', 'SystemParameters', 'System',
    'CICDVariable', 'CICDVariables',
    'ExtraParam', 'ExtraParams'
]


@dataclass(frozen=True)
class SystemParameters:
    project: Project
    created_cicd_vars_names: list[str]
    script_dir: Path
    is_force: bool


@dataclass(frozen=True)
class System:
    host_domain: str


ExtraParamName = str
ExtraParams = dict[ExtraParamName, ExtraParam]

CICDVariableName = str
CICDVariables = dict[CICDVariableName, CICDVariable]


@dataclass(frozen=True)
class Parameters:
    __system_params: SystemParameters
    system: System
    workdir: Path
    extras: ExtraParams
    cicd_variables: CICDVariables
    all_cicd_variables: CICDVariables
    used_template: str
    template_variables: dict[str, str]
