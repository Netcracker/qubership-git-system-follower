# Gear Rollback

This guide explains how rollbacks are managed within the system. A rollback involves reverting a component to an older version than the one currently installed.

## Overview of Rollback Mechanics

Rollbacks are handled by identifying the requested version and comparing it against the version currently recorded in `.state.yaml`.

- **Automatic Detection**: When a user requests a version lower than the current one, GSF checks if the transition is "safe" (i.e., whether it can be automatically managed).

### Simple Gear Layout (Single Semantic Version, e.g., 1.0.0)
- **Scripts Directory**: Contains `init.py` for initialization and `delete.py` for deletion.
- **Update Logic**: This transition is straightforward as the target (Complex) supports multi-version structures and `update.py` scripts. These scripts handle complex update scenarios—including clearing existing files and installing new content—ensuring a clean transition from a non-versioned (Simple) state to a versioned (Complex) environment.
- **Layout Structure**:
```text
scripts/
├─ delete.py
├─ init.py
└─ templates/
   ├─ <template>/
   │  ├─ cookiecutter.json
   │  │  └─ {{ cookiecutter.gsf_repository_name }}/
   │  │  └─ <template files>
   │  └─ <other template>
   │  └─ ...
```

### Complex Gear Layout (Multiple Semantic Versions, e.g., 1.0.0 and 1.0.2)
- **Versioned Scripts**: Utilizes a versioned directory structure under `scripts/`.
- **Update Logic**: Relies on `update.py` scripts to manage upgrades between specific versions.
- **Layout Structure**:
```text
scripts/
├─ <version>/
│  ├─ delete.py
│  ├─ init.py
│  ├─ update.py
│  └─ templates/
│  │  ├─ <template>/
│  │  │  ├─ cookiecutter.json
│  │  │  └─ {{ cookiecutter.gsf_repository_name }}/
│  │  │  └─ <template files>
│  │  └─ <other template>
│  │     └─ ...
│  └─ <next version>/
│    └─ ...
```


## Rollback Logic

The system determines how to perform a rollback based on the availability of metadata about the currently installed gear.

### Standard Rollback
When no special flags are provided (or `is_skip_force_rollback` is false), GSF performs a forced installation of the target version.

- **Mechanism**: Forced reinstallation (`init(..., is_force=True)`). 
- **Process**: The system skips the detailed comparison of differences between versions and directly installs the requested version. This approach is faster but does not guarantee a "safe" transition as it does not explicitly purge assets from higher versions before installing lower ones.
- **Example**: From Complex to Simple rollback here it would directly run init.py for Simple gear 1.0.0

### Safe Rollback (via `--skip-force-rollback`)
In cases where specific conditions require it, the `--skip-force-rollback` flag can be used to ensure a safe transition when standard force-install shortcuts aren't sufficient.

- **Mechanism**: Explicit transition via deletion and initialization.
- **Process**: When `--skip-force-rollback` is enabled, GSF performs a "safe" rollback by first executing a full deletion of the current assets before initiating the target version. This ensures that all differences are accounted for by explicitly clearing the environment before re-applying the desired configuration.
- **Example**: From Complex to Simple rollback here it would run delete.py of 1.0.2 of Complex gear and then run init.py for Simple gear 1.0.0
---

## Troubleshooting Rollback Issues

If a rollback cannot be performed automatically (e.g., "Rollback validation skipped" or "source missing"), it usually means the current installation was performed without full source tracking.

**How to fix:**
1. **Re-establish Source**: Re-run the `install` command using the currently installed gear's direct path or registry link. This updates `.state.yaml` with the correct metadata.
2. **Retry Rollback**: Once the source is properly tracked, subsequent rollbacks to older versions will be automatically supported by the system.

---

## Comparison Summary

| Feature | Standard Rollback (Default) | Safe Rollback (`--skip-force-rollback`) |
| :--- | :--- | :--- |
| **Requirement** | No special flags provided | `--skip-force-rollback` flag is used |
| **Mechanism** | Force Install (`init(is_force=True)`) | Delete then Init |
| **Safety** | Lower; does not purge old assets | Higher; ensures a clean state via full delete |
| **Use Case** | Standard operation to revert a change | Required when a "safe" transition is needed or source tracking is missing or not an image |

---

## Best Practices
- Always ensure your gear is installed with full source information (default behavior) to enable seamless rollbacks.
- Use `--skip-force-rollback` only when you unsure of the target state or have a source that's not an image and need to guarantee a clean environment by purging existing assets using `delete.py` that comes with the gears before re-installing.