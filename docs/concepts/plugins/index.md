# Plugins
The functionality of git-system-follower can be extended with plugins.

The plugin system in git-system-follower is written using the `pluggy` library.

## Extension Points
* [CLI Arguments](cli_arguments.md)  
Expansion point for input arguments (Gears). Use this if you need to handle custom input.

## How to connect plugin
A plugin is just as much a python package. git-system-follower reads all entry points available from
the current environment. If an entry point belongs to a certain group, it will automatically try to load that plugin.
