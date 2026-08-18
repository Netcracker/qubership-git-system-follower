# Token Permissions

git-system-follower requires a GitLab token to manage the repository. Which access
level the token must have depends on **what the package actually does**:

- plain repository operations (push, merge requests, `.state.yaml` management) require **Developer** access;
- managing **CI/CD variables** or **webhooks** requires **Maintainer** access;
- synchronizing **project metadata** (`description` / `icon` / CI/CD catalog) requires **Owner** access.

## Permission matrix

| Operation | Required role |
|---|---|
| Push changes / create & merge requests | Developer (30) |
| Manage CI/CD variables | Maintainer (40) |
| Manage webhooks | Maintainer (40) |
| Sync project description / icon | Owner (50) |
| Enable / disable CI/CD catalog | Owner (50) |

### What do the numbers mean?

The numbers are GitLab's internal numeric values for project access levels, as
returned by the GitLab API in the `access_level` field. The role with the higher
number is the more privileged one:

| Value | Role |
|---|---|
| 10 | Guest |
| 20 | Reporter |
| 30 | Developer |
| 40 | Maintainer |
| 50 | Owner |

git-system-follower compares these values (via the `permissions` section of the
GitLab project API response) to decide whether the provided token is enough for
what a package needs to do.

## When each level is checked

Whether a package needs a higher role than Developer is not always visible from
its `package.yaml`, because a gear's `init.py` / `update.py` / `delete.py` is
arbitrary Python. For this reason the required role is determined in two moments:

1. **Statically**, as soon as the package description file is parsed: a
   `description` or `icon` section in `package.yaml` means project metadata will
   be synchronized, so **Owner** access is required.
2. **At the execution point**, while a gear's script runs: calling the
   `create_variable` / `delete_variable` or `create_webhook` / `update_webhook` /
   `delete_webhook` package API registers a **Maintainer** requirement.

If the provided token has less access than required, the run is aborted **before**
the changes are pushed or merged, with an error message that names the required
role and the reason.

## Examples

| Package contents | Required role |
|---|---|
| Plain gear (only files pushed to the repository) | Developer |
| Gear that creates CI/CD variables or webhooks | Maintainer |
| Gear with `description` / `icon` in `package.yaml` | Owner |
| Gear that enables the CI/CD catalog | Owner |
