# Plugins
## Documentation
1. [Docs Home](../docs_home.md)
2. [Getting Started Guides](../getting_started.md) 
   1. [Quickstart Guide](../getting_started/quickstart.md)
   2. [Installation Guide](../getting_started/installation.md)
3. [Concepts Guides](../concepts.md) 
   1. [Gears Guide](gears.md)
   2. [apiVersion list](api_version_list.md)
      1. [apiVersion v1](api_version_list/v1.md) 
   3. [.state.yaml Guide](state.md)
   4. **[Plugins Guide](plugins.md)**
      1. [CLI Arguments Extension Point](plugins/cli_arguments.md) 
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

The functionality of git-system-follower can be extended with plugins.

The plugin system in git-system-follower is written using the `pluggy` library.

## Extension Points
* [CLI Arguments](plugins/cli_arguments.md)  
Expansion point for input arguments (Gears). Use this if you need to handle custom input.
* [Versioning](plugins/versioning.md)  
TBD

## How to connect plugin
A plugin is just as much a python package. git-system-follower reads all entry points available from
the current environment. If an entry point belongs to a certain group, it will automatically try to load that plugin.
