# Installation
This guide shows how to install the git-system-follower CLI. git-system-follower can be installed either source, or from pre-built python package.

git-system-follower is python package, you can install it with any python package manager.

!!! note
    git-system-follower only supports Linux, it can run on Windows or macOS, but officially Windows and macOS are not supported

## From PyPI
If you prefer to use git-system-follower as a standalone CLI tool instead of integrating its functionality into your Python packages, `uv tool` is the recommended installation method.

For more details, see the [uv tool documentation](https://docs.astral.sh/uv/concepts/tools/).

???+ note "Recommended: By uv"
    
    Before proceeding, make sure `uv` is installed. See the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)

    Then, install git-system-follower with:
    ```bash
    uv tool install qubership-git-system-follower
    ```

    > However, you may want to install git-system-follower as a python package so that you can, for example, use it inside your own python packages

    You can also do this with `uv`:
    ```bash
    # create & activate virtual env
    uv venv .venv && source .venv/bin/activate

    # install git-system-follower
    uv pip install qubership-git-system-follower
    ```

However, if `uv` is not a suitable option, use `pip` instead.

??? note "Standard: By pip"
    ```bash
    # create & activate virtual env
    python -m venv .venv && source .venv/bin/activate 

    # Install git-system-follower
    pip install qubership-git-system-follower
    ```

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
