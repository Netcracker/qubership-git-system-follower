# Quickstart Guide
## Documentation
1. [Docs Home](../docs_home.md)
2. [Getting Started Guides](../getting_started.md)  
   1. **[Quickstart Guide](quickstart.md)**
   2. [Installation Guide](installation.md)
3. [Concepts Guides](../concepts.md)  
   1. [Gears Guide](../concepts/gears.md)
   2. [apiVersion list](../concepts/api_version_list.md)
      1. [apiVersion v1](../concepts/api_version_list/v1.md) 
   3. [.state.yaml Guide](../concepts/state.md)
   4. [Plugins Guide](../concepts/plugins.md)
      1. [CLI Arguments Extension Point](../concepts/plugins/cli_arguments.md)
4. [How-to Guides](../how_to.md)  
   1. [Build Guide](../how_to/build.md)
   2. [Gear Development Cases](../how_to/gear_development_cases.md)
   3. [Integration with semantic-release](../how_to/integration_with_semantic_release.md)
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

This guide covers how you can get started using git-system-follower

## Requirements
The following tools are required for git-system-follower to work
1. `git` >= 2.44.0 (see [git-scm.com getting started installing git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git))
2. `python` >= 3.10 (see [wiki.python.org beginners guide](https://wiki.python.org/moin/BeginnersGuide/Download))

## Prerequisites
The following prerequisites are required for a successful use of git-system-follower:
1. Gitlab instance with version >= v16.2.10

## Install git-system-follower
git-system-follower is a python package, you can install it with any python package manager

For more details, see [the Installation Guide](installation.md)

## Complete repository prerequisites
Once git-system-follower is ready, you can prepare the repository. 

**Note**. Right now git-system-follower only works with Gitlab

### Gitlab repository
1. **Create or select Gitlab repository**: create new empty repositories within the group or utilize existing repositories that you wish to manage
2. **Generate `Access Token`**:  
    1. Create a GitLab `Access Token` with the following scopes:
        * `api`: Full access to the API
        * `read_api`: Access to read API features
        * `read_repository`: Access to read repository data
        * `write_repository`: Access to modify repository data
    2. Ensure the token is associated with a user who has the necessary permissions or use the repository `Access Token`

Exporting the variable with the token to the repository before installing/uninstalling Gears:
```bash
export GSF_GIT_TOKEN=<your token>
```

## Install an example Gear
To install a gear, you can run the `install` command
```bash
gsf install --repo <your repo> \
            --branch <your branch> \
            <TBD: example package>
```

## Uninstall an example Gear
To uninstall a gear, you can run the `uninstall` command
```bash
gsf uninstall --repo <your repo> \
              --branch <your branch> \
              <TBD: example package>
```
