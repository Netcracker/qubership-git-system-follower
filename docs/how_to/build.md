# Build Gear

Information on how to build your project as a git-system-follower Gear.

A Gear is built the same way regardless of its `apiVersion`: you prepare the
`git-system-follower-package/` directory and publish it either as an **OCI artifact**
or as a **Docker image**. The `apiVersion` only changes the content of the
`package.yaml` file.

## Distribution options

A Gear can be distributed in two ways:

* **Docker image** — build a `FROM scratch` image with the `gsf.package="true"` label
  and `COPY git-system-follower-package /git-system-follower-package`, then
  `docker build` and `docker push`. The `Dockerfile` structure is described first in the
  [v1](build_v1.md) and [v2](build_v2.md) pages.
* **OCI artifact** — `oras push <your registry> git-system-follower-package/`, no labels
  required.

For details about when the `gsf.package` label is required, see [Image Labels](image_labels.md).

## API Versions

| Version | package.yaml             | Distribution                     |
|---------|--------------------------|----------------------------------|
| **v1**  | `apiVersion: "v1"`       | OCI artifact or Docker image     |
| **v2**  | `apiVersion: "v2"`       | OCI artifact or Docker image     |

## Quicklinks by Version

### v1 (Legacy)
* [Build Gear v1](build_v1.md) — `package.yaml` with `apiVersion: v1`

### v2 (Current)
* [Build Gear v2](build_v2.md) — `package.yaml` with `apiVersion: v2`, plus `description`, `icon`, `subtype`

## Key v2 Differences

| Feature                     | v1  | v2                          |
|-----------------------------|-----|-----------------------------|
| Project metadata (`description`, `icon`) | ❌  | ✅ auto-synced to GitLab    |
| `subtype`                   | ❌  | ✅ `component`              |
| Develop API                 | v1 surface | v2 surface (auto metadata sync) |

## Next steps

After building the Gear, see the [CLI reference](../cli_reference/install.md) to install it.
