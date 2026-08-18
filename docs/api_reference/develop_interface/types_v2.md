# types module (v2)
API provided in `types.py` module. This module contains classes for easy interaction. You can also use them as type hints in your code.

v2 reexports all v1 types and adds `ProjectMetadata` and `GraphQLClient`.

## Usage in package API

```python
from git_system_follower.develop.api.v2.types import (
   Parameters, System, ExtraParam, ExtraParams,
   CICDVariable, CICDVariables,
   ProjectMetadata, GraphQLClient
)
```

## Classes description

All v1 classes (`Parameters`, `System`, `ExtraParam`, `ExtraParams`, `CICDVariable`, `CICDVariables`, `Webhook`, `Webhooks`) are identical. See [v1 Types](types_v1.md) for their descriptions.

### `ProjectMetadata` class (v2 only)
```python
class ProjectMetadata(Singleton):
    def initialize(self, description=None, icon=None, cicd_catalog=False) -> 'ProjectMetadata': ...
    @property
    def description(self) -> Optional[str]: ...
    @property
    def icon(self) -> Optional[str]: ...
    @property
    def cicd_catalog(self) -> bool: ...
    @property
    def icon_hash(self) -> str: ...
```
Singleton holder for the project metadata defined in `package.yaml`. Used internally to sync description, icon and the CI/CD catalog to the GitLab project.

!!! warning
    This class is a singleton and is initialized once per run by the core. Don't create your own instances.

### `GraphQLClient` class (v2 only)
```python
class GraphQLClient(Singleton):
    def initialize(self, url: str, token: str) -> 'GraphQLClient': ...
    @property
    def client(self) -> gitlab.GraphQL: ...
```
Singleton wrapper around `gitlab.GraphQL` used for direct GraphQL mutations/queries (e.g. CI/CD catalog operations).

!!! warning
    This class is a singleton and is initialized once per run by the core. Don't create your own instances.
