# CLI reference
## Documentation
1. [Docs Home](docs_home.md)
2. [Getting Started Guides](getting_started.md) 
   1. [Quickstart Guide](getting_started/quickstart.md)
   2. [Installation Guide](getting_started/installation.md)
3. [Concepts Guides](concepts.md)  
   1. [Gears Guide](concepts/gears.md)
   2. [apiVersion list](concepts/api_version_list.md)
      1. [apiVersion v1](concepts/api_version_list/v1.md) 
   3. [.state.yaml Guide](concepts/state.md)
4. [How-to Guides](how_to.md)  
   1. [Build Guide](how_to/build.md)
   2. [Gear Development Cases](how_to/gear_development_cases.md)
   3. [Integration with semantic-release](how_to/integration_with_semantic_release.md)
5. **[CLI reference](cli_reference.md)** 
   1. [download](cli_reference/download.md)
   2. [install](cli_reference/install.md) 
   3. [list](cli_reference/list.md)
   4. [uninstall](cli_reference/uninstall.md)
   5. [version](cli_reference/version.md)
6. [API reference](api_reference.md)  
   1. [Develop interface](api_reference/develop_interface.md)  
      1. [types Module](api_reference/develop_interface/types.md)
      2. [cicd_variables Module](api_reference/develop_interface/cicd_variables.md)
      3. [templates Module](api_reference/develop_interface/templates.md)

---

This CLI provides several commands for managing gears within your GitLab repository.
Below are pages with the available commands and their functionalities:
1. [download](cli_reference/download.md) - Download gears
2. [install](cli_reference/install.md) - Install gears to repositories in GitLab group
3. [list](cli_reference/list.md) - List installed gears: **in develop** :exclamation:
4. [uninstall](cli_reference/uninstall.md) - Uninstall gears from repositories in GitLab group
5. [version](cli_reference/version.md) - Show version

## Entry points
You can use long and short entry point to use `git-system-follower`, their functionality is the same:
```bash
$ git-system-follower packages --help  # long entry point
$ gsf packages --help                  # short entry point
```
From now on, the short entry point option will be used in the documentation: `gsf`

## Display help text
To list the help on any command just execute the command, followed by the `--help` option
```text
$ gsf packages --help

Usage: gsf packages [OPTIONS] COMMAND [ARGS]...

  Package management in Gitlab repository

Options:
  --help  Show this message and exit.

Commands:
  download   Download packages
  install    Install packages to branches in GitLab repository
  list       List installed packages: in develop
  uninstall  Uninstall packages from branches in GitLab repository
  version    Show version
```