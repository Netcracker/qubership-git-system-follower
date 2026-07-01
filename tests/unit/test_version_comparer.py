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
from git_system_follower.utils.version_comparer import VersionComparer


@pytest.mark.unit
@pytest.mark.parametrize("version, expected", [
    ("24.1_something", True),
    ("25.2_feature", True),
    ("23.4_release", True),
    ("1.0.0", False),
    ("2.3.5", False),
    ("v1.2.3", False),
    ("prefix-1.0.0-suffix", False),
])
def test_is_quarterly(version, expected):
    comparer = VersionComparer()
    assert comparer.is_quarterly(version) == expected


@pytest.mark.unit
@pytest.mark.parametrize("version, expected", [
    ("1.0.0", True),
    ("2.3.5", True),
    ("v1.2.3", True),
    ("prefix-1.0.0-suffix", True),
    ("10.20.30", True),
    ("24.1_something", False),
    ("not_a_version", False),
    ("1.2", False),
])
def test_has_semver(version, expected):
    comparer = VersionComparer()
    assert comparer.has_semver(version) == expected


@pytest.mark.unit
@pytest.mark.parametrize("v1, v2, expected", [
    # Same versions
    ("1.0.0", "1.0.0", 0),
    ("2.3.5", "2.3.5", 0),
    # Different major versions (should return -2 or 2)
    ("1.0.0", "2.0.0", -2),
    ("2.0.0", "1.0.0", 2),
    ("1.5.9", "2.0.1", -2),
    # Same major, different minor/patch (should return -1 or 1)
    ("1.0.0", "1.0.1", -1),
    ("1.0.1", "1.0.0", 1),
    ("1.1.0", "1.2.0", -1),
    ("1.2.0", "1.1.0", 1),
    ("1.1.5", "1.2.3", -1),
    # With prefixes/suffixes
    ("v1.0.0", "v1.0.1", -1),
    ("v1.0.0-alpha", "v1.0.0-beta", -1),
])
def test_compare_semver_to_semver(v1, v2, expected):
    comparer = VersionComparer()
    assert comparer.compare(v1, v2) == expected


@pytest.mark.unit
@pytest.mark.parametrize("v1, v2, expected", [
    ("24.1_release", "24.1_release", 0),
    ("24.1_release", "24.2_release", -1),
    ("24.2_release", "24.1_release", 1),
    ("23.4_old", "24.1_new", -1),
])
def test_compare_quarterly_to_quarterly(v1, v2, expected):
    comparer = VersionComparer()
    result = comparer.compare(v1, v2)
    assert (result < 0) == (expected < 0)
    assert (result > 0) == (expected > 0)
    assert (result == 0) == (expected == 0)


@pytest.mark.unit
@pytest.mark.parametrize("quarterly, semver", [
    ("24.1_something", "1.0.0"),
    ("23.4_release", "2.5.3"),
    ("25.2_feature", "1.2.3"),
    ("24.1_old", "v1.0.0"),
])
def test_compare_quarterly_to_semver(quarterly, semver):
    comparer = VersionComparer()
    # Quarterly < Semver (should return -1)
    assert comparer.compare(quarterly, semver) == -1
    # Semver > Quarterly (should return 1)
    assert comparer.compare(semver, quarterly) == 1


@pytest.mark.unit
@pytest.mark.parametrize("v1, v2", [
    ("1.0.0", "  1.0.0  "),
    ("  2.3.5", "2.3.5"),
])
def test_compare_with_whitespace(v1, v2):
    comparer = VersionComparer()
    assert comparer.compare(v1, v2) == 0


@pytest.mark.unit
@pytest.mark.parametrize("v1, v2, expected", [
    ("abc", "abc", 0),
    ("abc", "xyz", -1),
    ("xyz", "abc", 1),
])
def test_compare_fallback_lexicographic(v1, v2, expected):
    comparer = VersionComparer()
    assert comparer.compare(v1, v2) == expected


@pytest.mark.unit
def test_compare_result_values():
    comparer = VersionComparer()
    # Major version difference
    assert comparer.compare("1.0.0", "2.0.0") == -2
    assert comparer.compare("2.0.0", "1.0.0") == 2
    # Same major version
    assert comparer.compare("1.0.0", "1.0.1") == -1
    assert comparer.compare("1.0.1", "1.0.0") == 1
    # Equal
    assert comparer.compare("1.2.3", "1.2.3") == 0


@pytest.mark.unit
def test_quarterly_to_semver_detection():
    comparer = VersionComparer()
    # Quarterly to semver
    start_quarterly = "24.1_release"
    end_semver = "1.0.0"
    is_quarterly_to_semver = (
        comparer.is_quarterly(start_quarterly) and
        not comparer.is_quarterly(end_semver)
    )
    assert is_quarterly_to_semver is True

    # Semver to semver
    start_semver = "1.0.0"
    end_semver = "1.1.0"
    is_quarterly_to_semver = (
        comparer.is_quarterly(start_semver) and
        not comparer.is_quarterly(end_semver)
    )
    assert is_quarterly_to_semver is False

    # Quarterly to quarterly
    start_quarterly = "24.1_release"
    end_quarterly = "24.2_release"
    is_quarterly_to_semver = (
        comparer.is_quarterly(start_quarterly) and
        not comparer.is_quarterly(end_quarterly)
    )
    assert is_quarterly_to_semver is False


@pytest.mark.unit
def test_version_sorting_mixed_types():
    comparer = VersionComparer()
    versions = [
        "1.2.0",
        "24.1_release",
        "1.0.0",
        "24.2_feature",
        "1.1.0",
        "23.4_old",
    ]

    # Sort using the comparer - mimics the logic in updater.py
    sorted_versions = sorted(
        versions,
        key=lambda v: (comparer.compare('0.0.0', v), v)
    )

    # Find indices where quarterly and semver versions are
    quarterly_indices = [i for i, v in enumerate(sorted_versions)
                        if comparer.is_quarterly(v)]
    semver_indices = [i for i, v in enumerate(sorted_versions)
                     if not comparer.is_quarterly(v)]

    # Verify all semver versions appear before all quarterly versions
    if quarterly_indices and semver_indices:
        assert max(semver_indices) < min(quarterly_indices), \
            "Semver versions should all come before quarterly versions when sorting"

    # Expected order: semver versions sorted, then quarterly versions sorted
    expected = ['1.0.0', '1.1.0', '1.2.0', '23.4_old', '24.1_release', '24.2_feature']
    assert sorted_versions == expected
