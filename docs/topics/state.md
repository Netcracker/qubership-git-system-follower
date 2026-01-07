# .state.yaml
git-system-follower stores state in the `.state.yaml` file at the root of the repository.

git-system-follower hashes values in the `.state.yaml` to prevent unauthorized changes or misuse and
masks template variable values

## The `.state.yaml` structure
```yaml
hash: Hash of 'packages' section
packages: # List of installed packages
- cicd_variables: # Section of created CI/CD variables
    hash: Hash of 'names' section
    names: # Name list of created CI/CD variables
      - Name of CI/CD variable
      - Name of another CI/CD variable
      - etc
  dependencies: # List of dependencies of this package
    - 'dependency-name@dependency-version'
    - 'another-dependency-name@another-dependency-version'
  last_update: Date in 'YYYY-MM-DD HH:MM:SS.ffffff' format
  name: Gear name
  template_variables: # Section of used variables to create template
    variable_name: Masked Base64-encoded value
    another_variable_name: Masked Base64-encoded value
  used_template: Installation template used
  version: Gear version
```

### `.packages` section
This is a list of installed packages in the current branch, all packages have the following structure:
```yaml
- cicd_variables: Section of created CI/CD variables
  dependencies: List of dependencies of this package
  last_update: Date in 'YYYY-MM-DD HH:MM:SS.ffffff' format
  name: Gear name
  template_variables: Section of used variables to create template
  used_template: Installation template used
  version: Gear version
```

### `.packages.cicd_variables` section
This section contains the names of the variables that resolves at run time of the git-system-follower. 
The list of names is hashed to avoid manual modification of the `.state.yaml` file or the variables themselves.
```yaml
hash: Hash of 'names' section
names:
  - Name of CI/CD variable
  - Name of another CI/CD variable
  - etc
```

### `.packages.dependencies` section
In `.state.yaml`, dependencies are listed in the `dependencies` section as `name@version`. The details of each
dependency-package are described separately. 
This makes the structure more readable and simplifies dependency management.

For example, we have package `my-second-gear@1.0.0` with dependency `my-first-gear@2.0.0`.
It will be specified as follows:
```yaml
hash: ...
packages:
- cicd_variables: ...
  dependencies:
    - 'my-first-gear@2.0.0'
  last_update: ...
  name: my-second-gear
  template_variables: ...
  used_template: ...
  version: 1.0.0
- cicd_variables: ...
  dependencies: []
  last_update: ...
  name: my-first-gear
  template_variables: ...
  used_template: ...
  version: 2.0.0
```

### `.packages.last_update` section
This section contains the date of the last change in the format `YYYY-MM-DD HH:MM:SS.ffffff`. 
The field is for informational purposes only and does not affect functionality.

### `.packages.name` and `.packages.version` sections
These sections contain information from `package.yaml` in Gear

### `.packages.template_variables` section
This is where the variables that were passed by the package developer to the template generation are stored. 
This is to avoid having to remember and pass these variables again when the package is deleted.

!!! warning

    Variable values are masked in `base64` encoding only, not encrypted.

how to see the values of variables:
```bash
echo "<variable value>" | base64 -d 
```

### `.packages.used_template` section
This section specifies which template was used when the package was installed
