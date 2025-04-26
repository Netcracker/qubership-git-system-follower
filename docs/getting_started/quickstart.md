# Quickstart Guide
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

!!! note
    Right now git-system-follower only works with Gitlab

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
