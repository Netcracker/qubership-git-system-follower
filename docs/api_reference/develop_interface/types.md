# types module
## Documentation
1. [Docs Home](../../docs_home.md)
2. [Getting Started Guides](../../getting_started.md) 
   1. [Quickstart Guide](../../getting_started/quickstart.md)
   2. [Installation Guide](../../getting_started/installation.md)
3. [Concepts Guides](../../concepts.md)  
   1. [Gears Guide](../../concepts/gears.md)
   2. [apiVersion list](../../concepts/api_version_list.md)
      1. [apiVersion v1](../../concepts/api_version_list/v1.md) 
   3. [.state.yaml Guide](../../concepts/state.md)
   4. [Plugins Guide](../../concepts/plugins.md)
      1. [CLI Arguments Extension Point](../../concepts/plugins/cli_arguments.md)
4. [How-to Guides](../../how_to.md)  
   1. [Build Guide](../../how_to/build.md)
   2. [Gear Development Cases](../../how_to/gear_development_cases.md)
   3. [Integration with semantic-release](../../how_to/integration_with_semantic_release.md)
5. [CLI reference](../../cli_reference.md)
   1. [download](../../cli_reference/download.md)
   2. [install](../../cli_reference/install.md) 
   3. [list](../../cli_reference/list.md)
   4. [uninstall](../../cli_reference/uninstall.md)
   5. [version](../../cli_reference/version.md)
6. [API reference](../../api_reference.md)  
   1. [Develop interface](../develop_interface.md)
      1. **[types Module](types.md)**
      2. [cicd_variables Module](cicd_variables.md)
      3. [templates Module](templates.md)

---

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

:exclamation: This class is only used to transfer information. Don't create your own instances

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

:exclamation: This class is only used to transfer information. Don't create your own instances

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