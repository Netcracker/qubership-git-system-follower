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

from git_system_follower.develop.api.types import Parameters, ExtraParams
from git_system_follower.develop.api.cicd_variables import CICDVariable, create_variable
from git_system_follower.develop.api.templates import create_template

VAR1 = 'VAR1'

def main(parameters: Parameters):
    variables = check_prerequisites(parameters.extras)
    if (tags := parameters.extras.get('TAGS')) is not None:
        variables['TAGS'] = tags
    create_template(parameters, 'default', variables)

    for name, extra in parameters.extras.items():
        if name in variables.keys():
            continue

        create_variable(parameters, CICDVariable(
            name=extra.name,
            value=extra.value,
            env='*',
            masked=extra.masked
        ))

def check_prerequisites(extras: ExtraParams) -> ExtraParams:
    return { VAR1 : 'VAR1'}