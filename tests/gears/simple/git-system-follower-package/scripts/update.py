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

from git_system_follower.develop.api.types import Parameters
from git_system_follower.develop.api.cicd_variables import CICDVariable, create_variable, delete_variable
from git_system_follower.develop.api.templates import update_template


def main(parameters: Parameters):
    template_variables_names = []
    variables = {}
    for name in template_variables_names:
        if (variable := parameters.extras.get(name)) is not None:
            variables[variable.name] = variable
    update_template(parameters, variables)

    for name, extra in parameters.extras.items():
        if name in template_variables_names:
            continue

        if name in parameters.cicd_variables:
            delete_variable(parameters, parameters.cicd_variables[name])
        create_variable(parameters, CICDVariable(
            name=extra.name,
            value=extra.value,
            env='*',
            masked=extra.masked
        ))
