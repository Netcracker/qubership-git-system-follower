# templates module
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
      1. [types Module](types.md)
      2. [cicd_variables Module](cicd_variables.md)
      3. **[templates Module](templates.md)**

---


API provided in `templates.py` module. This module contains functions for easy interaction with `cookiecutter` templates.

## Usage in package api
```python
from git_system_follower.develop.api.templates import create_template, update_template, delete_template
```

### Examples
```python
from git_system_follower.develop.api.types import Parameters
from git_system_follower.develop.api.templates import create_template, delete_template


def main(parameters: Parameters):
   delete_template(parameters)
   create_template(parameters, 'default')
```

## Functions description
### `getget_template_names` function
```python
def get_template_names(parameters: Parameters) -> tuple[str, ...]:
```
Return tuple of template names 

#### Arguments
| Name            | Type         | Description                                    |
|-----------------|--------------|------------------------------------------------|
| `parameters`    | `Parameters` | parameters that were passed to the package api |

### `create_template` function
```python
def create_template(
    parameters: Parameters, template_name: str, *,
    is_force: bool = False
) -> None:
```
Create files using `cookiecutter` template

If `is_force` parameter is `False`, then it will necessarily be safe to create files using template:
1. If file doesn't exist: create file
2. If file exists:
   1. Files content doesn't match: notification of this (warning)
   2. Files content matches: notification of this (info)

If `is_force` parameter is `True`, then it will necessarily be force to create files using template:
1. If file doesn't exist: create file
2. If file exists:
   1. Files content doesn't match: overwrite this file, notification of this (warning)
   2. Files content matches: notification of this (info)

#### Arguments
| Name            | Type         | Description                                    |
|-----------------|--------------|------------------------------------------------|
| `parameters`    | `Parameters` | parameters that were passed to the package api |
| `template_name` | `str`        | name of template to be created                 |

#### Keyword arguments
| Name       | Type   | Description                           |
|------------|--------|---------------------------------------|
| `is_force` | `bool` | forced creation (ignore file content) |

### `update_template` function
```python
def update_template(
    parameters: Parameters, *, 
    is_force: bool = False
) -> None:
```
Update files using `cookiecutter` template

If `is_force` parameter is `False`, then it will necessarily be safe to update files using template:
1. If file doesn't exist: create file
2. If file exists: do nothing
   1. Files content doesn't match: notification of this (warning)
   2. Files content matches: notification of this (info)

If `is_force` parameter is `True`, then it will necessarily be force to update files using template:
1. If file doesn't exist: create file
2. If file exists:
   1. Files content doesn't match: overwrite this file, notification of this (warning)
   2. Files content matches: notification of this (info)

#### Arguments
| Name            | Type         | Description                                    |
|-----------------|--------------|------------------------------------------------|
| `parameters`    | `Parameters` | parameters that were passed to the package api |

#### Keyword arguments
| Name       | Type   | Description                           |
|------------|--------|---------------------------------------|
| `is_force` | `bool` | forced creation (ignore file content) |

### `delete_template` function
```python
def delete_template(
    parameters: Parameters, *, 
    is_force: bool = False
) -> None:
```
Delete files using `cookiecutter` template

If `is_force` parameter is `False`, then it will necessarily be safe to delete files using template:
1. If file doesn't exist: do nothing
2. If file exists:
   1. Files content doesn't match: notification of this (warning)
   2. Files content matches: delete this file, notification of this (info)

If `is_force` parameter is `True`, then it will necessarily be force to delete files using template:
1. If file doesn't exist: do nothing
2. If file exists:
   1. Files content doesn't match: delete this file, notification of this (warning)
   2. Files content matches: delete this file, notification of this (info)

#### Arguments
| Name            | Type         | Description                                    |
|-----------------|--------------|------------------------------------------------|
| `parameters`    | `Parameters` | parameters that were passed to the package api |


#### Keyword arguments
| Name       | Type   | Description                           |
|------------|--------|---------------------------------------|
| `is_force` | `bool` | forced deletion (ignore file content) |
