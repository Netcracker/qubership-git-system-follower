# Gear Lifecycle

## Structure Types

gsf auto-detects gear structure by checking `scripts/` directory.

/// html | div[style='float: left; width: 48%;']
Complex / has versioned subdirectories:
```
scripts/
├─ 1.0.0/
│  ├─ init.py
│  ├─ update.py
│  ├─ delete.py
│  └─ templates/
└─ 2.0.0/
   └─ ...
```
///

/// html | div[style='float: right;width: 4%;']
///

/// html | div[style='float: right;width: 48%;']
Simple / no version subdirectories:
```
scripts/
├─ init.py
├─ delete.py
└─ templates/
```
///

/// html | div[style='clear: both;']
///

Tries to parse directory names as versions: successful → complex, otherwise → simple.  

For more details about the file structure, see [the package API (`scripts/` directory)](../gears.md#the-package-api-scripts-directory)

## Installation

Before installation, gsf tries to determine whether the current gear (from `package.yaml`) is already installed in the repository. It does this by reading `.state.yaml`, a file that maintains information about installed gears. gsf checks for matching entries by both the gear name and version.

- If a matching (name & version) entry exists in `.state.yaml`, gsf considers the gear already installed.
- [First installation](#first-installation): if `.state.yaml` is missing or empty, gsf considers that no gears are installed in the repository.
- [Upgrade](#upgrade) / [Downgrade](#downgrade): if there is a matching name but version does not match, gsf considers it an upgrade / downgrade scenario.

This check ensures correct installation/upgrade logic and prevents redundant operations.

### First installation

The gear installation process starts with structure detection (whether the gear is a simple type using `scripts/`, or complex with versioned subdirectories). Based on that, gsf finds and executes the correct `init.py` script, passing the repository path as the working directory. The internals of `init.py` will interact with the template engine to generate files as defined by the gear specification.

Once initialization completes, gsf records metadata about the installed gear to `.state.yaml`. This entry is later used by gsf to determine gear status for upgrades, consistency checks, or uninstall actions.

These internal steps ensure the installed files match gear expectations and that gear state tracking can support future lifecycle operations.

### Upgrade

Upgrade scenario detection:

* **Complex structure** upgrade uses `update.py` scripts between versions for sequential upgrades. Ex. from `v1` to `v3` like `v1` -> `v2` -> `v3`
* **Simple structure** upgrade uses same `init.py` with `is_force=True` flag. This re-runs initialization which overwrites files. Ex. from `v1` to `v3` like `v1` -> `v3`

For upgrading we are using [3-Way Merge](#3-way-merge).

### Downgrade

Not implemented yet

### 3-Way Merge

We use an approach similar to a 3-way merge when working with two gear versions (for upgrade/downgrade). There are three main objects involved:

1. Base: the `v1` version of the gear - this is the common ancestor, representing the previous (currently installed) version in the repository.
2. Source: the `v2` version of the gear - the new version we want to install into the repository.
3. Target: the current state of the repository - which may contain user changes and is where we aim to apply the new (Source) version.

gsf clones the repository (target) and generates two versions of the gear in a temporary directory (`/tmp`):

* `v1` (base): generated using the variables from the `packages[].template_variables` field in `.state.yaml`, i.e., with the variables that were used during the previous installation of the current (old) version of the gear.
* `v2` (source): generated using the variables obtained from the package API of the new gear version.

Then, gsf compares the files between the base (`v1`) and the target (the current repository). If the files differ, it means the user has made changes (user changes). This way, gsf determines the list of files that were not modified by the user. These files can be replaced: for them, new versions from `v2` (source) are taken and updated in the target repository. User changes are not overwritten.

## Deletion

Before deleting a gear, gsf determines the type of structure (simple or complex) and locates the corresponding scripts directory. It then executes the `delete.py` script from the gear package, setting the repository as the working directory. The `delete.py` script uses the templates API to identify which files should be deleted. To decide which files to remove, gsf generates templates in a temporary directory and compares their hashes to those of files in the repository. Files that match the original template and have not been modified by the user are deleted, while user-modified files are preserved. After completing the deletion process, gsf removes the gear’s entry from `.state.yaml` to update the state of installed packages.

## State Management

File `.state.yaml` tracks installed packages:

```yaml
packages:
  - name: my-package
    version: "2.0.0"
    structure_type: simple
    used_template: "default"
    template_variables: {...}
```

State updates:

- Install: adds package entry
- Upgrade: updates version and template_variables fields
- Delete: removes package entry

For more details about `.state.yaml` structure, see [`.state.yaml` Guide](../state.md).