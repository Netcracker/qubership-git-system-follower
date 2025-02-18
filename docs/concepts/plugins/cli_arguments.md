# CLI Arguments Extension Point
## Documentation
1. [Docs Home](../../docs_home.md)
2. [Getting Started Guides](../../getting_started.md) 
   1. [Quickstart Guide](../../getting_started/quickstart.md)
   2. [Installation Guide](../../getting_started/installation.md)
3. [Concepts Guides](../../concepts.md) 
   1. [Gears Guide](../gears.md)
   2. [apiVersion list](../api_version_list.md)
      1. [apiVersion v1](../api_version_list/v1.md) 
   3. [.state.yaml Guide](../state.md)
   4. [Plugins Guide](../plugins.md)
      1. **[CLI Arguments Extension Point](cli_arguments.md)**
4. [How-to Guides](../../how_to.md)  
   1. [Build Guide](../../how_to/build.md)
   2. [Gear Development Cases](../../how_to/gear_development_cases.md)
   3. [Integration with semantic-release](../../how_to/integration_with_semantic_release.md)
5. [CLI reference](../../cli_reference.md) 
   1. [download](../../cli_reference/download.md)
   2. [install](../../cli_reference/install.md) 
   3. [list](../../cli_reference/list.md)
   4. [uninstall](../../cli_reference/uninstall.md)
   5. [version](../../cli_reference/version.md)
6. [API reference](../../api_reference.md)  
   1. [Develop interface](../../api_reference/develop_interface.md)  
      1. [types Module](../../api_reference/develop_interface/types.md)
      2. [cicd_variables Module](../../api_reference/develop_interface/cicd_variables.md)
      3. [templates Module](../../api_reference/develop_interface/templates.md)

---

Extension point for input arguments (aka Gears). Use this point if you need to handle custom input, for example, 
you want to pass a `.txt` file that lists the OCI artifact.

That is, you can write functionality to handle arguments that, for example, have a complex structure. 

Note that the result of the plugin must be one of the following:
source directory (`PackageCLISource`), tar.gz archive (`PackageCLITarGz`), docker image/OCI artifact (`PackageCLIImage`).
See the example below

Plugin System entry points group: `gsf.plugins.cli.packages`

## Plugin file structure
```text
<plugin name>/  # e.g. txt-plugin
├─ pyproject.toml
└─ <plugin name>/  # e.g. txt_plugin
   ├─ __init__.py
   ├─ main.py
   └─ <other files>/
```

## `pyproject.toml` file
```toml
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"

[project]
name = "<plugin name>"  # e.g. txt-plugin
version = "0.0.1"
dependencies = [
    'pluggy',
    <libraries you need>  # e.g. requests
]

[project.entry-points."gsf.plugins.cli.packages"]  # Registration with the CLI system
point-name = 'path.to.module:ImplementedInterface'  # A main entry point
```

## `main.py` file
You can write a large plugin that includes many modules and complex logic,
but the minimum `main.py` should contain only the implementation of the `match` and `get_gears` hooks. 
If you need some additional parameters from cli, you can get them added with the help of `plugin_options`.

Specification for your plugins: [git_system_follower/plugins/cli/packages/specs.py](../../../git_system_follower/plugins/cli/packages/specs.py#L28)

For example, txt plugin:
```python
from pathlib import Path

from git_system_follower.typings.cli import PackageCLIImage
from git_system_follower.plugins.cli.packages.specs import HookSpec
from git_system_follower.plugins.cli.packages import hookimpl
from git_system_follower.plugins.cli.packages.default import ImagePlugin


class TxtPlugin(HookSpec):
    suffix = '.tar.gz'
    
    @hookimpl
    def match(self, value: str) -> bool:
        path = Path(value)
        return path.name.endswith(self.suffix)
    
    @hookimpl
    def get_gears(self, value: str, **kwargs) -> list[PackageCLIImage]:
        path = Path(value)
        with open(path, 'r') as file:
            images = file.read()
        
        image_plugin = ImagePlugin()
        gears = []
        for image in images:
            gear = image_plugin.parse_image(image)
            gears.append(gear)
        return gears
```