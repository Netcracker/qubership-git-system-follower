# Image Labels

When a Gear is distributed as a Docker image, git-system-follower inspects the image
labels to decide whether the image is a Gear. This avoids unpacking the image to read
`package.yaml`.

## Supported labels

| Label              | Purpose                                              | Value   | Required |
|--------------------|------------------------------------------------------|---------|:--------:|
| `gsf.package`      | Marks the image as a git-system-follower Gear        | `true`  |    no¹   |

¹ `gsf.package` is only checked for Docker images. OCI artifacts are always treated
as Gears (they cannot carry labels reliably), so the label is not required there.

## When labels are read

* **Docker image** (`application/vnd.docker.distribution.manifest.v2+json`): the image
  must carry `gsf.package="true"` to be accepted as a Gear.
* **OCI image** (`application/vnd.oci.image.manifest.v1+json`): accepted as a Gear
  without a label check.
* **OCI artifact** (published with `oras push`): accepted as a Gear without a label check.

Example `Dockerfile`:

```Dockerfile
FROM scratch

LABEL gsf.package="true"

COPY git-system-follower-package /git-system-follower-package
```
