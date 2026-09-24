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

"""Tests for the static 'files/' directory support in package/templates.py."""

import pytest

from git_system_follower.errors import PackageApiError
from git_system_follower.package.templates import (
    _copy_static_files, _delete_static_files,
    create_template, delete_template,
)


@pytest.mark.unit
def test_copy_static_files_copies_verbatim(tmp_path):
    files_dir = tmp_path / 'files'
    (files_dir / 'nested').mkdir(parents=True)
    (files_dir / 'top.txt').write_text('top content')
    (files_dir / 'nested' / 'inner.txt').write_text('inner content')

    target = tmp_path / 'target'
    target.mkdir()

    _copy_static_files(files_dir, target)

    assert (target / 'top.txt').read_text() == 'top content'
    assert (target / 'nested' / 'inner.txt').read_text() == 'inner content'


@pytest.mark.unit
def test_copy_static_files_fresh_install_skips_different_content(tmp_path):
    """
    On a fresh install (no prev_files_dir), if target exists with different content, skip (treated as user changes).
    """
    files_dir = tmp_path / 'files'
    files_dir.mkdir()
    (files_dir / 'static.txt').write_text('new content')

    target = tmp_path / 'target'
    target.mkdir()
    (target / 'static.txt').write_text('pre-existing content')

    _copy_static_files(files_dir, target)

    assert (target / 'static.txt').read_text() == 'pre-existing content'


@pytest.mark.unit
def test_copy_static_files_update_overwrites_only_if_target_matches_new_gear(tmp_path):
    """On update, only overwrites if target content already matches new gear content (not previous version)."""
    prev_files_dir = tmp_path / 'prev_files'
    prev_files_dir.mkdir()
    (prev_files_dir / 'static.txt').write_text('old gear content')

    files_dir = tmp_path / 'files'
    files_dir.mkdir()
    (files_dir / 'static.txt').write_text('new gear content')

    target = tmp_path / 'target'
    target.mkdir()
    (target / 'static.txt').write_text('old gear content')  # matches prev, but NOT new gear

    _copy_static_files(files_dir, target)

    # Current logic: compares new gear vs target, they differ -> skip
    assert (target / 'static.txt').read_text() == 'old gear content'


@pytest.mark.unit
def test_copy_static_files_update_skips_when_target_differs_from_new_gear(tmp_path):
    """On update, skips when target content differs from new gear (regardless of previous version)."""
    prev_files_dir = tmp_path / 'prev_files'
    prev_files_dir.mkdir()
    (prev_files_dir / 'static.txt').write_text('old gear content')

    files_dir = tmp_path / 'files'
    files_dir.mkdir()
    (files_dir / 'static.txt').write_text('new gear content')

    target = tmp_path / 'target'
    target.mkdir()
    (target / 'static.txt').write_text('user-modified content')  # differs from both prev and new

    _copy_static_files(files_dir, target)

    # Current logic: compares new gear vs target, they differ -> skip
    assert (target / 'static.txt').read_text() == 'user-modified content'


@pytest.mark.unit
def test_delete_static_files_no_user_changes_deletes(tmp_path):
    """On uninstall, if the target matches the gear file, delete it."""
    files_dir = tmp_path / 'files'
    files_dir.mkdir()
    (files_dir / 'static.txt').write_text('gear content')

    target = tmp_path / 'target'
    target.mkdir()
    (target / 'static.txt').write_text('gear content')  # no user changes

    _delete_static_files(files_dir, target)

    assert not (target / 'static.txt').exists()


@pytest.mark.unit
def test_delete_static_files_user_changes_skipped(tmp_path):
    """On uninstall, if the target was modified by the user, skip with a warning."""
    files_dir = tmp_path / 'files'
    files_dir.mkdir()
    (files_dir / 'static.txt').write_text('gear content')

    target = tmp_path / 'target'
    target.mkdir()
    (target / 'static.txt').write_text('user-modified content')

    _delete_static_files(files_dir, target)

    assert (target / 'static.txt').exists()


@pytest.mark.unit
def test_delete_static_files_skips_missing_target(tmp_path):
    files_dir = tmp_path / 'files'
    files_dir.mkdir()
    (files_dir / 'static.txt').write_text('template content')

    target = tmp_path / 'target'
    target.mkdir()

    _delete_static_files(files_dir, target)  # should not raise

    assert not (target / 'static.txt').exists()


# --- create_template / delete_template routing ---

@pytest.mark.unit
def test_create_template_top_level_files_only(tmp_path):
    """files/<template>/ alone (no templates/<template>/) still copies static files."""
    script_dir = tmp_path / 'scripts'
    files_dir = script_dir / 'files' / 'onsite'
    files_dir.mkdir(parents=True)
    (files_dir / 'config.yaml').write_text('env: onsite')

    target = tmp_path / 'my-repo'
    target.mkdir()

    create_template(script_dir, 'onsite', target, variables={}, skip_files=(), is_force=False, is_autoheal=False)

    assert (target / 'config.yaml').read_text() == 'env: onsite'


@pytest.mark.unit
def test_create_template_neither_raises(tmp_path):
    """Neither templates/<template>/ nor files/<template>/ → PackageApiError."""
    script_dir = tmp_path / 'scripts'
    script_dir.mkdir()
    target = tmp_path / 'my-repo'
    target.mkdir()

    with pytest.raises(PackageApiError):
        create_template(script_dir, 'onsite', target, variables={}, skip_files=(), is_force=False, is_autoheal=False)



@pytest.mark.unit
def test_delete_template_top_level_files_only(tmp_path):
    """files/<template>/ alone (no templates/<template>/) still deletes static files."""
    script_dir = tmp_path / 'scripts'
    files_dir = script_dir / 'files' / 'onsite'
    files_dir.mkdir(parents=True)
    (files_dir / 'config.yaml').write_text('env: onsite')

    target = tmp_path / 'my-repo'
    target.mkdir()
    (target / 'config.yaml').write_text('env: onsite')

    delete_template(script_dir, 'onsite', target, variables={}, skip_files=(), is_force=False)

    assert not (target / 'config.yaml').exists()


@pytest.mark.unit
def test_delete_template_neither_raises(tmp_path):
    """Neither templates/<template>/ nor files/<template>/ → PackageApiError."""
    script_dir = tmp_path / 'scripts'
    script_dir.mkdir()
    target = tmp_path / 'my-repo'
    target.mkdir()

    with pytest.raises(PackageApiError):
        delete_template(script_dir, 'onsite', target, variables={}, skip_files=(), is_force=False)


# --- get_template_names ---

@pytest.mark.unit
def test_get_template_names_templates_only(tmp_path):
    """get_template_names finds templates in templates/ directory."""
    script_dir = tmp_path / 'scripts'
    (script_dir / 'templates' / 't1').mkdir(parents=True)
    (script_dir / 'templates' / 't2').mkdir(parents=True)

    from git_system_follower.package.templates import get_template_names
    names = get_template_names(script_dir)

    assert names == ('t1', 't2')


@pytest.mark.unit
def test_get_template_names_files_only(tmp_path):
    """get_template_names finds templates in files/ directory (no templates/ dir)."""
    script_dir = tmp_path / 'scripts'
    (script_dir / 'files' / 'static1').mkdir(parents=True)
    (script_dir / 'files' / 'static2').mkdir(parents=True)

    from git_system_follower.package.templates import get_template_names
    names = get_template_names(script_dir)

    assert names == ('static1', 'static2')


@pytest.mark.unit
def test_get_template_names_both_dirs(tmp_path):
    """get_template_names merges templates from both templates/ and files/."""
    script_dir = tmp_path / 'scripts'
    (script_dir / 'templates' / 'tmpl').mkdir(parents=True)
    (script_dir / 'files' / 'static').mkdir(parents=True)

    from git_system_follower.package.templates import get_template_names
    names = get_template_names(script_dir)

    assert names == ('static', 'tmpl')


@pytest.mark.unit
def test_get_template_names_no_dirs_raises(tmp_path):
    """get_template_names raises if neither templates/ nor files/ exists."""
    script_dir = tmp_path / 'scripts'
    script_dir.mkdir()

    from git_system_follower.package.templates import get_template_names
    with pytest.raises(PackageApiError):
        get_template_names(script_dir)
