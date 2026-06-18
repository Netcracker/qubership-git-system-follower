# webhooks module
API provided in `webhooks.py` module. This module contains functions for easy interaction with GitLab webhooks.

!!! info
      Webhooks are externally managed resources. GSF tracks them in state for reference purposes but does not enforce configuration validation. All webhook operations are simple create/update/delete with no protection mechanisms.

## Usage in package API

```python
from git_system_follower.develop.api.webhooks import Webhook, create_webhook, update_webhook, delete_webhook
```

### Examples

#### Basic webhook creation
```python
from git_system_follower.develop.api.types import Parameters
from git_system_follower.develop.api.webhooks import Webhook, create_webhook


def init(parameters: Parameters):
    webhook = Webhook(
        url='https://web.dummy.com/gitlab-webhook',
        push_events=True,
        merge_requests_events=True,
        pipeline_events=True,
        enable_ssl_verification=True
    )
    create_webhook(parameters, webhook)
```

#### Update webhook configuration
```python
from git_system_follower.develop.api.types import Parameters
from git_system_follower.develop.api.webhooks import Webhook, update_webhook


def update(parameters: Parameters):
    # Same URL, different event triggers
    webhook = Webhook(
        url='https://web.dummy.com/gitlab-webhook',
        push_events=True,
        merge_requests_events=True,
        pipeline_events=True,
        job_events=True,  # NEW: added job events
        releases_events=True  # NEW: added releases events
    )
    update_webhook(parameters, webhook)  # Delete + create pattern
```

#### Delete webhook
```python
from git_system_follower.develop.api.types import Parameters
from git_system_follower.develop.api.webhooks import Webhook, delete_webhook


def delete(parameters: Parameters):
    webhook = Webhook(url='https://web.dummy.com/gitlab-webhook')
    delete_webhook(parameters, webhook)
```

#### Change webhook URL
```python
from git_system_follower.develop.api.types import Parameters
from git_system_follower.develop.api.webhooks import Webhook, create_webhook, delete_webhook


def update(parameters: Parameters):
    # Delete old webhook
    old_webhook = Webhook(url='https://old-web.dummy.com/webhook')
    delete_webhook(parameters, old_webhook)
    
    # Create new webhook
    new_webhook = Webhook(
        url='https://new-web.dummy.com/webhook',
        push_events=True,
        merge_requests_events=True
    )
    create_webhook(parameters, new_webhook)
```

## Functions description

### `create_webhook` function
```python
def create_webhook(parameters: Parameters, webhook: Webhook) -> Webhook
```
Create webhook using GitLab REST API. Only creates new webhooks, skips if already exists.

**Behavior:**
1. If webhook doesn't exist: create webhook
2. If webhook exists: skip creation (use `update_webhook` to modify)

#### Arguments
| Name         | Type           | Description                                    |
|--------------|----------------|------------------------------------------------|
| `parameters` | `Parameters`   | Parameters that were passed to the package API |
| `webhook`    | `Webhook`      | Webhook configuration to create                |

#### Returns
`Webhook` - Created or existing webhook configuration

---

### `update_webhook` function
```python
def update_webhook(parameters: Parameters, webhook: Webhook) -> Webhook
```
Update webhook using GitLab REST API. Uses **delete + create** pattern to ensure clean configuration update.

**Behavior:**
1. Delete webhook if exists (by URL)
2. Create webhook with new configuration

!!! note
    This function uses delete + create pattern for predictable behavior. The webhook will be briefly unavailable during the update.

#### Arguments
| Name         | Type           | Description                                    |
|--------------|----------------|------------------------------------------------|
| `parameters` | `Parameters`   | Parameters that were passed to the package API |
| `webhook`    | `Webhook`      | Webhook configuration to update to             |

#### Returns
`Webhook` - Updated webhook configuration

---

### `delete_webhook` function
```python
def delete_webhook(parameters: Parameters, webhook: Webhook) -> None
```
Delete webhook using GitLab REST API. Deletes by URL regardless of configuration.

**Behavior:**
1. If webhook exists: delete it
2. If webhook doesn't exist: skip (nothing to delete)

#### Arguments
| Name         | Type           | Description                                    |
|--------------|----------------|------------------------------------------------|
| `parameters` | `Parameters`   | Parameters that were passed to the package API |
| `webhook`    | `Webhook`      | Webhook to delete (only URL is used)           |

#### Returns
`None`

---

## Webhook TypedDict

```python
class Webhook(TypedDict, total=False):
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
```

### Fields

| Field                          | Type   | Default | Description                                      |
|--------------------------------|--------|---------|--------------------------------------------------|
| `url`                          | `str`  | *required* | Webhook URL endpoint                          |
| `push_events`                  | `bool` | `True`  | Trigger on push events                           |
| `issues_events`                | `bool` | `False` | Trigger on issue events                          |
| `merge_requests_events`        | `bool` | `False` | Trigger on merge request events                  |
| `wiki_page_events`             | `bool` | `False` | Trigger on wiki page events                      |
| `deployment_events`            | `bool` | `False` | Trigger on deployment events                     |
| `releases_events`              | `bool` | `False` | Trigger on release events                        |
| `pipeline_events`              | `bool` | `False` | Trigger on pipeline events                       |
| `job_events`                   | `bool` | `False` | Trigger on job events                            |
| `tag_push_events`              | `bool` | `False` | Trigger on tag push events                       |
| `note_events`                  | `bool` | `False` | Trigger on comment/note events                   |
| `confidential_issues_events`   | `bool` | `False` | Trigger on confidential issue events             |
| `confidential_note_events`     | `bool` | `False` | Trigger on confidential comment events           |
| `token`                        | `str`  | `""`    | Secret token for webhook authentication          |
| `enable_ssl_verification`      | `bool` | `True`  | Enable SSL certificate verification              |

### Minimal example

Only the `url` field is required. All event triggers default to `False` except `push_events` (defaults to `True`):

```python
# Minimal webhook - only push_events enabled
webhook = Webhook(url='https://example.com/webhook')
```

### Complete example

```python
# Webhook with all event types enabled
webhook = Webhook(
    url='https://example.com/webhook',
    push_events=True,
    issues_events=True,
    merge_requests_events=True,
    wiki_page_events=True,
    deployment_events=True,
    releases_events=True,
    pipeline_events=True,
    job_events=True,
    tag_push_events=True,
    note_events=True,
    confidential_issues_events=True,
    confidential_note_events=True,
    token='my-secret-webhook-token',
    enable_ssl_verification=True
)
```

## State file tracking

Webhooks are tracked in the state file for audit purposes:

```yaml
webhooks:
  urls:
    - 'https://web.dummy.com/webhook'
    - 'https://monitoring.company.com/webhook'
  hash: '<hash-of-all-webhook-configs>'
```

**Key points:**
- The `hash` provides cryptographic proof of webhook configurations at install time
- Hash mismatches trigger warnings but **do not block operations**
- Purpose: audit trail and blame prevention, not enforcement
- All webhooks are treated equally (no distinction between managed/external)

## Best practices

### 1. Only specify events you need
```python
# Good - explicit about what events are enabled
webhook = Webhook(
    url='https://web.dummy.com/webhook',
    merge_requests_events=True,
    pipeline_events=True
)

# Avoid - unnecessary verbosity
webhook = Webhook(
    url='https://web.dummy.com/webhook',
    push_events=False,
    issues_events=False,
    merge_requests_events=True,
    wiki_page_events=False,
    # ... listing all 12+ fields
)
```

### 2. Use update_webhook for configuration changes
```python
# When changing event triggers on same URL
def update(parameters: Parameters):
    webhook = Webhook(
        url='https://web.dummy.com/webhook',
        push_events=True,
        merge_requests_events=True,
        job_events=True  # Adding new event
    )
    update_webhook(parameters, webhook)  # Clean delete + create
```

### 3. Use delete + create for URL changes
```python
# When URL changes
def update(parameters: Parameters):
    delete_webhook(parameters, Webhook(url='https://old-url.com/webhook'))
    create_webhook(parameters, Webhook(url='https://new-url.com/webhook'))
```

### 4. Multiple webhooks per package
```python
def init(parameters: Parameters):
    # CI/CD webhook
    ci_webhook = Webhook(
        url='https://web.dummy.com/webhook',
        pipeline_events=True,
        job_events=True
    )
    create_webhook(parameters, ci_webhook)
    
    # Monitoring webhook
    monitoring_webhook = Webhook(
        url='https://monitoring.company.com/webhook',
        push_events=True,
        merge_requests_events=True
    )
    create_webhook(parameters, monitoring_webhook)
```

## Webhook URL validation

GitLab enforces specific rules for webhook URLs. If webhook creation fails, ensure your URL follows [GitLab's webhook rules](https://docs.gitlab.com/ee/user/project/integrations/webhooks.html):

- Must be a valid URL
- Must use HTTP or HTTPS protocol
- Local network URLs may be blocked depending on GitLab configuration
- URL must be accessible from GitLab server
