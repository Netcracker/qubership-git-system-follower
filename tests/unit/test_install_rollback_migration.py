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

"""Tests for gear type migration during a version rollback.

A rollback (state version > new package version) that also changes the gear
structure type (simple <-> complex) must behave symmetrically with the upgrade
path: it should require --force on mismatch and, when --force is supplied,
persist the new gear's structure_type instead of the stale old one.
"""

from pathlib import Path
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from git_system_follower.install import install_package
from git_system_follower.states import PackageState


GEARS_DIR = Path(__file__).parent.parent / "gears"


def _make_state(structure_type: str, version: str) -> PackageState:
    return PackageState(
        name="migrate",
        version=version,
        used_template="default",
        template_variables={},
        last_update=str(datetime.now()),
        structure_type=structure_type,
        dependencies=[],
        cicd_variables=[],
    )


def _make_package(version: str) -> dict:
    # Complex gear: scripts/0.0.1 exists so get_gear_info resolves 'complex'
    return {
        "apiVersion": "v1",
        "type": 1,
        "name": "migrate",
        "version": version,
        "dependencies": (),
        "path": GEARS_DIR / "complex",
    }


def _make_old_package(version: str) -> dict:
    return {
        "apiVersion": "v1",
        "type": 1,
        "name": "migrate",
        "version": version,
        "dependencies": (),
        "path": GEARS_DIR / "complex",
    }


_COMMON_KWARGS = {
    "created_cicd_variables": (),
    "created_webhooks": (),
    "extras": (),
    "is_skip_force_rollback": True,
    "is_autoheal": False,
}


@pytest.mark.unit
def test_rollback_migration_requires_force_without_force():
    """Rollback + gear type migration without --force must abort (SystemExit)."""
    # State tracked a SIMPLE gear at a higher version; new package is COMPLEX at lower version.
    state = _make_state(structure_type="simple", version="0.0.2")
    package = _make_package(version="0.0.1")
    old_package = _make_old_package(version="0.0.2")

    with patch("git_system_follower.install.rollback") as mock_rollback:
        mock_rollback.return_value = {
            "template": "default",
            "template_variables": {},
            "cicd_variables": [],
            "webhooks": [],
        }
        with pytest.raises(SystemExit):
            install_package(package, (old_package,), SimpleNamespace(), state, is_force=False, **_COMMON_KWARGS)
        mock_rollback.assert_not_called()


@pytest.mark.unit
def test_rollback_migration_with_force_updates_structure_type():
    """Rollback + gear type migration with --force proceeds and updates state structure_type."""
    state = _make_state(structure_type="simple", version="0.0.2")
    package = _make_package(version="0.0.1")
    old_package = _make_old_package(version="0.0.2")

    with patch("git_system_follower.install.rollback") as mock_rollback:
        mock_rollback.return_value = {
            "template": "default",
            "template_variables": {},
            "cicd_variables": [],
            "webhooks": [],
        }
        install_package(package, (old_package,), SimpleNamespace(), state, is_force=True, **_COMMON_KWARGS)
        mock_rollback.assert_called_once()
        assert state["structure_type"] == "complex"


@pytest.mark.unit
def test_rollback_same_gear_type_no_force_prompt():
    """Rollback without gear type migration must NOT require --force."""
    state = _make_state(structure_type="complex", version="0.0.2")
    package = _make_package(version="0.0.1")
    old_package = _make_old_package(version="0.0.2")

    with patch("git_system_follower.install.rollback") as mock_rollback:
        mock_rollback.return_value = {
            "template": "default",
            "template_variables": {},
            "cicd_variables": [],
            "webhooks": [],
        }
        install_package(package, (old_package,), SimpleNamespace(), state, is_force=False, **_COMMON_KWARGS)
        mock_rollback.assert_called_once()
        assert state["structure_type"] == "complex"
