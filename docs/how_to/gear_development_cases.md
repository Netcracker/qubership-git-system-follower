# Gear Development Cases

This guide covers common cases and best practices when developing and distributing a Gear.

## Version synchronization between image tag and package.yaml

When publishing a Gear as a Docker image, the image tag **should match** the `version` field in `package.yaml`.

```yaml
# package.yaml
apiVersion: v1
type: gitlab-ci-pipeline
name: my-gear
version: 1.0.0
```

```bash
# Build and push with matching tag
docker build -t registry.example.com/team/my-gear:1.0.0 .
docker push registry.example.com/team/my-gear:1.0.0
```

If the image tag does not exactly match the version in `package.yaml`, git-system-follower will log a warning:

```
Mismatch found in version of gear (1.0.0_gsf_image) and package.yaml (1.0.0)
```

This is **not advisable**. A mismatch can cause confusion during rollback and version tracking. Always keep the image tag in sync with `package.yaml`.

## Name synchronization between image and package.yaml

The `name` field in `package.yaml` should match the gear image name. git-system-follower uses this to verify that the correct gear is being installed.

```yaml
# package.yaml
apiVersion: v1
type: gitlab-ci-pipeline
name: my-gear
version: 1.0.0
```

```bash
# Image name should match the name in package.yaml
docker build -t registry.example.com/team/my-gear:1.0.0 .
```

If the image name does not contain the package name, git-system-follower will raise an error to prevent incorrect gears from being installed.

## Gear structure types

git-system-follower auto-detects the gear structure type by examining the `scripts/` directory layout.

### Simple (single version)

A simple gear has Python scripts directly in `scripts/` without version subdirectories.

```text
git-system-follower-package/
  package.yaml
  scripts/
    init.py
    delete.py
    templates/
      my-template/
        cookiecutter.json
        {{ cookiecutter.gsf_repository_name }}/
          ...
```

**When to use:** Choose simple when your gear is self-contained, doesn't need versioned migrations, and will be updated by reinstalling with `--force`.

Key characteristics:

- `is_force` is always `true` — files are overwritten on every install
- No `update.py` support — upgrades use `init.py` with force
- Best for small, self-contained gears

### Complex (multiple versions)

A complex gear has version-named subdirectories under `scripts/`.

```text
git-system-follower-package/
  package.yaml
  scripts/
    1.0.0/
      init.py
      update.py
      delete.py
      templates/
        my-template/
          ...
    1.1.0/
      init.py
      update.py
      delete.py
      templates/
        my-template/
          ...
```

**When to use:** Choose complex when your gear needs controlled migrations between versions, or when you want to preserve user modifications to files during upgrades.

Key characteristics:

- Supports `update.py` for versioned migrations
- On upgrade, git-system-follower walks through all intermediate versions sequentially
- Preferred for long-term maintainability

!!! warning
    Simple and complex gears should not be mixed in the same repository. Installing a simple gear on a branch with a complex gear (or vice versa) will exit with an error.

    To migrate between gear types, use the `--force` flag:

    ```bash
    gsf install -r https://gitlab.example.com/team/project.git \
                -b main \
                -t <GITLAB_TOKEN> \
                --force \
                registry.example.com/team/my-gear:1.0.0
    ```

    This allows the structure type change but **review the affected files in your repository manually** to make sure everything looks as expected before moving forward.

For more details, see [Gears](../concepts/gears.md) and [apiVersion list](../concepts/api_version_list/index.md).

## package.yaml

A `package.yaml` supports the following fields:

```yaml
apiVersion: v1
type: gitlab-ci-pipeline
name: my-gear
version: 1.0.0
dependencies:
  - artifactory.company.com/team/dependency-image:1.0.0
```

| Section        | Required | Description                                    |
|----------------|:--------:|------------------------------------------------|
| `apiVersion`   | Yes      | Must be `v1`                                   |
| `type`         | Yes      | Gear type (e.g. `gitlab-ci-pipeline`)          |
| `name`         | Yes      | Unique gear name                               |
| `version`      | Yes      | Gear version                                   |
| `dependencies` | No       | List of dependency Docker images               |

For the full field reference, see [`apiVersion` v1](../concepts/api_version_list/v1.md).

## Develop API

Package scripts should import from the develop API:

```python
from git_system_follower.develop.api.types import Parameters
from git_system_follower.develop.api.templates import create_template, delete_template
from git_system_follower.develop.api.cicd_variables import create_variable, delete_variable
from git_system_follower.develop.api.webhooks import create_webhook, delete_webhook
```

For the full API reference, see [Develop Interface](../api_reference/develop_interface/index.md).

## Building your Gear

Gears can be distributed as Docker images or OCI artifacts.

- [Build Gear](build.md) — overview of distribution options
- [Image Labels](image_labels.md) — when the `gsf.package` label is required

### Example Dockerfile

```Dockerfile
FROM scratch

LABEL gsf.package="true"

COPY git-system-follower-package /git-system-follower-package
```

```bash
docker build -t registry.example.com/team/my-gear:1.0.0 .
docker push registry.example.com/team/my-gear:1.0.0
```

## Installing and uninstalling Gears

- [CLI reference / install](../cli_reference/install.md)
- [CLI reference / uninstall](../cli_reference/uninstall.md)

### Install example

```bash
gsf install -r https://gitlab.example.com/team/project.git \
            -b main \
            -t <GITLAB_TOKEN> \
            registry.example.com/team/my-gear:1.0.0
```

### Uninstall example

```bash
gsf uninstall -r https://gitlab.example.com/team/project.git \
              -b main \
              -t <GITLAB_TOKEN> \
              registry.example.com/team/my-gear:1.0.0
```

## Development workflow for a dev branch

When developing a new Gear or iterating on an existing one, follow this workflow:

1. **Create a dev branch** in your gear repository
2. **Build and push** the gear image with a dev tag (keep it in sync with `package.yaml`)
3. **Test installation** on a throwaway target branch using `gsf install`
4. **Verify** that templates, CI/CD variables, and webhooks are created correctly
5. **Test update** by installing an older version first, then installing the new version
6. **Test rollback** by installing a newer version first, then installing the older version
7. **Test uninstall** to confirm clean removal
8. **Merge to main** and push the release image to the registry

```bash
# 1. Build dev version
docker build -t registry.example.com/team/my-gear:1.1.0-dev.1 .
docker push registry.example.com/team/my-gear:1.1.0-dev.1

# 2. Test fresh install
gsf install -r https://gitlab.example.com/team/target-project.git \
            -b test-branch \
            -t <GITLAB_TOKEN> \
            registry.example.com/team/my-gear:1.1.0-dev.1

# 3. Verify results in GitLab (check files, CI/CD variables, etc.)

# 4. Test update: install an older version, then the new one
gsf install -r https://gitlab.example.com/team/target-project.git \
            -b test-branch \
            -t <GITLAB_TOKEN> \
            registry.example.com/team/my-gear:1.0.0
gsf install -r https://gitlab.example.com/team/target-project.git \
            -b test-branch \
            -t <GITLAB_TOKEN> \
            registry.example.com/team/my-gear:1.1.0-dev.1

# 5. Test rollback: install a newer version, then downgrade
gsf install -r https://gitlab.example.com/team/target-project.git \
            -b test-branch \
            -t <GITLAB_TOKEN> \
            registry.example.com/team/my-gear:1.2.0
gsf install -r https://gitlab.example.com/team/target-project.git \
            -b test-branch \
            -t <GITLAB_TOKEN> \
            registry.example.com/team/my-gear:1.0.0

# 6. Clean up
gsf uninstall -r https://gitlab.example.com/team/target-project.git \
              -b test-branch \
              -t <GITLAB_TOKEN> \
              registry.example.com/team/my-gear:1.0.0

# 7. After merging to main, build and push the release image
docker build -t registry.example.com/team/my-gear:1.1.0 .
docker push registry.example.com/team/my-gear:1.1.0
```

!!! tip
    Use `--debug` flag during development to see detailed logs of what git-system-follower is doing.

## Token permissions

Different operations require different access levels. See [Token Permissions](../concepts/token_permissions.md) for the full hierarchy.

| Role    | Required for                                  |
|---------|-----------------------------------------------|
| Developer (30) | Push, merge requests, state management  |
| Maintainer (40) | CI/CD variable and webhook management |
