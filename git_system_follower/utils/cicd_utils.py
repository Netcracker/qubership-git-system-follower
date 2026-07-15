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

""" Helper functions to capture and revert CI/CD variable changes in GitLab projects """
from git_system_follower.package.cicd_variables import delete_variable
from git_system_follower.logger import logger


def capture_existing_cicd(project) -> dict:
    """ Capture current CI/CD variables so their values can be restored if the merge fails """
    existing_cicd = {}
    try:
        remote_vars = project.variables.list()
        for v in remote_vars:
            existing_cicd[v.key] = {'value': v.value, 'masked': v.masked}
    except Exception:
        existing_cicd = {}
    return existing_cicd


def restore_existing_cicd(project, existing_cicd: dict) -> None:
    """ Best-effort restore of CI/CD variables that existed before an install/uninstall """
    for var_name, original in existing_cicd.items():
        original_value, is_masked = original['value'], original['masked']
        masked_value = '*****' if is_masked else original_value
        try:
            var_obj = next((v for v in project.variables.list() if v.key == var_name), None)
            if var_obj:
                var_obj.value = original_value
                var_obj.save()
            else:
                project.variables.create({'key': var_name, 'value': original_value, 'masked': is_masked})
            logger.info(f'\t\tReverted CI/CD variable {var_name} to its previous value ({masked_value})')
        except Exception as e:
            logger.warning(f'\t\tFailed to revert CI/CD variable {var_name}: {e}')


def cleanup_created_cicd(project, created_cicd_variables) -> None:
    """ Best-effort cleanup of CI/CD variables created during an install/uninstall """
    if created_cicd_variables and isinstance(created_cicd_variables, tuple):
        for var_name in created_cicd_variables:
            try:
                delete_variable(
                    project, {'name': var_name, 'value': '', 'masked': False, 'env': ''}, is_force=True
                )
            except Exception as e:
                logger.warning(f'\t\tFailed to remove CI/CD variable {var_name}: {e}')


def revert_cicd_changes(project, existing_cicd: dict, state) -> None:
    """ Undo CI/CD variable changes made during an install/uninstall (best-effort)

    Only touches variables the gear(s) actually managed this run (per state's
    created CI/CD variable names) - restoring those that pre-existed to their
    original value, and removing those that did not exist before the run.
    Unrelated project CI/CD variables are left untouched and unlogged.
    """
    try:
        touched = tuple(state.get_all_created_cicd_variables())
    except Exception:
        touched = ()
    if not touched:
        return

    logger.info(':: Reverting CI/CD variable changes')
    to_restore = {name: original for name, original in existing_cicd.items() if name in touched}
    to_remove = tuple(name for name in touched if name not in existing_cicd)
    restore_existing_cicd(project, to_restore)
    cleanup_created_cicd(project, to_remove)
