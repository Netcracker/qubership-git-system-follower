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

""" Module with api to work with GitLab webhooks for package developers """
import json
from git_system_follower.package.package_info import get_gear_info
from git_system_follower.variables import PACKAGE_API_RESULT as __PACKAGE_API_RESULT
from git_system_follower.develop.api.types import Parameters
from git_system_follower.errors import PackageInterfaceError
from git_system_follower.package.webhooks import (
    Webhook,
    create_webhook as __create_webhook,
    update_webhook as __update_webhook,
    delete_webhook as __delete_webhook
)


__all__ = ['Webhook', 'create_webhook', 'update_webhook', 'delete_webhook']


def create_webhook(parameters: Parameters, webhook: Webhook) -> Webhook:
    """ Create webhook using gitlab REST API

    Creates a new webhook, skips if already exists:
        1. If webhook doesn't exist: create webhook
        2. If webhook exists: skip creation (use update_webhook to modify)

    :param parameters: parameters that were passed to the package api
    :param webhook: webhook to be created

    :return: creation response if webhook is created
    """
    system_params = parameters._Parameters__system_params
    if webhook['url'] in system_params.created_webhooks_urls:
        raise PackageInterfaceError(
            f"{webhook['url']} webhook used in another package. According "
            f"to package manager policy, you cannot use the same webhook URL in "
            f"different packages"
        )

    structure_type = get_gear_info(system_params.script_dir.parents[2])['structure_type']
    response = __create_webhook(system_params.project, webhook)
    __add_info_about_webhook(response, structure_type=structure_type)
    return response


def update_webhook(parameters: Parameters, webhook: Webhook) -> Webhook:
    """ Update webhook using gitlab REST API (delete + create pattern)

    Updates existing webhook configuration:
        1. Deletes webhook if exists
        2. Creates webhook with new configuration

    :param parameters: parameters that were passed to the package api
    :param webhook: webhook configuration to update to

    :return: creation response after update
    """
    system_params = parameters._Parameters__system_params
    if webhook['url'] in system_params.created_webhooks_urls:
        raise PackageInterfaceError(
            f"{webhook['url']} webhook used in another package. According "
            f"to package manager policy, you cannot use the same webhook URL in "
            f"different packages"
        )

    structure_type = get_gear_info(system_params.script_dir.parents[2])['structure_type']
    response = __update_webhook(system_params.project, webhook)
    __add_info_about_webhook(response, structure_type=structure_type)
    return response


def delete_webhook(parameters: Parameters, webhook: Webhook) -> None:
    """ Delete webhook using gitlab REST API

    Deletes webhook by URL regardless of configuration:
        1. If webhook doesn't exist: do nothing
        2. If webhook exists: delete it

    :param parameters: parameters that were passed to the package api
    :param webhook: webhook to be deleted (only URL is used for matching)
    """
    system_params = parameters._Parameters__system_params
    if webhook['url'] in system_params.created_webhooks_urls:
        raise PackageInterfaceError(
            f"{webhook['url']} webhook used in another package. According "
            f"to package manager policy, you cannot use the same webhook URL in "
            f"different packages"
        )

    __delete_webhook(system_params.project, webhook)
    __delete_info_about_webhook(webhook)


def __add_info_about_webhook(webhook: Webhook, structure_type: str) -> None:
    with open(__PACKAGE_API_RESULT, 'r') as file:
        content = json.load(file)

    if structure_type == "simple":  # to allow update of simple gear webhooks
        try:
            index = next(i
                    for i, w in enumerate(content["webhooks"])
                    if w.get("url") == webhook['url']
                )
            content['webhooks'].pop(index)
        except Exception:
            pass
    if webhook not in content['webhooks']:
        content['webhooks'].append(dict(webhook))
    with open(__PACKAGE_API_RESULT, 'w') as file:
        json.dump(content, file)

def __delete_info_about_webhook(webhook: Webhook) -> None:
    with open(__PACKAGE_API_RESULT, 'r') as file:
        content = json.load(file)
    if webhook not in content['webhooks']:
        return
    index = content['webhooks'].index(webhook)
    content['webhooks'].pop(index)
    with open(__PACKAGE_API_RESULT, 'w') as file:
        json.dump(content, file)
