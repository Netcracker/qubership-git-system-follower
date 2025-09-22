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
from pathlib import Path
from datetime import datetime
from git_system_follower.package import package_info
from git_system_follower.states import PackageState

GEARS_DIR = Path(__file__).parent.parent / "gears"

@pytest.mark.unit
@pytest.mark.parametrize("gear_folder, state_type, expected_match, expect_exception", [
    ("simple", None, "simple", False),     # Simple gear with no existing state
    ("complex", None, "complex", False),   # Complex gear with no existing state
    ("complex", "simple", None, True),     # Mismatch: gear is complex, state is simple
    ("simple", "complex", None, True),     # Mismatch: gear is simple, state is complex
])
def test_get_gear_info(gear_folder, state_type, expected_match, expect_exception):
    path = GEARS_DIR / gear_folder

    state = None
    if state_type:
        state = PackageState(
            name="hello-gear",
            version="v1.1_branch_r1.0.0",
            used_template="default",
            template_variables={},
            last_update=str(datetime.now()),
            structure_type=state_type,
            dependencies=[],
            cicd_variables=[],
        )

    if expect_exception:
        with pytest.raises(SystemExit):
            package_info.get_gear_info(path=path, state=state)
    else:
        result = package_info.get_gear_info(path=path, state=state)
        assert expected_match in result["structure_type"], (
            f"Expected structure type '{expected_match}' in result, got {result['structure_type']}"
        )
