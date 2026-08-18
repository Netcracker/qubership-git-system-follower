# Gear Dependencies

One gear may depend on any number of other gears. For example, a gear that provisions
a full environment can reuse the scripts and templates of a common, separately
maintained gear instead of duplicating them.

Dependencies are declared in the `dependencies` section of the gear's `package.yaml`
file and are managed automatically by git-system-follower: they are downloaded and
installed before the main gear and uninstalled after it.

## Declaring dependencies

The `dependencies` section is optional in both `apiVersion: v1` and `apiVersion: v2`.
Each dependency is specified as a **Docker image** that contains a gear package:

```yaml
apiVersion: v2
type: gear
name: application-environment
version: 1.0.0

dependencies:
  - registry.example.com/git-system-follower/common-storage:1.2.0
  - registry.example.com/git-system-follower/common-messaging:2.0.0
```

## Dependency versions

The version of a dependency is taken from the dependency's own `package.yaml` file —
not from the image tag. To download the correct image, the tag should match that
version:

```yaml
dependencies:
  - registry.example.com/git-system-follower/common-storage:1.2.0
```

If the image tag does not match the version in the dependency's `package.yaml`, a
warning is logged and the version from `package.yaml` is used:

```
Mismatch found in version of gear (1.2.0) and package.yaml (1.3.0)
```

Dependency images must be accessible using the registry credentials provided to the
`install` command (see [CLI reference](../cli_reference/install.md)).

## Installation behavior

When you run `git-system-follower install`, dependencies are processed **first**, and
the main gear **last**:

1. All dependency gears are downloaded and installed.
2. The main gear is installed on top of them.

### Shared dependencies are installed once

If two gears declare the same dependency, it is downloaded and installed only once.
Already-installed dependencies are skipped, so the same gear can be used as a
dependency of several other gears without conflicts.

### Download caching

Downloaded dependency images are cached, so a dependency that has already been
downloaded is not fetched again on subsequent installs. The mapping between downloaded
packages and their source images is kept in the `image-package-map.json` file.

### Maximum dependency depth

A gear may depend on other gears, but its dependencies **cannot have dependencies of
their own**. The maximum dependency depth is 1 (only one level of nested gears).

If the limit is exceeded, installation stops with an error that shows the dependency
chain:

```
The maximum dependency level has been reached (1). Error for application-environment -> common-storage -> common-database
```

## Uninstall behavior

When you run `git-system-follower uninstall`, the main gear is removed **first** and its
dependencies afterwards.

A dependency is **not** removed while another installed gear still uses it:

- If a dependency is shared with a gear that stays installed, the dependency is kept.
- If all gears that use the dependency are uninstalled in the same run, the dependency
  is removed together with them.
