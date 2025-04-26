# CLI reference
This CLI provides several commands for managing gears within your GitLab repository.
Below are pages with the available commands and their functionalities:

1. [download](download.md) - Download gears
2. [install](install.md) - Install gears to Gitlab repository
3. [list](list.md) - List installed gears: **in develop** :exclamation:
4. [uninstall](uninstall.md) - Uninstall gears from Gitlab repository
5. [version](version.md) - Show version

## Entry points
You can use long and short entry point to use git-system-follower, their functionality is the same:
```bash
git-system-follower --help  # long entry point
gsf --help                  # short entry point
```
From now on, the short entry point option will be used in the documentation: `gsf`

## Display help text
To list the help on any command just execute the command, followed by the `--help` option

```bash
gsf --help
```

<div class="result" markdown>

```plaintext
Usage: gsf [OPTIONS] COMMAND [ARGS]...

  The package manager for Git providers

Options:
  --help  Show this message and exit.

Commands:
  download   Download packages
  install    Install packages to branches in GitLab repository
  list       List installed packages: in develop
  uninstall  Uninstall packages from branches in GitLab repository
  version    Show version
```

</div>