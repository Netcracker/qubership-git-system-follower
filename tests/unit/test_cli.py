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
import click

from git_system_follower.utils.cli import _normalize_extra_args


EXTRA = '--extra'
EXTRA_EXTERNAL = '--extra-external'


@pytest.mark.unit
def test_normalize_extra_no_expanded_flag():
    """ --extra without expanded flag appends empty string """
    result = _normalize_extra_args([EXTRA, 'NAME', 'value', 'masked'])
    assert result == [EXTRA, 'NAME', 'value', 'masked', '']


@pytest.mark.unit
def test_normalize_extra_expanded():
    """ --extra with expanded flag """
    result = _normalize_extra_args([EXTRA, 'NAME', 'value', 'masked', 'expanded'])
    assert result == [EXTRA, 'NAME', 'value', 'masked', 'expanded']


@pytest.mark.unit
def test_normalize_extra_no_expanded():
    """ --extra with no-expanded flag """
    result = _normalize_extra_args([EXTRA, 'NAME', 'value', 'masked', 'no-expanded'])
    assert result == [EXTRA, 'NAME', 'value', 'masked', 'no-expanded']


@pytest.mark.unit
def test_normalize_extra_external_no_expanded_flag():
    """ --extra-external without expanded flag appends empty string """
    result = _normalize_extra_args([EXTRA_EXTERNAL, 'NAME', 'value', 'masked'])
    assert result == [EXTRA_EXTERNAL, 'NAME', 'value', 'masked', '']


@pytest.mark.unit
def test_normalize_extra_external_expanded():
    """ --extra-external with expanded flag """
    result = _normalize_extra_args([EXTRA_EXTERNAL, 'NAME', 'value', 'masked', 'expanded'])
    assert result == [EXTRA_EXTERNAL, 'NAME', 'value', 'masked', 'expanded']


@pytest.mark.unit
def test_normalize_extra_multiple():
    """ Multiple --extra flags with mixed expanded flags """
    result = _normalize_extra_args([
        EXTRA, 'A', '1', 'masked', 'expanded',
        EXTRA_EXTERNAL, 'B', '2', 'no-masked', 'no-expanded',
        EXTRA, 'C', '3', 'masked',
    ])
    assert result == [
        EXTRA, 'A', '1', 'masked', 'expanded',
        EXTRA_EXTERNAL, 'B', '2', 'no-masked', 'no-expanded',
        EXTRA, 'C', '3', 'masked', '',
    ]


@pytest.mark.unit
def test_normalize_extra_invalid_expanded_value():
    """ Invalid expanded value raises BadParameter with clear message """
    with pytest.raises(click.BadParameter) as exc_info:
        _normalize_extra_args([EXTRA, 'NAME', 'value', 'masked', 'ALU'])
    assert "'ALU' is not one of 'expanded', 'no-expanded'." in str(exc_info.value)


@pytest.mark.unit
def test_normalize_extra_external_invalid_expanded_value():
    """ Invalid expanded value for --extra-external raises BadParameter """
    with pytest.raises(click.BadParameter) as exc_info:
        _normalize_extra_args([EXTRA_EXTERNAL, 'APP_NAME', 'app-name', 'no-masked', 'ALU'])
    assert "'ALU' is not one of 'expanded', 'no-expanded'." in str(exc_info.value)


@pytest.mark.unit
def test_normalize_extra_case_insensitive_expanded():
    """ Expanded flag values are case-insensitive """
    result = _normalize_extra_args([EXTRA, 'NAME', 'value', 'masked', 'EXPANDED'])
    assert result[-1] == 'EXPANDED'
    result = _normalize_extra_args([EXTRA, 'NAME', 'value', 'masked', 'No-Expanded'])
    assert result[-1] == 'No-Expanded'


@pytest.mark.unit
def test_normalize_extra_flag_followed_by_another_flag():
    """ --extra without expanded flag followed by another --extra flag """
    result = _normalize_extra_args([
        EXTRA, 'NAME', 'value', 'masked', EXTRA, 'NAME2', 'value2', 'masked'
    ])
    assert result == [
        EXTRA, 'NAME', 'value', 'masked', '',
        EXTRA, 'NAME2', 'value2', 'masked', '',
    ]


@pytest.mark.unit
def test_normalize_extra_external_followed_by_another_flag():
    """ --extra-external without expanded flag followed by another --extra-external flag """
    result = _normalize_extra_args([
        EXTRA_EXTERNAL, 'APP_NAME', 'app-name', 'no-masked', EXTRA_EXTERNAL, 'B', '2', 'masked'
    ])
    assert result == [
        EXTRA_EXTERNAL, 'APP_NAME', 'app-name', 'no-masked', '',
        EXTRA_EXTERNAL, 'B', '2', 'masked', '',
    ]


@pytest.mark.unit
def test_normalize_extra_flag_followed_by_expanded():
    """ --extra flag followed by expanded value """
    result = _normalize_extra_args([
        EXTRA, 'NAME', 'value', 'masked', 'expanded', EXTRA, 'NAME2', 'value2', 'masked', 'no-expanded'
    ])
    assert result == [
        EXTRA, 'NAME', 'value', 'masked', 'expanded',
        EXTRA, 'NAME2', 'value2', 'masked', 'no-expanded',
    ]
