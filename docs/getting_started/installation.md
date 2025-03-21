# Installation
## Documentation
1. [Docs Home](../docs_home.md)
2. [Getting Started Guides](../getting_started.md)  
   1. [Quickstart Guide](quickstart.md)
   2. **[Installation Guide](installation.md)**
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

This guide shows how to install the git-system-follower CLI. git-system-follower can be installed either source, or from pre-built python package.

git-system-follower is python package, you can install it with any python package manager.

**Note**. git-system-follower only supports Linux, it can run on Windows or macOS, but officially Windows and macOS are not supported

## From PyPI
If you prefer to use git-system-follower as a standalone CLI tool instead of integrating its functionality into your Python packages, `uv tool` is the recommended installation method.

For more details, see the [uv tool documentation](https://docs.astral.sh/uv/concepts/tools/).

<details open>
    <summary><b>Recommended: By uv</b></summary>

   Before proceeding, make sure uv is installed. See the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)

   Then, install git-system-follower with:
   ```bash
   uv tool install qubership-git-system-follower
   ```
   
   > However, you may want to install git-system-follower as a python package so that you can, for example, use it inside your own python packages

   You can also do this with `uv`:
   ```bash
   # create & activate virtual env
   uv venv .venv && source .venv/bin/activate

   # Install git-system-follower
   uv pip install qubership-git-system-follower
   ```

</details>

However, if `uv` is not a suitable option, use `pip` instead.
<details>
    <summary>By pip</summary>

   ```bash
   # create & activate virtual env
   python -m venv .venv && source .venv/bin/activate 

   # Install git-system-follower
   pip install qubership-git-system-follower
   ```
</details>

## From Source
Building git-system-follower from source is slightly more work

```bash
# create & activate virtual env
python -m venv .venv && source .venv/bin/activate

# Clone git repository
git clone https://github.com/Netcracker/qubership-git-system-follower.git

# Install git-system-follower
pip install -e git-system-follower/
```
