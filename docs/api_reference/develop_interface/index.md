# Develop Interface

The develop API has two versions matching the `apiVersion` in `package.yaml`:

## API Versions

| Version | Import Path | Package Requirement |
|---------|-------------|---------------------|
| **v1** | `git_system_follower.develop.api.v1` | `apiVersion: "v1"` |
| **v2** | `git_system_follower.develop.api.v2` | `apiVersion: "v2"` |

!!! note
    The unversioned path (`git_system_follower.develop.api.*`) is a **backwards-compatible shim**
    that works for v1 packages without needing the `.v1.` segment. New packages should use the
    explicit versioned paths above.

## Quicklinks by Version

### v1 (Legacy)
* [v1 Types](types_v1.md) — Core types: `Parameters`, `System`, `ExtraParam`, `CICDVariable`, `Webhook`
* [v1 CI/CD Variables](cicd_variables_v1.md) — `create_variable`, `update_variable`, `delete_variable`
* [v1 Webhooks](webhooks_v1.md) — `create_webhook`, `delete_webhook`
* [v1 Templates](templates_v1.md) — `create_template`, `update_template`, `delete_template`

### v2 (Current)
* [v2 Types](types_v2.md) — v1 types **+** `ProjectMetadata`, `GraphQLClient`
* [v2 CI/CD Variables](cicd_variables_v2.md) — Same as v1
* [v2 Webhooks](webhooks_v2.md) — Same as v1
* [v2 Templates](templates_v2.md) — **Auto-syncs project metadata** (description, icon, CI/CD catalog)

## Key v2 Differences

| Feature | v1 | v2 |
|---------|-----|-----|
| Project metadata sync | Manual | **Automatic** on template create/update/delete |
| `ProjectMetadata` class | ❌ | ✅ Description, icon, CI/CD catalog |
| `GraphQLClient` class | ❌ | ✅ Direct GraphQL mutations/queries |
| `subtype` support | ❌ | ✅ `component` |

## Usage

```python
# v1 package (apiVersion: "v1")
from git_system_follower.develop.api.v1 import (
    create_template, Parameters, System
)

# v2 package (apiVersion: "v2")
from git_system_follower.develop.api.v2 import (
    create_template, update_template, delete_template,
    Parameters, ProjectMetadata, GraphQLClient
)
```

### Legacy (backward-compatible) imports for v1

```python
# v1 packages may also use the unversioned path (backward-compatible shim)
from git_system_follower.develop.api import (
    create_template, Parameters, System
)
```