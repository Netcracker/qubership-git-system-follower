# Version Synchronization

The `package.yaml` file is the primary source of truth for the package version. Any other locations reference or imply a version — such as Docker tags must match the version specified in `package.yaml`.

1. The version field in `package.yaml` defines the canonical version of the package.
2. Any docker tag that includes or implies a version must match the version defined in `package.yaml`.

Sample version `package.yaml` in gear :

```yaml
version: 1.2.3
```

!!! note
    For example, consider a package `hello-gear` with the tag `1.2.3`.

    This tag must match the version specified in `package.yaml` to avoid ambiguity or inconsistency across environments and automation tools.