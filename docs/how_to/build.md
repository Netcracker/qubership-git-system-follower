# Build Gear
## Documentation
1. [Docs Home](../docs_home.md)
2. [Getting Started Guides](../getting_started.md) 
   1. [Quickstart Guide](../getting_started/quickstart.md)
   2. [Installation Guide](../getting_started/installation.md)
3. [Concepts Guides](../concepts.md) 
   1. [Gears Guide](../concepts/gears.md)
   2. [apiVersion list](../concepts/api_version_list.md)
      1. [apiVersion v1](../concepts/api_version_list/v1.md) 
   3. [.state.yaml Guide](../concepts/state.md)
4. [How-to Guides](../how_to.md)  
   1. **[Build Guide](build.md)**
   2. [Gear Development Cases](gear_development_cases.md)
   3. [Integration with semantic-release](integration_with_semantic_release.md)
5. [CLI reference](../cli_reference.md) 
   1. [download](../cli_reference/download.md)
   2. [install](../cli_reference/install.md) 
   3. [list](../cli_reference/list.md)
   4. [uninstall](../cli_reference/uninstall.md)
   5. [version](../cli_reference/version.md)
6. [API reference](../api_reference.md)  
   1. [Develop interface](../api_reference/develop_interface.md)  
      1. [types Module](../api_reference/develop_interface/types.md)
      2. [cicd_variables Module](../api_reference/develop_interface/cicd_variables.md)
      3. [templates Module](../api_reference/develop_interface/templates.md)

---

Information on how to build your project as git-system-follower Gear


## OCI artifact
Recommended option when you build your Gear as an OCI artifact

Package file structure:
```plaintext
<your repository>
├─ git-system-follower-package/
│  └─ <package files>
└─ <your other files>
```
Command to publish your Gear:
```bash
oras push <your registry> git-system-follower-package/
```

## Docker image with artifact
Package file structure:
```plaintext
<your repository>
├─ git-system-follower-package/
│  └─ <package files>
├─ Dockerfile
└─ <your other files>
```

## `Dockerfile` file
This simply requires you to put the gear in the image
```Dockerfile
FROM scratch
COPY git-system-follower-package /git-system-follower-package
```

docker build 