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

from pathlib import Path
import json

from git_system_follower.package.cicd_variables import CICDVariable


__all__ = ['get_env']


def get_env(
        workdir: Path, current_cicd_variables: dict[str, CICDVariable], used_template: str | None
) -> dict[str, str]:
    """ Get environment variables for subprocessing package api scripts

    :param workdir: workdir for package api scripts
    :param current_cicd_variables: current Gitlab CI/CD variables
    :param used_template: last used template

    :return: ready-made dict with env variables
    """
    env = {
        'WORKDIR': str(workdir),
        'CURRENT_CICD_VARIABLES': json.dumps(current_cicd_variables),
    }
    if used_template is not None:
        env['USED_TEMPLATE'] = used_template
    return env
