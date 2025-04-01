# install
## Documentation
1. [Docs Home](../docs_home.md)
2. [Getting Started Guides](../getting_started.md) 
   1. [Quickstart Guide](../getting_started/quickstart.md)
   2. [Installation Guide](../getting_started/installation.md)
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
   1. [download](download.md)
   2. **[install](install.md)**
   3. [list](list.md)
   4. [uninstall](uninstall.md)
   5. [version](version.md)
6. [API reference](../api_reference.md)  
   1. [Develop interface](../api_reference/develop_interface.md)  
      1. [types Module](../api_reference/develop_interface/types.md)
      2. [cicd_variables Module](../api_reference/develop_interface/cicd_variables.md)
      3. [templates Module](../api_reference/develop_interface/templates.md)

---

Install gears to branches in GitLab repository

git-system-follower install a gears into the repository branch using the package api: `init` / `update` / `delete`.
After it git-system-follower create/update `.states.yaml` file in root of directory where save information about installed gears

You can pass a gear to installation as:
1. docker image: it will be downloaded (see [CLI reference/download](download.md))
2. `.tar.gz` file
3. directory with gear (source code)

## Display help text
To list the help on any command just execute the command, followed by the `--help` option
```bash
gsf install --help
```

## Arguments
| Name    | Description                                                                                                                                                                            | Example                                                                                                                      |
|---------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| `GEARS` | Install all listed gears as:<br/>1. image: `<registry>/<repository>/<name>:<tag>`<br/>2. .tar.gz archive: `/path/to/archive.tar.gz`<br/>3.source code files: `/path/to/gear directory` | `artifactory.company.com/my-image:1.0.0`, `/path/to/my-archive@1.0.0.tar.gz`, `/path/to/my-gear@1.0.0`, `project/my-package` |

## Options
| Name                  | Description                                                                                         | Mandatory |                                     Default value                                      |  Environment variable   | Example                                                          |
|-----------------------|-----------------------------------------------------------------------------------------------------|:---------:|:--------------------------------------------------------------------------------------:|:-----------------------:|------------------------------------------------------------------|
| `-r`, `--repo`        | Gitlab repository url                                                                               |     +     |                                           -                                            |            -            | `https://git.company.com/test`, `http://localhost/test.git`      |
| `-b`, `--branch`      | Branches in which to install the gears                                                              |     +     |                                           -                                            |            -            | `main`, `features/FAKE-0000`                                     |
| `-t`, `--token`       | Gitlab access token                                                                                 |     +     |                                           -                                            |     `GSF_GIT_TOKEN`     | `glpat-xxxxxXYvoxqPZw_5Kmyr`                                     |
| `--extra`             | Extra parameters to be passed to the package API: `name`, `value`, `masked`/`no-masked` of variable |     -     |                                           -                                            |            -            | `add_functionality true no-masked`, `password MyPa$$word masked` |
| `--message`           | Commit message                                                                                      |     -     |                                  `Installed gear(s)`                                   |            -            | `FAKE-0000 update our tools`                                     |
| `--git-username`      | Username under which the commit will be made to the repository                                      |     -     |        The username in the `~/.gitconfig` file, if it does not exist, `unknown`        |   `GSF_GIT_USERNAME`    | `Name LastName`, `MyName`                                        |
| `--git-email`         | User email under which the commit will be made to the repository                                    |     -     | The user email in the `~/.gitconfig` file, if it does not exist, `unknown@example.com` |     `GSF_GIT_EMAIL`     | `your.email@gmail.com`                                           |
| `--registry-type`     | Specify the registry type or use automatic detection                                                |     -     |                                      `Autodetect`                                      |            -            | `Autodetect`, `Dockerhub`, `Artifactory`, `Nexus`                |
| `--registry-username` | Username for basic authentication in the registry when downloading Gears                            |     -     |                                           -                                            | `GSF_REGISTRY_USERNAME` | `myusername`, `k1shk1n`                                          |
| `--registry-password` | Password for basic authentication in the registry when downloading Gears                            |     -     |                                           -                                            | `GSF_REGISTRY_PASSWORD` | `MyPa$$w0rd`                                                     |
| `--insecure-registry` | Allow insecure connections to the registry (use HTTP instead of HTTPS)                              |     -     |                                        `False`                                         |            -            |                                                                  |
| `--force`             | Forced installation: change of files, CI/CD variables as specified in gear                          |     -     |                                        `False`                                         |            -            |                                                                  |
| `--debug`             | Show debug level messages                                                                           |     -     |                                        `False`                                         |            -            |                                                                  |

## Examples
Installing the gear (docker image) to main branch
```plaintext
$ gsf packages install -r https://git.company.com/test.git \
                       -b main -t glpat-xxxxxXYvoxqPZw_5Kmyr \
                       artifactory.company.com/my-image:1.0.0
```

Installing the gear (`.tar.gz` archive) to main branch
```plaintext
$ gsf packages install -r https://git.company.com/test.git \
                       -b main -t glpat-xxxxxXYvoxqPZw_5Kmyr \
                       packages/my-archive@1.0.0.tar.gz
```

Installing the gear (directory with source code) to main branch
```plaintext
$ gsf packages install -r https://git.company.com/test.git \
                       -b main -t glpat-xxxxxXYvoxqPZw_5Kmyr \
                       packages/my-project
```

Specify multiple gears for installation:
```plantext
$ gsf packages install -r https://git.company.com/test.git \
                       -b main -t glpat-xxxxxXYvoxqPZw_5Kmyr \
                       artifactory.company.com/my-image:1.0.0 \
                       packages/some-other-package.tar.gz \
                       projects/my-project
```

Specify multiple branches for installing:
```plantext
$ gsf packages install -r https://git.company.com/test.git \
                       -b main -b develop -b feature\DTWO-0000 \
                       -t glpat-xxxxxXYvoxqPZw_5Kmyr \
                       packages/my-gear@1.0.0
```

Passing extra parameters to api package during installation:
```plantext
$ gsf packages install -r https://git.company.com/test.git \
                       -b main -t glpat-xxxxxXYvoxqPZw_5Kmyr \
                       --extra FIRST_VAR_NAME FIRST_VAR_VALUE no-masked \
                       --extra PASSWORD Pa$$w0rd masked \
                       packages/my-gear@1.0.0
```

## Advanced
### Authentication Methods for Registry Access
You can work with private registries by providing authentication credentials.

There are three ways to specify credentials, listed in order of priority: 
1. Pass the credentials directly using `--registry-username` and `--registry-password`
2. Set `GSF_REGISTRY_USERNAME` and `GSF_REGISTRY_PASSWORD` as environment variables
3Credentials can be provided via stdin using `echo`: `echo -e "<username>\n<password>" | gsf install ...`
> \[!WARNING]
>
> Note that unlike other methods, you can't transfer only username or only password this way. This way you can transfer both username and password at once

> \[!WARNING]
>
> This priority is wrong. In the next version the 2nd and 3rd item will be reversed

If multiple methods are used, command-line parameters take precedence over stdin, and stdin takes precedence over environment variables.

> \[!NOTE]
>
> If you pass only one thing: username or password; then gsf will ask for the rest as a prompt.
> This is useful if you want to pass username in the clear and not show the password at all

### Carefully update/delete created resources
git-system-follower provides an interface for creating file structure and creating CI/CD variables,
so that when installing, git-system-follower tries to carefully update/delete created resources.

For example, if a CI/CD variable has already been created and does not match what the gear
being installed provides, git-system-follower will skip processing that variable. But if the `--force` parameter is specified or 
`is_force=True` is specified in creating variable in package api,
git-system-follower will update/delete the variable regardless of its contents.

Works the same way with files in the repository.

### Installation order
Install dependencies first, then root gear.

### Authorization and commits to the repository
The token from `--token` does not have to belong to the user from `--git-username`/`--git-email`. 
Commit changes can be made under a user who does not have permissions to the repository. 
But the push of these changes must be done under a user who has access to the repository.
