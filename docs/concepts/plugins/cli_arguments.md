# CLI Arguments Extension Point
Extension point for input arguments (aka Gears). Use this point if you need to handle custom input, for example, 
you want to pass a `.txt` file that lists the OCI artifact.

That is, you can write functionality to handle arguments that, for example, have a complex structure. 

!!! note
    Result of the plugin must be one of the following: a directory with the source code
    (`PackageCLISource`), a tar.gz archive (`PackageCLITarGz`), a docker image/OCI artifact (`PackageCLIImage`)
    
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

<!-- Specification for your plugins: [git_system_follower/plugins/cli/packages/specs.py](../../../git_system_follower/plugins/cli/packages/specs.py#L28) -->

For example, txt plugin:
```python
from pathlib import Path

from git_system_follower.typings.cli import PackageCLIImage
from git_system_follower.plugins.cli.packages.specs import HookSpec
from git_system_follower.plugins.cli.packages import hookimpl
from git_system_follower.plugins.cli.packages.default import ImagePlugin


class TxtPlugin(HookSpec):
    suffix = '.txt'
    
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