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

## Additional git-system-follower configuration
### Enabling shell autocompletion
git-system-follower supports command autocompletion in `Bash`, `Zsh`, and `Fish`, which will save you a lot of time when typing commands.

Enter into the environment where you have gsf installed. If you used `uv tool install` to install, you do not need to enter in anywhere, gsf commands are available in your system

=== "Bash"

    1. Generate and save script:  
        Save the script somewhere:
        ```bash
        _GSF_COMPLETE=bash_source gsf > ~/.gsf-complete.bash
        ```

        Source the file in `~/.bashrc`:
        ```bash
        . ~/.gsf-complete.bash
        ```

    2. Via `eval`:  
        However, there is another way, via `eval`.
        Add this to `~/.bashrc`: 
        ```bash
        eval "$(_GSF_COMPLETE=bash_source gsf)"
        ```

        !!! warning
            Using `eval` means that the command is invoked and evaluated every time a shell is started, which can delay shell responsiveness. To speed it up, write the generated script to a file, then source that (1st option)

=== "Zsh"

    1. Generate and save script:  
        Save the script somewhere:
        ```bash
        _GSF_COMPLETE=zsh_source gsf > ~/.gsf-complete.zsh
        ```

        Source the file in `~/.zshrc`:
        ```bash
        . ~/.gsf-complete.zsh
        ```

    2. Via `eval`:  
        However, there is another way, via `eval`.
        Add this to `~/.zshrc`: 
        ```bash
        eval "$(_GSF_COMPLETE=zsh_source gsf)"
        ```

        !!! warning
            Using `eval` means that the command is invoked and evaluated every time a shell is started, which can delay shell responsiveness. To speed it up, write the generated script to a file, then source that (1st option)

=== "Fish"

    1. Generate and save script:  
        Save the script to `~/.config/fish/completions/gsf.fish`:
        ```bash
        _GSF_COMPLETE=fish_source gsf > ~/.config/fish/completions/gsf.fish
        . ~/.gsf-complete.zsh
        ```

    2. Via `eval`:  
        However, there is another way.
        Add this to `~/.config/fish/completions/gsf.fish`: 
        ```bash
        _GSF_COMPLETE=fish_source gsf | source
        ```
        This is the same file used for the activation script method above. For `Fish` it’s probably always easier to use that method.

!!! quote "Note"

    For autocompletion, git-system-follower uses the built-in functionality of the `click` library