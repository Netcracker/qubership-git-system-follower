# Gear
## Documentation
1. [Docs Home](../docs_home.md)
2. [Getting Started Guides](../getting_started.md) 
   1. [Quickstart Guide](../getting_started/quickstart.md)
   2. [Installation Guide](../getting_started/installation.md)
3. [Concepts Guides](../concepts.md) 
   1. **[Gears Guide](gears.md)**
   2. [apiVersion list](api_version_list.md)
      1. [apiVersion v1](api_version_list/v1.md) 
   3. [.state.yaml Guide](state.md)
4. [How-to Guides](../how_to.md)  
   1. [Build Guide](../how_to/build.md)
   2. [Gear Development Cases](../how_to/gear_development_cases.md)
   3. [Integration with semantic-release](../how_to/integration_with_semantic_release.md)
5. [CLI reference](../cli_reference.md) 
   1. [download](../cli_reference/download.md)
   2. [install](../cli_reference/install.md) 
   3. [list](../cli_reference/list.md)
   4. [uninstall](../cli_reference/uninstall.md)
   5. [version](../cli_reference/version.md)
6. [API reference](../api_reference.md)  
   1. [Develop interface](../api_reference/develop_interface.md)  
      1. [types Module](../api_reference/develop_interface/types.md)
      2. [cicd_variables Module](../api_reference/develop_interface/cicd_variables.md)
      3. [templates Module](../api_reference/develop_interface/templates.md)

---

git-system-follower uses a packaging format called Gear. Gear is a collection of files describe the variables and structure of files in a repository.

Gears are created as files laid out in a particular directory tree. They can be packaged into archives, docker images (is scheduled to be converted to an OCI image).

## The Gear file structure
A Gear is organized as a collection of files in the `git-system-follower-package/` directory inside your project.

Inside of this directory, git-system-follower will expect a structure that matches this:
```text
git-system-follower-package/
  package.yaml  # A .yaml file containing information about Gear
  scripts/      # A directory with package API
```

## The package.yaml file
The `package.yaml` is required for a Gear. It contains the following fields:
```yaml
apiVersion: The Gear API version (required)
type: The type of the Gear (required)
name: The name of the Gear (required)
version: The version of the Gear (required)
dependencies: # A list of the Gear requirements (optional)
  - Docker image of another package
  - Another docker image of another package
```

### Gears and Versioning
Every Gears must have a version number. A version must follow TBD

### The `apiVersion` field
`apiVersion` field allows git-system-follower to understand which version of this Gear

You can check [available `apiVersion` list](api_version_list.md)

### The `type` field
`type` field allows git-system-follower to understand how work with this Gear

### The `name` field
`name` field allows git-system-follower to uniquely identify the Gear. Acceptable characters: letter, digits, `.`, `-`, `_`

### Gears dependencies
One gear may depend on any number of other gears. To add a dependency, it must be specified as a docker image in the `dependencies` section.

## The package API (`scripts/` directory)


### `scripts/` file structure
The file structure contains version directories with python scripts and cookiecutter templates
```text
scripts/
├─ <version>/
│  ├─ delete.py
│  ├─ init.py
│  ├─ update.py
│  └─ templates/
│     ├─ <template>/
│     │  ├─ cookiecutter.json
│     │  └─ {{ cookiecutter.gsf_repository_name }}/
│     │     └─ <template files>
│     └─ <other template>
│        └─ ...
└─ <next version>/
   └─ ...
```

### python scripts
scripts are used for different scenarios:
1. git-system-follower uses `init.py` for initialization in the repository.
2. git-system-follower uses `delete.py` for deletion in the repository.
3. git-system-follower uses `update.py` to update in the repository.
4. git-system-follower uses (TBD: to rollback or force-forward) in the repository.

All of these scripts may use develop interface for to work with Gear in the repository provided by git-system-follower.
You can use it from `from git_system_follower.develop.api` like this:

```python
from git_system_follower.develop.api.types import Parameters
from git_system_follower.develop.api.cicd_variables import CICDVariable, create_variable
from git_system_follower.develop.api.templates import create_template
```

For more details on how to develop your package api, see [API reference](../api_reference.md)

If you don't want to work with CI/CD variables, but only to create template(s), 
you may not create init.py, delete.py, default functions will be used for them.

Default `init.py`:
```python
def main(parameters: Parameters):
    templates = get_template_names(parameters)
    if not templates:
        raise ValueError('There are no templates in the package')

    if len(templates) > 1:
        template = parameters.extras.get('TEMPLATE')
        if template is None:
            raise ValueError('There are more than 1 template in the package, '
                             'specify which one you want to use with the TEMPLATE variable')
    else:
        template = templates[0]

    variables = parameters.extras.copy()
    variables.pop('TEMPLATE', None)
    create_template(parameters, template, variables)
```
this default checks for the presence of templates:
1. if there are no templates, it will generate an error,
2. if there is one template, it will apply it,
3. if there is more than one template, a `TEMPLATE` variable is needed so that git-system-follower can figure out which template to apply.

Also, all variables passed with `--extra` will be passed to the template.

Default `delete.py`:
```python
def main(parameters: Parameters):
    delete_template(parameters)
```
In this default only template deletion is called. 
git-system-follower does not require any additional information, since it stores information
about the generated template in `.state.yaml`.

For more details about `.state.yaml`, see [.state.yaml Guide](state.md)

### `cookiecutter` templates
`cookiecutter` is used to generate templates. For creating templates, see [cookiecutter documentation](https://cookiecutter.readthedocs.io/en/latest/)

The only additional thing required for git-system-follower is to name the template root directory `{{ cookiecutter.gsf_repository_name }}`
and add `gsf_repository_name` section with an empty value (`""`) in `cookiecutter.json` file:
```json
{
  "gsf_repository_name": ""
}
```

P.S. Even if you don't need templates, but just copy files, still use `cookiecutter` with regular files for this purpose

You can use variables that have been passed as extra parameters to git-system-follower. For example, you can use parameter,
which have been passed to git-system-follower as `--extra VAR_NAME VAR_VALUE no-masked`, in template as `{{ cookiecutter.VAR_NAME }}`

## Build Gear
The gear is built into a docker image for future use and distibution.

For more details on how to build you gear, see [build gear](../how_to/build.md)

## Final repository file structure with gear
```text
<your repository>
├─ git-system-follower-package/
│  ├─ package.yaml
│  └─ scripts/
│     ├─ <version>/
│     │  ├─ delete.py
│     │  ├─ init.py
│     │  ├─ update.py
│     │  └─ templates/
│     │     ├─ <template>/
│     │     │  ├─ cookiecutter.json
│     │     │  └─ {{ cookiecutter.gsf_repository_name }}/
│     │     │     └─ <template files>
│     │     └─ <other template>
│     │        └─ ...
│     └─ <next version>/
│        └─ ...
├─ Dockerfile        # for build git-system-follower package
└─ <your other files>
```

## Advanced
### Why package being built as a docker image
The build process is docker image oriented because docker images are easy to build and transport

### How version is updated
git-system-follower sequentially installs all version that stand between versions A and B, where A is version currently installed,
B is version we want to upgrade to

Example:
* `1.0.0` version installed
* We want to install `1.4.0` version
* There are five version between them: `1.1.0`, `1.2.0`, `1.2.1`, `1.2.2`, `1.3.0`

In this case, the update will be as follows: 
1. use `update.py` of `1.1.0` version
2. use `update.py` of `1.2.0` version
3. use `update.py` of `1.2.1` version
4. use `update.py` of `1.2.2` version
5. use `update.py` of `1.3.0` version
6. use `update.py` of `1.4.0` version

Each new version keeps the scripts of older versions, so git-system-follower won't download all those version, only latest (`1.4.0`)

### Package size will grow because of scripts, what to do about it
After some time you will realize that some versions will no longer be used/supported, update your package in your repositories and you
will be able to remove scripts of irrelevant version from new version

### Template generation work in package api
Template is generated in the temp directory (`/tmp/`) with `gsf-package-manager-...` name (where `...` is a bunch of different letters and numbers)
and then files are copied to local repository directory. This is so that if we have identical files, we can compare their contents for careful template generation