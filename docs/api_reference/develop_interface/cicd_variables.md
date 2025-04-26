# cicd_variables module
API provided in `cicd_variables.py` module. This module contains functions for easy interaction with CI/CD variables.

!!! warning
      When you want to mask a variable, follow [Gitlab Mask a CI/CD variable rules](https://docs.gitlab.com/ee/ci/variables/#mask-a-cicd-variable)

## Usage in package api

```python
from git_system_follower.develop.api.cicd_variables import create_variable, delete_variable
```

### Examples

```python
from git_system_follower.develop.api.types import Parameters
from git_system_follower.develop.api.cicd_variables import CICDVariable, create_variable, delete_variable


def main(parameters: Parameters):
    delete_variable(parameters, parameters.cicd_variables['KUBE_TOKEN'])
    create_variable(parameters, CICDVariable(name='KUBE_TOKEN', value='new_kubernetes_token', env='*', masked=True))
```

## Functions description
### `create_variable` function
```python
def create_variable(
    parameters: Parameters, variable: CICDVariable, *, 
    is_force: bool = False
) -> RESTObject | None
```
Create CI/CD variable using gitlab REST API

If `is_force` parameter is `False`, then it will necessarily be safe to create CI/CD variable:

1. If CI/CD variable doesn't exist: create CI/CD variable
2. If CI/CD variable exists:
      1. CI/CD variables values doesn't match: notification of this (warning)
      2. CI/CD variables values matches: notification of this (info)

If `is_force` parameter is `True`, then it will necessarily be force to create CI/CD variable:

1. If CI/CD variable doesn't exist: create CI/CD variable
2. If CI/CD variable exists:
      1. CI/CD variables values doesn't match: overwrite this CI/CD variable, notification of this (warning)
      2. CI/CD variables values content matches: notification of this (info)

#### Arguments
| Name         | Type           | Description                                    |
|--------------|----------------|------------------------------------------------|
| `parameters` | `Parameters`   | parameters that were passed to the package api |
| `variable`   | `CICDVariable` | CI/CD variable to be created                   |

#### Keyword arguments
| Name       | Type   | Description                             |
|------------|--------|-----------------------------------------|
| `is_force` | `bool` | forced creation (ignore variable value) |

#### Returns
Creation response if variable is created (`RESTObject` class from `gitlab.base`. `gitlab` - `python-gitlab` python library)

### `delete_variable` function
```python
def delete_variable(
    parameters: Parameters, variable: CICDVariable, *, 
    is_force: bool = False
) -> None
```
Delete CI/CD variable using gitlab REST API

If `is_force` parameter is `False`, then it will necessarily be safe to delete CI/CD variable:

1. If CI/CD variable doesn't exist: do nothing
2. If CI/CD variable exists:
      1. CI/CD variables values doesn't match: notification of this (warning)
      2. CI/CD variables value matches: delete this CI/CD variable, notification of this (info)

If `is_force` parameter is `True`, then it will necessarily be force to delete CI/CD variable:

1. If CI/CD variable doesn't exist: do nothing
2. If CI/CD variable exists:
      1. CI/CD variables values doesn't match: delete this file, notification of this (warning)
      2. CI/CD variables values matches: delete this file, notification of this (info)
   

#### Arguments
| Name         | Type           | Description                                    |
|--------------|----------------|------------------------------------------------|
| `parameters` | `Parameters`   | parameters that were passed to the package api |
| `variable`   | `CICDVariable` | CI/CD variable to be deleted                   |

#### Keyword arguments
| Name       | Type   | Description                             |
|------------|--------|-----------------------------------------|
| `is_force` | `bool` | forced deletion (ignore variable value) |

#### Returns
`None`

## Advanced
`is_force` is calculated inside functions as follows: if git-system-follower is run with `--force` option or if `is_force=True` is passed to function,
then these functions will work in force mode
