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

import copy
import yaml
import pytest
from pathlib import Path
from unittest.mock import Mock
from git_system_follower.package.package_info import (
    get_package_info, _validate_package_info
)
from git_system_follower.errors import DescriptionSectionError
from git_system_follower.variables import PACKAGE_DESCRIPTION_FILE_API, PACKAGE_DIRNAME
from git_system_follower.develop.api.v2.types import ProjectMetadata, GraphQLClient
from git_system_follower.package.project_metadata import initialize_metadata, sync_icon

GEARS_DIR = Path(__file__).parent.parent / "gears"
GEARS_V1 = ("simple", "complex")
GEARS_V2 = ("simplev2", "complexv2")


@pytest.fixture(autouse=True)
def _reset_metadata_singletons():
    """ Reset the process-wide ProjectMetadata/GraphQLClient singletons before
    and after each test so metadata state doesn't leak between tests. """
    ProjectMetadata()._data = None
    GraphQLClient()._data = None
    yield
    ProjectMetadata()._data = None
    GraphQLClient()._data = None


def _write_package_yaml(tmp_path: Path, data: dict) -> Path:
    """ Build a git-system-follower-package/package.yaml under tmp_path and
    return the gear root dir (what get_package_info expects as `directory`) """
    package_dir = tmp_path / PACKAGE_DIRNAME
    package_dir.mkdir(parents=True, exist_ok=True)
    with open(package_dir / "package.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f)
    return tmp_path


def _valid_v2_payload(**overrides) -> dict:
    base = {
        "apiVersion": "v2",
        "type": "gitlab-ci-pipeline",
        "name": "test-gear",
        "version": "1.0.0",
        "description": "A test gear for v2 schema validation",
        "icon": "icon.png",
    }
    base.update(overrides)
    return base

@pytest.mark.unit
@pytest.mark.parametrize("gear_folder", GEARS_V2)
def test_v2_gear_fixtures_load_successfully(gear_folder):
    path = GEARS_DIR / gear_folder
    result = get_package_info(path, name=gear_folder)
    assert result["description"], "description should be present and non-empty for v2 gears"
    assert result["icon"], "icon should be present and non-empty for v2 gears"


@pytest.mark.unit
@pytest.mark.parametrize("gear_folder", GEARS_V1)
def test_v1_gear_fixtures_unaffected_by_v2_changes(gear_folder):
    """ Regression: existing v1 fixtures must keep working without description/icon """
    path = GEARS_DIR / gear_folder
    result = get_package_info(path, name=gear_folder)
    assert result["apiVersion"] == "v1"
    assert "description" not in result or result.get("description") is None


# ---------------------------------------------------------------------------
# Schema-level tests: exercise _validate_package_info() directly against
# constructed dicts, so failure cases don't need on-disk fixtures per case
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_v2_minimal_payload_is_valid():
    data = _valid_v2_payload()
    result = _validate_package_info(copy.deepcopy(data))
    assert result["description"] == data["description"]
    assert result["icon"] == data["icon"]
    assert "subtype" not in result or result.get("subtype") is None


@pytest.mark.unit
def test_v2_with_optional_subtype_component_is_valid():
    data = _valid_v2_payload(subtype="component")
    result = _validate_package_info(copy.deepcopy(data))
    assert result["subtype"] == "component"


@pytest.mark.unit
@pytest.mark.parametrize("missing_key", ["description", "icon"])
def test_v2_without_description_or_icon_is_valid(missing_key):
    """ description/icon are optional for v2 gears, so omitting either must
    validate successfully and simply leave the key out of the result """
    data = _valid_v2_payload()
    del data[missing_key]
    result = _validate_package_info(copy.deepcopy(data))
    assert missing_key not in result


@pytest.mark.unit
@pytest.mark.parametrize("missing_key", ["description", "icon"])
def test_get_package_info_succeeds_without_description_or_icon(tmp_path, missing_key):
    """ get_package_info() must not exit when a v2 gear omits description/icon """
    data = _valid_v2_payload()
    del data[missing_key]
    gear_dir = _write_package_yaml(tmp_path, data)
    result = get_package_info(gear_dir, name="test-gear")
    assert missing_key not in result


@pytest.mark.unit
@pytest.mark.parametrize("empty_value", ["", None])
@pytest.mark.parametrize("key", ["description", "icon"])
def test_v2_empty_or_null_mandatory_value(key, empty_value):
    """ Key present but empty/null. _validate_section_types() is currently a
    no-op TODO, so this documents today's (permissive) behavior rather than
    asserting a non-empty-string rule that doesn't exist yet -- flag before
    treating a passing test here as "correct". """
    data = _valid_v2_payload(**{key: empty_value})
    result = _validate_package_info(copy.deepcopy(data))
    assert result[key] == empty_value


@pytest.mark.unit
def test_v2_unknown_extra_section_rejected():
    data = _valid_v2_payload(unknown_field="oops")
    with pytest.raises(DescriptionSectionError, match="extra section"):
        _validate_package_info(data)


@pytest.mark.unit
@pytest.mark.parametrize("subtype", ["not-a-real-subtype", "comp", "componentX", "com"])
def test_v2_invalid_subtype_value(subtype):
    """ subtype is value-restricted to the registered package_subtypes. The
    substring entries ('comp', 'componentX', 'com') would wrongly pass if
    package_subtypes were a plain string and `in` matched as a substring. """
    data = _valid_v2_payload(subtype=subtype)
    with pytest.raises(DescriptionSectionError):
        _validate_package_info(data)


@pytest.mark.unit
def test_v1_payload_rejects_v2_only_sections():
    """ Regression: v1 schema shouldn't silently accept description/icon/subtype
    just because v2 added them -- they aren't in v1's mandatory/optional_sections,
    so _validate_section_names should still reject them as unknown extras. """
    data = {
        "apiVersion": "v1",
        "type": "gitlab-ci-pipeline",
        "name": "test-gear",
        "version": "1.0.0",
        "description": "should not be allowed under v1",
    }
    with pytest.raises(DescriptionSectionError, match="extra section"):
        _validate_package_info(data)


@pytest.mark.unit
def test_unsupported_api_version_lists_v1_and_v2():
    data = _valid_v2_payload(apiVersion="v3")
    with pytest.raises(DescriptionSectionError) as exc_info:
        _validate_package_info(data)
    assert "v1" in str(exc_info.value)
    assert "v2" in str(exc_info.value)


@pytest.mark.unit
def test_v2_registered_in_package_description_file_api():
    """ Guard-rail: catches accidentally leaving v2 out of variables.py """
    assert "v2" in PACKAGE_DESCRIPTION_FILE_API
    v2_info = PACKAGE_DESCRIPTION_FILE_API["v2"]
    assert "description" in v2_info["optional_sections"]
    assert "icon" in v2_info["optional_sections"]
    assert "subtype" in v2_info["optional_sections"]


@pytest.mark.unit
def test_v2_dependencies_still_optional():
    data = _valid_v2_payload()
    result = _validate_package_info(copy.deepcopy(data))
    assert result["dependencies"] == ()


@pytest.mark.unit
def test_validation_does_not_initialize_project_metadata():
    """ Validation is pure: parsing a v2 payload with description/icon must NOT
    touch the process-wide ProjectMetadata/GraphQLClient singletons. They are
    initialized later, per-package, right before a package's scripts run. """
    data = _valid_v2_payload()
    _validate_package_info(copy.deepcopy(data))
    assert ProjectMetadata()._data is None
    assert GraphQLClient()._data is None


@pytest.mark.unit
@pytest.mark.parametrize("missing_key", ["description", "icon"])
def test_validation_ok_when_metadata_key_missing(missing_key):
    """ description/icon are optional, so omitting one validates fine and the
    result carries no metadata key """
    data = _valid_v2_payload()
    del data[missing_key]
    result = _validate_package_info(copy.deepcopy(data))
    assert missing_key not in result


@pytest.mark.unit
def test_v1_payload_with_both_metadata_keys_rejected_as_extra_section():
    """ A v1 package.yaml that carries description/icon should be rejected as an
    extra-section error (v1 has no project metadata). """
    data = {
        "apiVersion": "v1",
        "type": "gitlab-ci-pipeline",
        "name": "test-gear",
        "version": "1.0.0",
        "description": "present but not allowed under v1",
        "icon": "icon.png",
    }
    with pytest.raises(DescriptionSectionError, match="extra section"):
        _validate_package_info(data)


def _fake_repo():
    repo = Mock()
    repo.gitlab.manager.gitlab.url = "https://gitlab.example.com/path"
    repo.token = "secret-token"
    return repo


@pytest.mark.unit
def test_initialize_metadata_sets_project_metadata():
    package = _valid_v2_payload()
    initialize_metadata(package, _fake_repo())
    ctx = ProjectMetadata()
    assert ctx.description == package["description"]
    assert ctx.icon == package["icon"]


@pytest.mark.unit
def test_initialize_metadata_re_initializable_for_different_package():
    """ A single process runs scripts for several packages (e.g. delete old +
    init new during a rollback); each call must refresh the singleton, not raise. """
    initialize_metadata(_valid_v2_payload(), _fake_repo())
    other = _valid_v2_payload(description="other", icon="other.png")
    initialize_metadata(other, _fake_repo())
    ctx = ProjectMetadata()
    assert ctx.description == "other"
    assert ctx.icon == "other.png"


@pytest.mark.unit
@pytest.mark.parametrize("missing_key", ["description", "icon"])
def test_initialize_metadata_noop_when_key_missing(missing_key):
    package = _valid_v2_payload()
    del package[missing_key]
    initialize_metadata(package, _fake_repo())
    assert ProjectMetadata()._data is None


# ---------------------------------------------------------------------------
# Icon synchronization: no icon declared must not touch an existing avatar
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_sync_icon_no_icon_declared_leaves_existing_avatar_untouched(tmp_path):
    """ Regression: a gear without an `icon` must NOT remove an avatar that
    already exists on the project (it may belong to another package, be set
    externally, or be left over from a previous gear version). """
    project = Mock()
    project.attributes = {"avatar_url": "https://gitlab.example.com/uploads/avatar.png"}
    ctx = ProjectMetadata()
    ctx.initialize(description="desc", icon=None)  # no icon declared

    result = sync_icon(project, ctx, tmp_path)

    assert result is False
    project.save.assert_not_called()
    assert project.avatar != ""


@pytest.mark.unit
def test_sync_icon_icon_declared_sets_avatar(tmp_path):
    """ A gear that declares an `icon` still syncs it to the project avatar. """
    icon_file = tmp_path / "icon.png"
    icon_file.write_bytes(b"fake-png-bytes")
    project = Mock()
    project.attributes = {"avatar_url": None}
    ctx = ProjectMetadata()
    ctx.initialize(description="desc", icon="icon.png")

    result = sync_icon(project, ctx, tmp_path)

    assert result is True
    assert project.avatar == b"fake-png-bytes"
