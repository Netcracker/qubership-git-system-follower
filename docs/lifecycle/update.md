# Gear Updates

This guide explains how updates are managed within different gear types: **Simple** and **Complex**. Understanding these differences is crucial for correctly applying changes to your configuration's logic and assets.

## Overview of Update Mechanics

The primary difference between Simple and Complex gears lies in how they handle versioning and progression. 

- **Simple Gear**: Designed for a single, non-versioned state. "Updating" involves moving the entire project to a new unified state.
- **Complex Gear**: Designed for multi-version management. "Updating" involves transitioning through specific versioned steps using specialized scripts.

### Simple Gear Layout (Single Semantic Version, e.g., 1.0.2)
- **Scripts Directory**: Contains `init.py` for initialization and `delete.py` for deletion.
- **Update Logic**: Since the structure is flat, updates are handled as direct transitions. While it does not require navigating multiple versions via `update.py` scripts, it still ensures that content is correctly cleared and replaced during the update process.
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

See [Static files](../how_to/gear_development_cases.md#static-files) for static file placement and behavior during updates.


## Simple Gear Updates

In a **Simple** gear configuration, there is no internal versioning system (e.g., only one directory structure). 

### Update Logic
Because the structure is flat and does not support multiple versions, an update in a Simple gear is treated as a direct transition to a new state.
An update to a higher version in a Simple gear configuration is processed as an initial installation (init) of that specific version.

- **Mechanism**: Direct replacement or modification of the existing components.
- **Process**: Since there are no "intermediate" version paths to navigate through, any change accepted by the system moves the entire configuration from its current state directly into the new state.
- **Note**: While `init.py` and `delete.py` are present in the scripts directory, they are used for initial setup or removal rather than navigating between versions within the same configuration.

---

## Complex Gear Updates

In a **Complex** gear configuration, the structure is built to support multiple versioned segments (e.g., 1.0.0, 1.0.1, 1.0.2). This allows for granular control over upgrades.

### Update Logic
Updates in Complex gears rely on the `update.py` scripts located within each version's directory to move between specific points.

- **Mechanism**: Sequential navigation through versioned folders.
- **Process**: To update from one version (e.g., 1.0.0) to another (e.g., 1.0.2), the system identifies the target and executes `update.py` scripts for each leap in the chain.
- **Key Components**:
  - **Versioned Folders**: Each folder (1.0.0, 1.0.1, etc.) contains its own `init.py`, `delete.py`, and `update.py`.
  - **`update.py`**: This is the primary tool for "hopping" between versions. It ensures that file contents are correctly cleared or replaced as you move forward in the progression.

---

## Comparison Summary

| Feature | Simple Gear Update | Complex Gear Update |
| :--- | :--- | :--- |
| **Structure** | Single/Flat | Multi-versioned / Segmented |
| **Navigation** | Direct transition to target state | Sequential navigation via `update.py` |
| **Complexity** | Lower; intended for direct replacements | Higher; supports phased rollouts and transitions |
| **Core Scripts** | `init.py`, `delete.py` | `init.py`, `delete.py`, `update.py` |

---

## Best Practices
- For **Simple** gears, ensure that the target state is fully defined before performing an update to avoid leaving the configuration in an inconsistent state.
- For **Complex** gears, always verify the current version folder you are departing from and the target destination before executing `update.py` sequences.