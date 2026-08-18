# Build Gear (v2)

How to build your project as a Gear with `apiVersion: v2`.

v2 is a strict superset of v1. Building and publishing is the same as for
[v1](build_v1.md) — only the `package.yaml` file has additional sections.

## Docker image with artifact

### `Dockerfile` file

This simply requires you to put the gear in the image:

```Dockerfile
FROM scratch

LABEL gsf.package="true"

COPY git-system-follower-package /git-system-follower-package
```

Build & publish your Gear:

```bash
docker build -t <image>:<tag> .
docker push <registry>/<image>:<tag>
```

For details about when the `gsf.package` label is required, see [Image Labels](image_labels.md).

## OCI artifact

Recommended option when you build your Gear as an OCI artifact.

Publish your Gear:

```bash
oras push <your registry> git-system-follower-package/
```

## Package file structure

```plaintext
<your repository>
├─ git-system-follower-package/
│  ├─ package.yaml
│  └─ scripts/
│     └─ ...
└─ <your other files>
```

## `package.yaml`

Example:

```yaml
apiVersion: v2
type: gitlab-ci-pipeline
name: my-first-gear
version: 1.0.0
description: 'CI/CD pipeline for my service'
icon: 'icon.png'
subtype: component
dependencies:
  - artifactory.company.com/path-to/my-another-image:1.0.0
```

### v2-only sections

| Section       | Description                                                            |
|---------------|------------------------------------------------------------------------|
| `description` | Project description that will be synchronized to GitLab                |
| `icon`        | Path to the project icon file inside the `scripts/` directory          |
| `subtype`     | Gear subtype, currently the only supported value is `component`        |

For the full description of the v2 `package.yaml` sections, see
[`apiVersion` v2](../concepts/api_version_list/v2.md).

## Project metadata synchronization

When `description` and `icon` are present in `package.yaml`, git-system-follower
automatically synchronizes the project description, icon and CI/CD catalog with GitLab
during `install` and `update`. The metadata is tracked in the `.state.yaml` file.
See [`apiVersion` v2](../concepts/api_version_list/v2.md) for details.

## Develop API

v2 package scripts import the package API from the v2 surface:

```python
from git_system_follower.develop.api.v2 import Parameters, ProjectMetadata
from git_system_follower.develop.api.v2.templates import create_template
```

The v2 template functions (`create_template`, `update_template`) automatically trigger
the project metadata synchronization. See the [Develop Interface](../api_reference/develop_interface/index.md) reference.
