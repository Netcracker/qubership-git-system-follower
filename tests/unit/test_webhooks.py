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
from git_system_follower.package import webhooks
from tests.config import vcr_instance, project


def create_webhook_config(url, **kwargs):
    """Helper function to create webhook configuration with defaults"""
    defaults = {
        "url": url,
        "push_events": False,
        "issues_events": False,
        "merge_requests_events": False,
        "wiki_page_events": False,
        "deployment_events": False,
        "releases_events": False,
        "pipeline_events": False,
        "job_events": False,
        "tag_push_events": False,
        "note_events": False,
        "confidential_issues_events": False,
        "confidential_note_events": False,
        "token": "test_token",
        "enable_ssl_verification": True
    }
    defaults.update(kwargs)
    return webhooks.Webhook(**defaults)


@pytest.mark.unit
@pytest.mark.parametrize("url, event_config", [
    # Basic webhook with only push events
    ("https://example.com/webhook1", {"push_events": True}),
    # Multiple common events, SSL disabled
    ("https://example.com/webhook2", {"push_events": True, "issues_events": True, "merge_requests_events": True,
                                       "pipeline_events": True, "enable_ssl_verification": False}),
    # Only merge request events
    ("https://example.com/webhook3", {"merge_requests_events": True}),
    # CI/CD focused: pipeline and job events
    ("https://example.com/webhook4", {"pipeline_events": True, "job_events": True}),
    # Release and deployment events
    ("https://example.com/webhook5", {"deployment_events": True, "releases_events": True}),
    # Tag push events
    ("https://example.com/webhook6", {"tag_push_events": True}),
    # Note/comment events
    ("https://example.com/webhook7", {"note_events": True}),
    # Wiki page events
    ("https://example.com/webhook8", {"wiki_page_events": True}),
    # Confidential events
    ("https://example.com/webhook9", {"confidential_issues_events": True, "confidential_note_events": True}),
    # All events enabled
    ("https://example.com/webhook10", {
        "push_events": True, "issues_events": True, "merge_requests_events": True, "wiki_page_events": True,
        "deployment_events": True, "releases_events": True, "pipeline_events": True, "job_events": True,
        "tag_push_events": True, "note_events": True, "confidential_issues_events": True,
        "confidential_note_events": True
    }),
])
@vcr_instance.use_cassette("test_webhooks")
def test_webhook_creation_and_deletion(url, event_config):
    """Test creating and deleting webhooks with various event configurations"""
    webhook = create_webhook_config(url, **event_config)

    # Create webhook
    created_webhook = webhooks.create_webhook(project=project, webhook=webhook)

    # Verify webhook was created with correct configuration
    assert created_webhook['url'] == url
    for key, expected_value in event_config.items():
        assert created_webhook[key] == expected_value, f"Mismatch in {key}"

    # Test idempotency: creating same webhook again should not fail
    created_again = webhooks.create_webhook(project=project, webhook=webhook)
    assert created_again['url'] == url

    # Delete webhook
    webhooks.delete_webhook(project=project, webhook=webhook)

    # Test deleting already deleted webhook (should not fail)
    webhooks.delete_webhook(project=project, webhook=webhook)


@pytest.mark.unit
@pytest.mark.parametrize("url, initial_events, updated_events", [
    # Update push events and SSL
    ("https://example.com/update1",
     {"push_events": True},
     {"issues_events": True, "merge_requests_events": True, "pipeline_events": True, "enable_ssl_verification": False}),
    # Enable all CI/CD events
    ("https://example.com/update2",
     {"push_events": True},
     {"deployment_events": True, "releases_events": True, "pipeline_events": True, "job_events": True,
      "tag_push_events": True}),
    # Enable confidential events
    ("https://example.com/update3",
     {"issues_events": True},
     {"note_events": True, "confidential_issues_events": True, "confidential_note_events": True}),
    # Add wiki and note events
    ("https://example.com/update4",
     {"push_events": True, "enable_ssl_verification": False},
     {"wiki_page_events": True, "note_events": True, "enable_ssl_verification": True}),
])
@vcr_instance.use_cassette("test_webhooks")
def test_webhook_update(url, initial_events, updated_events):
    """Test updating webhook configuration"""
    # Create initial webhook
    initial_webhook = create_webhook_config(url, token="initial_token", **initial_events)
    created = webhooks.create_webhook(project=project, webhook=initial_webhook)

    # Verify initial webhook was created correctly
    assert created['url'] == url
    for key, expected_value in initial_events.items():
        assert created[key] == expected_value, f"Mismatch in initial {key}"

    # Update webhook with new configuration
    updated_webhook = create_webhook_config(url, token="updated_token", **updated_events)
    result = webhooks.update_webhook(project=project, webhook=updated_webhook)

    # Verify all webhook settings were updated
    assert result['url'] == url
    for key, expected_value in updated_events.items():
        assert result[key] == expected_value, f"Mismatch in updated {key}"

    # Clean up
    webhooks.delete_webhook(project=project, webhook=updated_webhook)


@pytest.mark.unit
@vcr_instance.use_cassette("test_webhooks")
def test_get_webhooks():
    """Test retrieving all webhooks returns a dictionary"""
    # Get all webhooks
    all_webhooks = webhooks.get_webhooks(project=project)

    # Verify it returns a dictionary
    assert isinstance(all_webhooks, dict)

    # If there are webhooks, verify structure
    for url, webhook_data in all_webhooks.items():
        assert 'url' in webhook_data
        assert webhook_data['url'] == url
        assert 'push_events' in webhook_data
        assert 'enable_ssl_verification' in webhook_data
