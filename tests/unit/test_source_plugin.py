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

"""Tests for SourcePlugin resolving relative directory gear paths (e.g. ".")."""


import pytest

from git_system_follower.plugins.cli.packages.default import SourcePlugin
from git_system_follower.utils.utility import normalized_in_string_match


@pytest.mark.unit
def test_dot_is_resolved_to_absolute_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plugin = SourcePlugin()

    matched = plugin.process('.')

    assert matched is True
    assert plugin.value == str(tmp_path.resolve())
    assert plugin.gears[0].path == tmp_path.resolve()


@pytest.mark.unit
def test_dot_no_longer_normalizes_to_an_empty_match(tmp_path, monkeypatch):
    """The bug: normalized_in_string_match("anything", ".") is always False,
    so a gear installed via "." could never be matched again for rollback."""
    gear_dir = tmp_path / 'my-gear'
    gear_dir.mkdir()
    monkeypatch.chdir(gear_dir)
    plugin = SourcePlugin()

    plugin.process('.')

    assert normalized_in_string_match('my-gear', plugin.value) is True


@pytest.mark.unit
def test_relative_subdirectory_is_also_resolved(tmp_path, monkeypatch):
    (tmp_path / 'gear').mkdir()
    monkeypatch.chdir(tmp_path)
    plugin = SourcePlugin()

    plugin.process('./gear')

    assert plugin.value == str((tmp_path / 'gear').resolve())


@pytest.mark.unit
def test_non_directory_value_is_left_untouched():
    plugin = SourcePlugin()

    matched = plugin.process('registry.example.com/repo/image:tag')

    assert matched is False
    assert plugin.value is None
