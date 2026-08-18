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
from git_system_follower.package.permissions import (
    AccessLevel, Requirements, access_level_name, check_token_permissions,
    detect_package_requirements, get_effective_access_level,
    get_registered_requirements, register_requirement, reset_registered_requirements
)


@pytest.fixture(autouse=True)
def _reset_registered_requirements():
    """ Registered requirements are process-wide; reset them before and after
    each test so registration doesn't leak between tests. """
    reset_registered_requirements()
    yield
    reset_registered_requirements()


# ---------------------------------------------------------------------------
# Requirements aggregation
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_requirements_none_means_developer():
    assert Requirements().required_access() == AccessLevel.DEVELOPER


@pytest.mark.unit
@pytest.mark.parametrize("kwarg", ["needs_cicd_variables", "needs_webhooks"])
def test_requirements_cicd_or_webhooks_mean_maintainer(kwarg):
    assert Requirements(**{kwarg: True}).required_access() == AccessLevel.MAINTAINER


@pytest.mark.unit
def test_requirements_metadata_wins_over_maintainer():
    req = Requirements(needs_cicd_variables=True, needs_webhooks=True, needs_metadata_sync=True)
    assert req.required_access() == AccessLevel.OWNER


@pytest.mark.unit
def test_requirements_reasons():
    req = Requirements(needs_cicd_variables=True, needs_metadata_sync=True)
    reasons = req.reasons
    assert len(reasons) == 2
    assert any('metadata' in reason for reason in reasons)
    assert any('variables' in reason for reason in reasons)


# ---------------------------------------------------------------------------
# Static detection from package description file
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_detect_description_requires_owner():
    req = detect_package_requirements({"apiVersion": "v2", "description": "desc", "icon": "icon.png"})
    assert req.needs_metadata_sync is True
    assert req.required_access() == AccessLevel.OWNER


@pytest.mark.unit
def test_detect_icon_only_requires_owner():
    req = detect_package_requirements({"apiVersion": "v2", "icon": "icon.png"})
    assert req.required_access() == AccessLevel.OWNER


@pytest.mark.unit
def test_detect_plain_package_requires_developer():
    req = detect_package_requirements({"apiVersion": "v1", "name": "g", "version": "1.0.0"})
    assert req.needs_metadata_sync is False
    assert req.required_access() == AccessLevel.DEVELOPER


# ---------------------------------------------------------------------------
# Runtime registration
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_register_requirement_and_reset():
    register_requirement(AccessLevel.MAINTAINER, "CI/CD variable 'FOO' management")
    req = get_registered_requirements()
    assert req.needs_cicd_variables is True
    assert req.needs_webhooks is True
    reset_registered_requirements()
    assert get_registered_requirements().required_access() == AccessLevel.DEVELOPER


@pytest.mark.unit
def test_register_owner_requirement():
    register_requirement(AccessLevel.OWNER, "project metadata synchronization")
    assert get_registered_requirements().needs_metadata_sync is True


@pytest.mark.unit
def test_access_level_name():
    assert access_level_name(AccessLevel.DEVELOPER) == "Developer"
    assert access_level_name(AccessLevel.MAINTAINER) == "Maintainer"
    assert access_level_name(AccessLevel.OWNER) == "Owner"


# ---------------------------------------------------------------------------
# Effective access level resolution
# ---------------------------------------------------------------------------

def _project(permissions=None, attributes=None, user=None, members_all=None):
    project = Mock()
    attrs = dict(attributes or {})
    if permissions is not None:
        attrs["permissions"] = permissions
    project.attributes = attrs
    project.manager.gitlab.user = user
    if members_all is not None:
        project.members_all = members_all
    return project


@pytest.mark.unit
def test_effective_access_from_project_permissions():
    project = _project(permissions={"project_access": {"access_level": 30}})
    assert get_effective_access_level(project) == AccessLevel.DEVELOPER


@pytest.mark.unit
def test_effective_access_group_beats_project():
    project = _project(permissions={
        "project_access": {"access_level": 30},
        "group_access": {"access_level": 40},
    })
    assert get_effective_access_level(project) == AccessLevel.MAINTAINER


@pytest.mark.unit
def test_effective_access_falls_back_to_members():
    member = Mock(id=7, access_level=40)
    members_all = Mock()
    members_all.get.return_value = member
    project = _project(user=Mock(id=7, is_admin=False), members_all=members_all)
    assert get_effective_access_level(project) == AccessLevel.MAINTAINER


@pytest.mark.unit
def test_effective_access_admin_is_owner():
    project = _project(user=Mock(is_admin=True))
    assert get_effective_access_level(project) == AccessLevel.OWNER


@pytest.mark.unit
def test_effective_access_defaults_to_developer():
    project = _project()
    assert get_effective_access_level(project) == AccessLevel.DEVELOPER


@pytest.mark.unit
def test_effective_access_resolves_via_gl_user_when_permissions_stale():
    member = Mock(id=7, access_level=50)
    members_all = Mock()
    members_all.get.return_value = member
    project = _project(user=Mock(id=7, is_admin=False), members_all=members_all)
    assert get_effective_access_level(project) == AccessLevel.OWNER


@pytest.mark.unit
def test_effective_access_defaults_to_developer_when_not_a_member():
    members_all = Mock()
    members_all.get.side_effect = Exception("not a member")
    project = _project(user=Mock(id=7, is_admin=False), members_all=members_all)
    assert get_effective_access_level(project) == AccessLevel.DEVELOPER


# ---------------------------------------------------------------------------
# Token permission check
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_check_token_permissions_passes_for_sufficient_token():
    project = _project(permissions={"project_access": {"access_level": 50}})
    check_token_permissions(project, Requirements(needs_metadata_sync=True))


@pytest.mark.unit
def test_check_token_permissions_exits_for_insufficient_token():
    project = _project(permissions={"project_access": {"access_level": 30}})
    project.path_with_namespace = "group/project"
    with pytest.raises(SystemExit):
        check_token_permissions(project, Requirements(needs_cicd_variables=True))


@pytest.mark.unit
def test_check_token_permissions_uses_registered_requirements():
    project = _project(permissions={"project_access": {"access_level": 30}})
    project.path_with_namespace = "group/project"
    register_requirement(AccessLevel.OWNER, "project metadata synchronization")
    with pytest.raises(SystemExit):
        check_token_permissions(project)


@pytest.mark.unit
def test_check_token_permissions_passes_when_nothing_registered():
    project = _project(permissions={"project_access": {"access_level": 30}})
    check_token_permissions(project)
