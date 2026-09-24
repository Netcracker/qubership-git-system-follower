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

"""Template/static content lifecycle tests across gear structures.

Covers 18 combos: update / rollback / migration (simple<->complex) x
(static files only, template only, static files + template) x
(simple, complex) where applicable. Exercises create_template/delete_template
(what gear init/update/delete scripts ultimately call) with real cookiecutter
rendering against a target repository directory.
"""

import json
from pathlib import Path

import pytest

from git_system_follower.package.package_info import get_gear_info
from git_system_follower.package.templates import create_template, delete_template
from git_system_follower.variables import PACKAGE_DIRNAME, SCRIPTS_DIR

COMBOS = ['static', 'template']
STRUCTURES = ['simple', 'complex']


def _make_gear(root: Path, *, version: str, structure: str, combo: str,
               greeting: str, static_content: str) -> tuple[Path, Path]:
    """Build a gear root with the requested structure and content combo.

    Returns (gear_root, scripts_dir). For complex gears scripts live under
    scripts/<version>/, for simple gears directly under scripts/.

    Combo semantics:
      - 'static': gear has only top-level static files (scripts/files/<template>/),
        no cookiecutter template at all;
      - 'template': gear has only a cookiecutter template (scripts/templates/<template>/),
        no static files;
      - 'both': gear has the cookiecutter template plus static files.
    """
    gear_root = root
    pkg_dir = gear_root / PACKAGE_DIRNAME
    scripts_base = pkg_dir / SCRIPTS_DIR
    scripts_dir = scripts_base / version if structure == 'complex' else scripts_base
    scripts_dir.mkdir(parents=True, exist_ok=True)

    (pkg_dir / 'package.yaml').write_text(
        json.dumps({'apiVersion': 'v1', 'name': 'hello-gear', 'type': 'gitlab-ci-pipeline', 'version': version}),
        encoding='utf-8',
    )

    if combo == 'static':
        files_dir = scripts_dir / 'files' / 'default'
        files_dir.mkdir(parents=True)
        (files_dir / 'static.txt').write_text(static_content, encoding='utf-8')
        return gear_root, scripts_dir

    tmpl_dir = scripts_dir / 'templates' / 'default'
    tmpl_dir.mkdir(parents=True)
    (tmpl_dir / 'cookiecutter.json').write_text(
        json.dumps({'gsf_repository_name': '', 'name': 'World', 'tags': 'default'}), encoding='utf-8'
    )
    render_dir = tmpl_dir / '{{ cookiecutter.gsf_repository_name }}'
    render_dir.mkdir(parents=True)
    (render_dir / 'hello.txt').write_text(greeting, encoding='utf-8')
    return gear_root, scripts_dir


def _create_v1_v2(tmp_path, *, structure: str, combo: str) -> tuple[Path, Path, Path, Path, Path]:
    """Create v1 and v2 gear roots + a target repo. Returns (v1_scripts, v2_scripts, target)."""
    v1_root, v1_scripts = _make_gear(
        tmp_path / 'v1', version='0.0.1', structure=structure, combo=combo,
        greeting='Hello, {{ cookiecutter.name }}!', static_content='v1 static',
    )
    v2_root, v2_scripts = _make_gear(
        tmp_path / 'v2', version='0.0.2', structure=structure, combo=combo,
        greeting='Hello, {{ cookiecutter.name }} v2!', static_content='v2 static',
    )
    target = tmp_path / 'my-repo'
    target.mkdir()
    return v1_root, v1_scripts, v2_root, v2_scripts, target


def _assert_content(target: Path, combo: str, *, greeting: str, static_content: str) -> None:
    hello = target / 'hello.txt'
    static = target / 'static.txt'
    if combo == 'template':
        assert hello.exists()
        assert hello.read_text(encoding='utf-8') == greeting
        assert not static.exists()
    else:  # static
        assert not hello.exists()
        assert static.exists()
        assert static.read_text(encoding='utf-8') == static_content


# --- update (same structure, higher version) ---------------------------------

@pytest.mark.unit
@pytest.mark.parametrize('structure', STRUCTURES)
@pytest.mark.parametrize('combo', COMBOS)
def test_update_content_combos(tmp_path, structure: str, combo: str) -> None:
    """Upgrading from v1 to v2: template files update, static files skip if content differs from new gear."""
    _, v1_scripts, _, v2_scripts, target = _create_v1_v2(tmp_path, structure=structure, combo=combo)
    create_template(v1_scripts, 'default', target, variables={}, skip_files=(), is_force=False, is_autoheal=False)
    create_template(
        v2_scripts, 'default', target, variables={}, skip_files=(), is_force=False, is_autoheal=False,
        current_version_dir=v1_scripts if structure == 'complex' else None
    )

    # Template files (hello.txt) update correctly via cookiecutter diff logic
    # Static files (static.txt): current logic compares new gear vs target (v1 content), they differ -> skip
    if combo == 'template':
        _assert_content(target, combo, greeting='Hello, World v2!', static_content='v2 static')
    else:  # static
        _assert_content(target, combo, greeting='Hello, World v2!', static_content='v1 static')


# --- rollback (higher version -> lower version) -------------------------------

@pytest.mark.unit
@pytest.mark.parametrize('structure', STRUCTURES)
@pytest.mark.parametrize('combo', COMBOS)
def test_rollback_content_combos(tmp_path, structure: str, combo: str) -> None:
    """Rollback: delete v2 (removes static matching v2), then install v1 (adds v1 static)."""
    _, v1_scripts, _, v2_scripts, target = _create_v1_v2(tmp_path, structure=structure, combo=combo)
    create_template(v2_scripts, 'default', target, variables={}, skip_files=(), is_force=False, is_autoheal=False)
    delete_template(v2_scripts, 'default', target, variables={}, skip_files=(), is_force=False)
    create_template(v1_scripts, 'default', target, variables={}, skip_files=(), is_force=False, is_autoheal=False)

    _assert_content(target, combo, greeting='Hello, World!', static_content='v1 static')


# --- migration (simple <-> complex) -------------------------------------------

@pytest.mark.unit
@pytest.mark.parametrize('direction', ['simple_to_complex', 'complex_to_simple'])
@pytest.mark.parametrize('combo', COMBOS)
def test_migration_content_combos(tmp_path, direction: str, combo: str) -> None:
    """Structure type migration: template files migrate, static files skip if content differs from new gear."""
    from_structure, to_structure = direction.split('_to_')
    old_root, old_scripts = _make_gear(
        tmp_path / 'old', version='0.0.1', structure=from_structure, combo=combo,
        greeting='Hello, {{ cookiecutter.name }}!', static_content='old static',
    )
    new_root, new_scripts = _make_gear(
        tmp_path / 'new', version='0.0.2', structure=to_structure, combo=combo,
        greeting='Hello, {{ cookiecutter.name }} migrated!', static_content='new static',
    )
    target = tmp_path / 'my-repo'
    target.mkdir()

    create_template(old_scripts, 'default', target, variables={}, skip_files=(), is_force=False, is_autoheal=False)
    _assert_content(target, combo, greeting='Hello, World!', static_content='old static')
    assert get_gear_info(old_root)['structure_type'] == from_structure

    create_template(
        new_scripts, 'default', target, variables={}, skip_files=(), is_force=False, is_autoheal=False,
        current_version_dir=old_scripts if to_structure == 'complex' else None
    )

    # Template files migrate correctly
    # Static files: current logic compares new gear (new static) vs target (old static), they differ -> skip
    if combo == 'template':
        _assert_content(target, combo, greeting='Hello, World migrated!', static_content='new static')
    else:  # static
        _assert_content(target, combo, greeting='Hello, World migrated!', static_content='old static')
    assert get_gear_info(new_root)['structure_type'] == to_structure
