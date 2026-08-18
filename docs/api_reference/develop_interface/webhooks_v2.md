# webhooks module (v2)
API provided in `webhooks.py` module. This module contains functions for easy interaction with GitLab webhooks.

The v2 API is identical to v1 — only the import path differs.

## Usage in package API

```python
from git_system_follower.develop.api.v2.webhooks import Webhook, create_webhook, update_webhook, delete_webhook
```

### Examples

```python
from git_system_follower.develop.api.v2.types import Parameters
from git_system_follower.develop.api.v2.webhooks import Webhook, create_webhook


def init(parameters: Parameters):
    webhook = Webhook(
        url='https://web.dummy.com/gitlab-webhook',
        push_events=True,
        merge_requests_events=True,
    )
    create_webhook(parameters, webhook)
```

## Functions description

See [v1 Webhooks](webhooks_v1.md) for the full function reference (`create_webhook`, `update_webhook`, `delete_webhook`). Signatures and behavior are identical.
