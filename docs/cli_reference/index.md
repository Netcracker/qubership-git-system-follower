# CLI reference
This CLI provides several commands for managing gears within your GitLab repository.
Below are pages with the available commands and their functionalities:

1. [download](download.md) - Download gears
2. [install](install.md) - Install gears to GitLab repository
3. [list](list.md) - List installed gears: **in develop** :exclamation:
4. [template](template.md) - Template out files using a cookiecutter template and show them in stdout
5. [uninstall](uninstall.md) - Uninstall gears from GitLab repository
6. [version](version.md) - Show version

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
  download   Download gears
  install    Install gears to branches in repository
  list       List installed gears: in develop
  template   Template out files using a cookiecutter template and show...
  uninstall  Uninstall gears from branches in repository
  version    Show version
```

</div>