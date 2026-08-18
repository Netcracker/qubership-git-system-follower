# cicd_variables module (v2)
API provided in `cicd_variables.py` module. This module contains functions for easy interaction with CI/CD variables.

The v2 API is identical to v1 — only the import path differs.

## Usage in package API

```python
from git_system_follower.develop.api.v2.cicd_variables import create_variable, delete_variable
```

### Examples

```python
from git_system_follower.develop.api.v2.types import Parameters
from git_system_follower.develop.api.v2.cicd_variables import CICDVariable, create_variable, delete_variable


def main(parameters: Parameters):
    delete_variable(parameters, parameters.cicd_variables['KUBE_TOKEN'])
    create_variable(parameters, CICDVariable(name='KUBE_TOKEN', value='new_kubernetes_token', env='*', masked=True))
```

## Functions description

See [v1 CI/CD Variables](cicd_variables_v1.md) for the full function reference (`create_variable`, `delete_variable`). Signatures and behavior are identical.
