# types module
API provided in `types.py` module. This module contains classes for easy interaction. You can also use them as type hints in your code.

## Usage in package api

```python
from git_system_follower.develop.api.types import (
   Parameters, System, ExtraParam, ExtraParams, 
   CICDVariable, CICDVariables
)
```

## Classes description
### `Parameters` class
```python
@dataclass(frozen=True)
class Parameters:
    system: System
    workdir: Path
    extras: ExtraParams
    cicd_variables: CICDVariables
    all_cicd_variables: CICDVariables
    used_template: str
```
Parameters which git-system-follower passed to package api

!!! warning
    This class is only used to transfer information. Don't create your own instances

#### Fields
| Name                 | Type                          | Description                                                                                                                 |
|----------------------|-------------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| `system`             | `System`                      | system information                                                                                                          |
| `workdir`            | `Path` from `pathlib` library | current work directory                                                                                                      |
| `extras`             | `ExtraParams`                 | extra parameters which have been passed in git-system-follower                                                             |
| `cicd_variables`     | `CICDVariables`               | CI/CD variables that wew created by previous gear version                                                                     |
| `all_cicd_variables` | `CICDVariables`               | all CI/CD variables that exist in repository                                                                                |
| `used_template`      | `str`                         | last used template. If `used_template=None` then no template has been used. If template has been deleted, it will be `None` |

### `System` class
```python
@dataclass(frozen=True)
class System:
    host_domain: str
```
System information about instance in which gear installed/uninstalled

!!! warning
    This class is only used to transfer information. Don't create your own instances

#### Fields
| Name          | Type  | Description                          |
|---------------|-------|--------------------------------------|
| `host_domain` | `str` | host domain, e.g. `your.company.com` |

### `ExtraParam` class
```python
class ExtraParam(NamedTuple):
    name: str
    value: str
    masked: bool
```
Extra parameter information

#### Fields
| Name     | Type   | Description                               |
|----------|--------|-------------------------------------------|
| `name`   | `str`  | extra parameter name                      |
| `value`  | `str`  | extra parameter value                     |
| `masked` | `bool` | whether to mask a extra parameter in logs |

### `ExtraParams` class
```python
ExtraParamName = str
ExtraParams = dict[ExtraParamName, ExtraParam]
```
Extra parameters which have been passed in git-system-follower as `--extra <name> <value> <masked/no-masked>`

This is `dict` where key is parameter name, value is `ExtraParam`

### `CICDVariable` class

```python
class CICDVariable(TypedDict):
    name: str
    value: str
    env: str
    masked: bool
```
CI/CD variable information 

#### Fields
| Name     | Type   | Description                                                                                               |
|----------|--------|-----------------------------------------------------------------------------------------------------------|
| `name`   | `str`  | CI/CD variable name                                                                                       |
| `value`  | `str`  | CI/CD variable value                                                                                      |
| `env`    | `str`  | Gitlab environment (see [Gitlab Environments documentation](https://docs.gitlab.com/ee/ci/environments/)) |
| `masked` | `bool` | whether to mask a CI/CD variable in logs and in Gitlab                                                    |

### `CICDVariables` class

```python
CICDVariableName = str
CICDVariables = dict[CICDVariableName, CICDVariable]
```
CI/CD variables information

This is `dict` where key is CI/CD variable name, value is `CICDVariable` 