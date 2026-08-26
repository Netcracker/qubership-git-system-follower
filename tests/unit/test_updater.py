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
from git_system_follower.package.updater import get_version_dirs
from git_system_follower.typings.package import PackageLocalData


@pytest.mark.unit
def test_get_version_dirs_quarterly_to_semver_with_intermediate_versions(tmp_path):
    """Test that intermediate semver versions are included when upgrading from quarterly to semver"""
    # Create mock package structure
    package_dir = tmp_path / "package"
    scripts_dir = package_dir / "git-system-follower-package" / "scripts"

    # Create version directories
    quarterly_versions = ["v26.3_main_r1.0.2", "v26.3_main_r1.0.3", "v26.3_main_r1.0.4"]
    semver_versions = ["2.0.0", "2.0.1", "2.1.0", "2.2.0"]

    for v in quarterly_versions + semver_versions:
        (scripts_dir / v).mkdir(parents=True, exist_ok=True)

    # Create package data
    package = PackageLocalData({
        "name": "test-gear",
        "version": "2.2.0",
        "path": package_dir,
        "dependencies": [],
        "type": "gitlab-ci-pipeline"
    })

    # State version is quarterly
    start_version = "v26.3_main_r1.0.2"

    # Get version directories
    versions, current_version = get_version_dirs(package, start_version)

    # Extract version names
    version_names = [v.name for v in versions]

    # Should include all quarterly > start (in order)
    assert version_names.index("v26.3_main_r1.0.3") < version_names.index("v26.3_main_r1.0.4")

    # Should include all semver <= target (in order, after quarterly)
    assert version_names.index("v26.3_main_r1.0.4") < version_names.index("2.0.0")
    assert version_names.index("2.0.0") < version_names.index("2.0.1")
    assert version_names.index("2.0.1") < version_names.index("2.1.0")
    assert version_names.index("2.1.0") < version_names.index("2.2.0")

    # Should NOT include the start version
    assert "v26.3_main_r1.0.2" not in version_names

    # Current version should be the start version
    assert current_version.name == "v26.3_main_r1.0.2"


@pytest.mark.unit
def test_get_version_dirs_quarterly_to_semver_no_intermediate(tmp_path):
    """Test quarterly to semver with no intermediate versions"""
    package_dir = tmp_path / "package"
    scripts_dir = package_dir / "git-system-follower-package" / "scripts"

    # Create version directories
    quarterly_versions = ["24.1_start", "24.2_mid"]
    semver_versions = ["1.0.0"]

    for v in quarterly_versions + semver_versions:
        (scripts_dir / v).mkdir(parents=True, exist_ok=True)

    package = PackageLocalData({
        "name": "test-gear",
        "version": "1.0.0",
        "path": package_dir,
        "dependencies": [],
        "type": "gitlab-ci-pipeline"
    })

    start_version = "24.1_start"

    versions, current_version = get_version_dirs(package, start_version)
    version_names = [v.name for v in versions]

    assert "24.2_mid" in version_names
    assert "1.0.0" in version_names
    assert "24.1_start" not in version_names
    assert current_version.name == "24.1_start"


@pytest.mark.unit
def test_get_version_dirs_semver_to_semver(tmp_path):
    """Test normal semver to semver update"""
    package_dir = tmp_path / "package"
    scripts_dir = package_dir / "git-system-follower-package" / "scripts"

    semver_versions = ["1.0.0", "1.1.0", "1.2.0", "2.0.0"]

    for v in semver_versions:
        (scripts_dir / v).mkdir(parents=True, exist_ok=True)

    package = PackageLocalData({
        "name": "test-gear",
        "version": "2.0.0",
        "path": package_dir,
        "dependencies": [],
        "type": "gitlab-ci-pipeline"
    })

    start_version = "1.0.0"

    versions, current_version = get_version_dirs(package, start_version)
    version_names = [v.name for v in versions]

    # Should include all versions > start and <= target
    assert "1.1.0" in version_names
    assert "1.2.0" in version_names
    assert "2.0.0" in version_names
    assert "1.0.0" not in version_names
    assert current_version.name == "1.0.0"


@pytest.mark.unit
def test_get_version_dirs_quarterly_to_quarterly(tmp_path):
    """Test quarterly to quarterly update"""
    package_dir = tmp_path / "package"
    scripts_dir = package_dir / "git-system-follower-package" / "scripts"

    quarterly_versions = ["24.1_start", "24.2_mid", "24.3_end"]

    for v in quarterly_versions:
        (scripts_dir / v).mkdir(parents=True, exist_ok=True)

    package = PackageLocalData({
        "name": "test-gear",
        "version": "24.3_end",
        "path": package_dir,
        "dependencies": [],
        "type": "gitlab-ci-pipeline"
    })

    start_version = "24.1_start"

    versions, current_version = get_version_dirs(package, start_version)
    version_names = [v.name for v in versions]

    assert "24.2_mid" in version_names
    assert "24.3_end" in version_names
    assert "24.1_start" not in version_names
    assert current_version.name == "24.1_start"
