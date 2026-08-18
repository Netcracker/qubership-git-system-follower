# templates module (v2)
API provided in `templates.py` module. This module contains functions for easy interaction with `cookiecutter` templates.

v2 extends the v1 template functions with **automatic project metadata synchronization** on create/update/delete.

## Usage in package API
```python
from git_system_follower.develop.api.v2.templates import create_template, update_template, delete_template
```

### Examples
```python
from git_system_follower.develop.api.v2.types import Parameters
from git_system_follower.develop.api.v2.templates import create_template, delete_template


def main(parameters: Parameters):
   delete_template(parameters)
   create_template(parameters, 'default')
```

## Functions description

The signatures of `get_template_names`, `create_template`, `update_template`, `delete_template` are identical to v1.
See [v1 Templates](templates_v1.md) for the full function reference.

## v2-specific behavior

Unlike v1, the v2 `create_template` and `update_template` functions **automatically synchronize project metadata**
from `package.yaml` after the template is applied:

* **Project description** – set from the `description` section.
* **Project icon (avatar)** – uploaded from the file referenced by `icon` (resolved relative to the `scripts/` directory of the executed version).
* **CI/CD catalog** – enabled/disabled by passing the `--extra gitlab_cicd_project_catalog <true|false> <masked|no-masked>` extra parameter.

The synchronized metadata is recorded in the `PACKAGE_API_RESULT` file under `project_metadata`
and is written to the `.state.yaml` `project_metadata` section.
