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

"""Tests for the @retry decorator in git_system_follower.utils.retry."""

from unittest.mock import Mock

import pytest

from git_system_follower.utils.retry import retry, NeedRetry, MaxRetries


@pytest.mark.unit
def test_succeeds_on_first_try_without_retrying():
    output_func, error_output_func = Mock(), Mock()
    func = Mock(return_value='ok')

    result = retry(output_func=output_func, error_output_func=error_output_func)(func)()

    assert result == 'ok'
    func.assert_called_once()
    output_func.assert_not_called()
    error_output_func.assert_not_called()


@pytest.mark.unit
def test_succeeds_after_some_needretry_failures():
    output_func, error_output_func = Mock(), Mock()
    func = Mock(side_effect=[NeedRetry('flaky 1'), NeedRetry('flaky 2'), 'ok'])

    result = retry(output_func=output_func, error_output_func=error_output_func)(func)()

    assert result == 'ok'
    assert func.call_count == 3
    assert error_output_func.call_count == 2
    assert output_func.call_count == 2


@pytest.mark.unit
def test_raises_max_retries_after_exhausting_attempts():
    output_func, error_output_func = Mock(), Mock()
    func = Mock(side_effect=NeedRetry('always fails'))

    with pytest.raises(MaxRetries):
        retry(max_retries=3, output_func=output_func, error_output_func=error_output_func)(func)()

    assert func.call_count == 3
    assert error_output_func.call_count == 3
    # No "Retry №N" message after the final, exhausting failure
    assert output_func.call_count == 2


@pytest.mark.unit
def test_non_needretry_exception_propagates_immediately():
    output_func, error_output_func = Mock(), Mock()
    func = Mock(side_effect=RuntimeError('not a retryable error'))

    with pytest.raises(RuntimeError):
        retry(output_func=output_func, error_output_func=error_output_func)(func)()

    func.assert_called_once()
    output_func.assert_not_called()
    error_output_func.assert_not_called()


@pytest.mark.unit
def test_passes_through_args_and_kwargs():
    func = Mock(return_value='ok')

    result = retry(output_func=Mock(), error_output_func=Mock())(func)(1, 2, key='value')

    func.assert_called_once_with(1, 2, key='value')
    assert result == 'ok'
