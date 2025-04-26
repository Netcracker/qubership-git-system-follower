# templates module
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
### `get_template_names` function
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
