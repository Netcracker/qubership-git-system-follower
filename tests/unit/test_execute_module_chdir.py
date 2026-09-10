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

"""Tests that execute_module always restores the process cwd, even on failure."""

import os
from unittest.mock import patch

import pytest

from git_system_follower.package.script import execute_module


@pytest.mark.unit
def test_cwd_is_restored_when_wrapped_func_raises(tmp_path):
    original_cwd = os.getcwd()
    workdir = tmp_path / 'workdir'
    workdir.mkdir()
    fake_script = tmp_path / 'init.py'  # doesn't exist; default= avoids _load_module erroring

    @execute_module
    def boom(path, workdir, current_version_dir, *, module):
        assert os.getcwd() == str(workdir)
        raise RuntimeError('script failed')

    try:
        with pytest.raises(RuntimeError):
            boom(fake_script, workdir, None, default='pass')
        assert os.getcwd() == original_cwd
    finally:
        os.chdir(original_cwd)


@pytest.mark.unit
def test_cwd_is_restored_on_success(tmp_path):
    original_cwd = os.getcwd()
    workdir = tmp_path / 'workdir'
    workdir.mkdir()
    fake_script = tmp_path / 'init.py'

    @execute_module
    def ok(path, workdir, current_version_dir, *, module):
        assert os.getcwd() == str(workdir)
        return 'result'

    try:
        with patch('git_system_follower.package.script.os.remove'):
            result = ok(fake_script, workdir, None, default='pass')
        assert result == 'result'
        assert os.getcwd() == original_cwd
    finally:
        os.chdir(original_cwd)
