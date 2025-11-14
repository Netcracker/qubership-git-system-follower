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
from git_system_follower.package import cicd_variables
from tests.config import vcr_instance, project

@pytest.mark.unit
@pytest.mark.parametrize("key, value, env, is_masked", [
    ("test_variable", "test", "test_env", False),  # Non-masked variable
    # ("test_variableM", "testM", "test_env", True),  # Masked variable (To be added)
])
@vcr_instance.use_cassette("test_create_variable")
def test_variable_creation_and_deletion(key, value, env, is_masked):
    variable = cicd_variables.CICDVariable(
        name=key,
        value=value,
        env=env,
        masked=is_masked
    )
    # Create
    cicd_variables.create_variable(
        project=project,
        variable=variable,
        is_force=False
    )
    # Delete
    cicd_variables.delete_variable(
        project=project,
        variable=variable,
        is_force=False
    )
