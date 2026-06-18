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

""" Module with api to work with GitLab webhooks """
from typing import TypedDict

from gitlab.v4.objects import Project
from gitlab.base import RESTObject
from gitlab.exceptions import GitlabCreateError

from git_system_follower.logger import logger


__all__ = ['Webhook', 'get_webhooks', 'create_webhook', 'update_webhook', 'delete_webhook']


class Webhook(TypedDict, total=False):
    """ GitLab project webhook

    Dictionary items:
        - url : str | webhook URL
        - push_events : bool | trigger on push events
        - issues_events : bool | trigger on issues events
        - merge_requests_events : bool | trigger on merge request events
        - wiki_page_events : bool | trigger on wiki page events
        - deployment_events : bool | trigger on deployment events
        - releases_events : bool | trigger on release events
        - pipeline_events : bool | trigger on pipeline events
        - job_events : bool | trigger on job events
        - tag_push_events : bool | trigger on tag push events
        - note_events : bool | trigger on comment events
        - confidential_issues_events : bool | trigger on confidential issues events
        - confidential_note_events : bool | trigger on confidential comment events
        - token : str | secret token for webhook authentication
        - enable_ssl_verification : bool | enable SSL verification
    """
    url: str
    push_events: bool
    issues_events: bool
    merge_requests_events: bool
    wiki_page_events: bool
    deployment_events: bool
    releases_events: bool
    pipeline_events: bool
    job_events: bool
    tag_push_events: bool
    note_events: bool
    confidential_issues_events: bool
    confidential_note_events: bool
    token: str
    enable_ssl_verification: bool
    managed_by: str


def get_webhooks(project: Project) -> dict[str, Webhook]:
    """ Get webhooks from remote repository

    :param project: GitLab project

    :return: webhooks dict: key - webhook URL, value - webhook information
    """
    gitlab_hooks = project.hooks.list(iterator=True)
    webhooks = {}
    for hook in gitlab_hooks:
        webhooks[hook.url] = _serialize_webhook(hook)
    return webhooks


def create_webhook(project: Project, webhook: Webhook) -> Webhook:
    """ Creating webhook - only creates, does not update existing

    :param project: Gitlab project
    :param webhook: webhook to be created
    :return: Gitlab REST API response
    """
    logger.info('\t-> Creating webhook')
    url = webhook['url']

    remote_hooks: list[RESTObject] = project.hooks.list(iterator=True)
    for remote_hook in remote_hooks:
        if webhook['url'] != remote_hook.url:
            continue

        # Webhook already exists
        logger.info(f"\t\tWebhook with URL {url} already exists. Skip creation")
        return _serialize_webhook(remote_hook)

    # Webhook doesn't exist - create new
    try:
        hook = project.hooks.create(webhook)
    except GitlabCreateError:
        msg = (
            f"Failed to create webhook with URL {url}. "
            f"Please make sure you follow GitLab's rules for webhooks "
            f"https://docs.gitlab.com/ee/user/project/integrations/webhooks.html"
        )
        logger.critical(msg)
        raise
    logger.info(f"\t\tWebhook with URL {url} has been created")
    logger.debug(f'\t\tResponse:\n{hook.pformat()}')
    return _serialize_webhook(hook)


def update_webhook(project: Project, webhook: Webhook) -> Webhook:
    """ Update webhook - uses delete + create pattern

    :param project: Gitlab project
    :param webhook: webhook configuration to update to
    :return: Gitlab REST API response
    """
    logger.info('\t-> Updating webhook')
    url = webhook['url']

    # Delete existing webhook if it exists
    delete_webhook(project, webhook)

    # Create new webhook with updated configuration
    try:
        hook = project.hooks.create(webhook)
    except GitlabCreateError:
        msg = (
            f"Failed to create webhook with URL {url}. "
            f"Please make sure you follow GitLab's rules for webhooks "
            f"https://docs.gitlab.com/ee/user/project/integrations/webhooks.html"
        )
        logger.critical(msg)
        raise
    logger.info(f"\t\tWebhook with URL {url} has been updated (delete + create)")
    logger.debug(f'\t\tResponse:\n{hook.pformat()}')
    return _serialize_webhook(hook)


def delete_webhook(project: Project, webhook: Webhook) -> None:
    """ Deleting webhook - deletes by URL regardless of configuration

    :param project: Gitlab project
    :param webhook: webhook to be deleted (only URL is used for matching)
    """
    logger.info('\t-> Deleting webhook')
    url = webhook['url']

    remote_hooks: list[RESTObject] = project.hooks.list(iterator=True)
    for remote_hook in remote_hooks:
        if webhook['url'] != remote_hook.url:
            continue

        # Found webhook with matching URL - delete it
        project.hooks.delete(remote_hook.id)
        logger.info(f"\t\tWebhook with URL {url} has been deleted")
        return

    logger.info(f"\t\tWebhook with URL {url} not found. Nothing to delete")


def _serialize_webhook(remote_hook: RESTObject) -> Webhook:
    return Webhook(
        url=remote_hook.url,
        push_events=remote_hook.push_events,
        issues_events=remote_hook.issues_events,
        merge_requests_events=remote_hook.merge_requests_events,
        wiki_page_events=remote_hook.wiki_page_events,
        deployment_events=getattr(remote_hook, 'deployment_events', False),
        releases_events=getattr(remote_hook, 'releases_events', False),
        pipeline_events=remote_hook.pipeline_events,
        job_events=getattr(remote_hook, 'job_events', False),
        tag_push_events=remote_hook.tag_push_events,
        note_events=getattr(remote_hook, 'note_events', False),
        confidential_issues_events=getattr(remote_hook, 'confidential_issues_events', False),
        confidential_note_events=getattr(remote_hook, 'confidential_note_events', False),
        token=getattr(remote_hook, 'token', ''),
        enable_ssl_verification=remote_hook.enable_ssl_verification
    )


def _webhooks_match(webhook: Webhook, remote_hook: RESTObject) -> bool:
    """ Check if webhook configuration matches remote hook """
    return (
        webhook.get('push_events', True) == remote_hook.push_events and
        webhook.get('issues_events', False) == remote_hook.issues_events and
        webhook.get('merge_requests_events', False) == remote_hook.merge_requests_events and
        webhook.get('wiki_page_events', False) == remote_hook.wiki_page_events and
        webhook.get('deployment_events', False) ==
            getattr(remote_hook, 'deployment_events', False) and
        webhook.get('releases_events', False) ==
            getattr(remote_hook, 'releases_events', False) and
        webhook.get('pipeline_events', False) == remote_hook.pipeline_events and
        webhook.get('job_events', False) == getattr(remote_hook, 'job_events', False) and
        webhook.get('tag_push_events', False) == remote_hook.tag_push_events and
        webhook.get('note_events', False) == getattr(remote_hook, 'note_events', False) and
        webhook.get('confidential_issues_events', False) ==
            getattr(remote_hook, 'confidential_issues_events', False) and
        webhook.get('confidential_note_events', False) ==
            getattr(remote_hook, 'confidential_note_events', False) and
        webhook.get('enable_ssl_verification', True) == remote_hook.enable_ssl_verification
    )


def _update_webhook(remote_hook: RESTObject, webhook: Webhook) -> None:
    """ Update remote hook with webhook configuration """
    remote_hook.push_events = webhook.get('push_events', True)
    remote_hook.issues_events = webhook.get('issues_events', False)
    remote_hook.merge_requests_events = webhook.get('merge_requests_events', False)
    remote_hook.wiki_page_events = webhook.get('wiki_page_events', False)
    if 'deployment_events' in webhook:
        remote_hook.deployment_events = webhook['deployment_events']
    if 'releases_events' in webhook:
        remote_hook.releases_events = webhook['releases_events']
    remote_hook.pipeline_events = webhook.get('pipeline_events', False)
    if 'job_events' in webhook:
        remote_hook.job_events = webhook['job_events']
    remote_hook.tag_push_events = webhook.get('tag_push_events', False)
    if 'note_events' in webhook:
        remote_hook.note_events = webhook['note_events']
    if 'confidential_issues_events' in webhook:
        remote_hook.confidential_issues_events = webhook['confidential_issues_events']
    if 'confidential_note_events' in webhook:
        remote_hook.confidential_note_events = webhook['confidential_note_events']
    if 'token' in webhook:
        remote_hook.token = webhook['token']
    remote_hook.enable_ssl_verification = webhook.get('enable_ssl_verification', True)
