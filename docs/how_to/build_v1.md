# Build Gear (v1)

How to build your project as a Gear with `apiVersion: v1`.

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
apiVersion: v1
type: gitlab-ci-pipeline
name: my-first-gear
version: 1.0.0
```

For the full description of the v1 `package.yaml` sections, see
[`apiVersion` v1](../concepts/api_version_list/v1.md).

## Develop API

v1 package scripts import the package API from the v1 surface:

```python
from git_system_follower.develop.api.v1 import Parameters
from git_system_follower.develop.api.v1.templates import create_template
```

For backward compatibility the unversioned `git_system_follower.develop.api` import
continues to work. See the [Develop Interface](../api_reference/develop_interface/index.md) reference.
