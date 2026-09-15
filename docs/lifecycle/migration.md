# Gear Migration

## Introduction

This guide outlines the procedures for migrating between different gear types (Simple -> Complex) and (Complex -> Simple). 

**Note:** Gear type migration is typically an infrequent event—usually occurring only once or twice in the lifecycle of a project's configuration.

**Note on Force Flag**: The `--force` flag is specifically designed for use during migrations to handle scenarios where intermediate versions might be missed; because forced actions bypass automatic validation, they require manual verification of the final state.

**Common Reasons for Migration:**
- **Scaling Requirements (Simple -> Complex)**: Moving to a complex structure when a project requires support for multi-version management and advanced deployment paths.
- **Architectural Simplification (Complex -> Simple)**: Transitioning to a simple structure when a project no longer requires multi-version tracking or is being consolidated into a single release path.
- **Standardization**: Consolidating projects under a unified standard (either complex or simple) to ensure consistent maintenance and lifecycle management across the organization.

**Automatic Detection:** GSF automatically detects migration scenarios and provides a "nudge" or prompt, reminding users to include the `--force` flag in subsequent `gsf install` commands to finalize the transition.

### Simple Gear Layout (Single Semantic Version, e.g., 1.0.0)
- **Scripts Directory**: Contains `init.py` for initialization and `delete.py` for deletion.
- **Update Logic**: This transition is straightforward as the target (Complex) supports multi-version structures and `update.py` scripts. These scripts handle complex update scenarios—including clearing existing files and installing new content—ensuring a clean transition from a non-versioned (Simple) state to a versioned (Complex) environment.
- **Layout Structure**:
```text
scripts/
├─ delete.py
├─ init.py
├─ templates/     (optional)
│  ├─ <template>/
│  │  ├─ cookiecutter.json
│  │  │  └─ {{ cookiecutter.gsf_repository_name }}/
│  │  │  └─ <template files>
│  │  └─ <other template>
│  │  └─ ...
└─ files/         (optional: static files)
   └─ <template>/
      └─ ...
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
│  ├─ templates/  (optional)
│  │  ├─ <template>/
│  │  │  ├─ cookiecutter.json
│  │  │  └─ {{ cookiecutter.gsf_repository_name }}/
│  │  │  └─ <template files>
│  │  └─ <other template>
│  │     └─ ...
│  └─ files/      (optional: static files)
│     └─ <template>/
│        └─ ...
└─ <next version>/
   └─ ...
```

See [Static files](../how_to/gear_development_cases.md#static-files) for static file placement and behavior during migration.

## Migration Types

Depending on the migration path, follow the logic outlined below:

### Simple to Complex Migration
This transition is straightforward as the target (Complex) supports multi-version structures and `update.py` scripts. These scripts handle complex update scenarios—including clearing existing files and installing new content—ensuring a clean transition from a non-versioned (Simple) state to a versioned (Complex) environment.

- **Simple Gear 1.0.0**:
```text
scripts/
├─ delete.py
├─ init.py
├─ templates/     (optional)
│  ├─ <template>/
│  │  ├─ cookiecutter.json
│  │  │  └─ {{ cookiecutter.gsf_repository_name }}/
│  │  │  └─ <template files>
│  │  └─ <other template>
│  │  └─ ...
└─ files/         (optional: static files)
   └─ <template>/
      └─ ...
```

- **Complex Gear (v1.0.0, v1.0.2)**:
The structure below applies to all versioned folders in a complex setup (e.g., 1.0.0 and 1.0.2). The presence of `update.py` ensures that transition steps can be executed across different version points:
```text
scripts/
├─ 1.0.0/
│  ├─ delete.py
│  ├─ init.py
│  ├─ update.py
│  ├─ templates/  (optional)
│  │  ├─ <template>/
│  │  │  ├─ cookiecutter.json
│  │  │  └─ {{ cookiecutter.gsf_repository_name }}/
│  │  │  └─ <template files>
│  │  └─ <other template>
│  │     └─ ...
│  └─ files/      (optional: static files)
│     └─ <template>/
│        └─ ...
├─ 1.0.1/
│  ├─ delete.py
│  ├─ init.py
│  ├─ update.py
│  └─ templates/
├─ 1.0.2/
│  ├─ delete.py
│  ├─ init.py
│  ├─ update.py
│  └─ templates/
```

**Migration Flow:**
[Source: v1.0.0] -> [Step: Identify Target v1.0.2] -> [Action: Run `update.py` for 1.0.0, 1.0.1 & 1.0.2] -> [Target: Complex]
- **Action**: Execute the `update.py` script at each step to bridge version gaps and ensure a comprehensive transition from a non-versioned (Simple) state to a versioned (Complex) environment.

### Complex to Simple Migration
This migration transitions from a multi-versioned structure to a non-versioned one. Since the target is a "Simple" gear, it does not require intermediate update steps between internal versions. Note: while `init.py` flattens the structure, users should verify that no remnants remain from previous versions.

- **Complex Gear (v1.0.0, v1.0.2)**:
The structure below applies to all versioned folders in a complex setup (e.g., 1.0.0 and 1.0.2). The presence of `update.py` ensures that transition steps can be executed across different version points:
```text
scripts/
├─ 1.0.0/
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
```

- **Simple Gear 1.0.2**:
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

**Migration Flow:**
[Source: Complex (v1.0.0, v1.0.2)] -> [Step: Target Configuration Setup] -> [Action: Run `init.py` on Target Configuration] -> [Target: Simple (v1.0.2)]

- **Action**: Perform an `init` operation on the target configuration. Since a "Simple" configuration only recognizes a single version, users must manually verify that no artifacts or files from previous version paths (e.g., 1.0.1) remain in the directory after the operation.