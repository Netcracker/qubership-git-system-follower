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
from unittest.mock import Mock
from gitlab.exceptions import GitlabGetError

from git_system_follower.package import cicd_variables
from git_system_follower.utils import cicd_utils

@pytest.mark.unit
@pytest.mark.parametrize("key, value, env, is_masked", [
    ("test_variable", "test", "test_env", False),  # Non-masked variable
])
def test_variable_creation_and_deletion(key, value, env, is_masked):
    """ Create then delete a CI/CD variable using mocked GitLab project """

    # --- Create phase: variable does not exist -> variables.get 404s -> create ---
    project_create = Mock()
    project_create.variables.get.side_effect = GitlabGetError("not found")

    mock_created = Mock()
    mock_created.key = key
    mock_created.value = value
    mock_created.environment_scope = env
    mock_created.masked = is_masked
    project_create.variables.create.return_value = mock_created

    variable = cicd_variables.CICDVariable(
        name=key,
        value=value,
        env=env,
        masked=is_masked
    )
    cicd_variables.create_variable(
        project=project_create,
        variable=variable,
        is_force=False
    )
    project_create.variables.get.assert_called_with(key)
    project_create.variables.create.assert_called_once()

    # --- Delete phase: variable exists -> variables.get finds it -> delete ---
    project_delete = Mock()
    existing = Mock()
    existing.key = key
    existing.value = value
    existing.masked = is_masked
    project_delete.variables.get.return_value = existing

    cicd_variables.delete_variable(
        project=project_delete,
        variable=variable,
        is_force=False
    )
    project_delete.variables.get.assert_called_with(key)
    project_delete.variables.delete.assert_called_once_with(key)


@pytest.mark.unit
def test_get_cicd_variables_uses_iterator_and_fetches_all():
    """ get_cicd_variables must use iterator=True to paginate through ALL variables """
    project = Mock()

    # Create 25 mock variables (more than one page of 20)
    mock_vars = []
    for i in range(25):
        v = Mock()
        v.key = f"var_{i}"
        v.value = f"value_{i}"
        v.environment_scope = "*"
        v.masked = False
        mock_vars.append(v)

    project.variables.list.return_value = iter(mock_vars)

    result = cicd_variables.get_cicd_variables(project)

    # Verify list was called with iterator=True (pagination through all pages)
    project.variables.list.assert_called_once_with(iterator=True)

    # Verify all 25 variables were collected (not just 20 from first page)
    assert len(result) == 25
    for i in range(25):
        assert f"var_{i}" in result
        assert result[f"var_{i}"]["value"] == f"value_{i}"
        assert result[f"var_{i}"]["env"] == "*"
        assert result[f"var_{i}"]["masked"] is False


@pytest.mark.unit
def test_capture_existing_cicd_uses_iterator():
    """ capture_existing_cicd must use iterator=True to capture all variables """
    project = Mock()

    mock_vars = []
    for i in range(30):
        v = Mock()
        v.key = f"var_{i}"
        v.value = f"value_{i}"
        v.masked = False
        mock_vars.append(v)

    project.variables.list.return_value = iter(mock_vars)

    result = cicd_utils.capture_existing_cicd(project)

    project.variables.list.assert_called_once_with(iterator=True)
    assert len(result) == 30
    for i in range(30):
        assert result[f"var_{i}"]["value"] == f"value_{i}"


@pytest.mark.unit
def test_create_variable_uses_get_not_list_when_variable_missing():
    """ create_variable should use variables.get() (targeted) not variables.list() """
    project = Mock()

    # variables.get raises GitlabGetError -> variable doesn't exist
    project.variables.get.side_effect = GitlabGetError("not found")

    mock_created = Mock()
    mock_created.key = "new_var"
    mock_created.value = "new_value"
    mock_created.environment_scope = "*"
    mock_created.masked = False
    project.variables.create.return_value = mock_created

    variable = cicd_variables.CICDVariable(
        name="new_var", value="new_value", env="*", masked=False
    )

    cicd_variables.create_variable(project, variable, is_force=False)

    # Should use get() with the variable name, not list()
    project.variables.get.assert_called_once_with("new_var")
    project.variables.list.assert_not_called()
    project.variables.create.assert_called_once()


@pytest.mark.unit
def test_create_variable_uses_get_not_list_when_variable_exists():
    """ create_variable should use variables.get() to check existing variable """
    project = Mock()

    existing = Mock()
    existing.key = "existing_var"
    existing.value = "same_value"
    existing.environment_scope = "*"
    existing.masked = False
    project.variables.get.return_value = existing

    variable = cicd_variables.CICDVariable(
        name="existing_var", value="same_value", env="*", masked=False
    )

    cicd_variables.create_variable(project, variable, is_force=False)

    project.variables.get.assert_called_once_with("existing_var")
    project.variables.list.assert_not_called()
    project.variables.create.assert_not_called()


@pytest.mark.unit
def test_delete_variable_uses_get_not_list():
    """ delete_variable should use variables.get() (targeted) not variables.list() """
    project = Mock()

    existing = Mock()
    existing.key = "del_var"
    existing.value = "same_value"
    existing.masked = False
    project.variables.get.return_value = existing

    variable = cicd_variables.CICDVariable(
        name="del_var", value="same_value", env="*", masked=False
    )

    cicd_variables.delete_variable(project, variable, is_force=False)

    project.variables.get.assert_called_once_with("del_var")
    project.variables.list.assert_not_called()
    project.variables.delete.assert_called_once_with("del_var")


@pytest.mark.unit
def test_delete_variable_uses_get_when_variable_missing():
    """ delete_variable should use variables.get() and handle missing variable """
    project = Mock()

    project.variables.get.side_effect = GitlabGetError("not found")

    variable = cicd_variables.CICDVariable(
        name="missing_var", value="val", env="*", masked=False
    )

    cicd_variables.delete_variable(project, variable, is_force=False)

    project.variables.get.assert_called_once_with("missing_var")
    project.variables.list.assert_not_called()
    project.variables.delete.assert_not_called()


@pytest.mark.unit
def test_restore_existing_cicd_uses_get_per_variable():
    """ restore_existing_cicd should use variables.get() per variable name, not list() """
    project = Mock()

    var_obj = Mock()
    var_obj.masked = False
    project.variables.get.return_value = var_obj

    existing_cicd = {
        "restore_var": {"value": "orig_value", "masked": False}
    }

    cicd_utils.restore_existing_cicd(project, existing_cicd)

    project.variables.get.assert_called_once_with("restore_var")
    project.variables.list.assert_not_called()
    var_obj.save.assert_called_once()
