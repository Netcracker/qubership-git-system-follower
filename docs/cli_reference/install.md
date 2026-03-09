# install
Install gears to branches in GitLab repository

git-system-follower install a gears into the repository branch using the package API: `init` / `update` / `delete`.
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
| `-r`, `--repo`        | Gitlab repository URL                                                                               |     +     |                                           -                                            |            -            | `https://git.company.com/test`, `http://localhost/test.git`      |
| `-b`, `--branch`      | Branches in which to install the gears                                                              |     +     |                                           -                                            |            -            | `main`, `features/FAKE-0000`                                     |
| `-t`, `--token`       | Gitlab access token                                                                                 |     +     |                                           -                                            |     `GSF_GIT_TOKEN`     | `<GITLAB_TOKEN>`                                     |
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
gsf install -r https://git.company.com/test.git \
            -b main -t <GITLAB_TOKEN> \
            artifactory.company.com/my-image:1.0.0
```

Installing the gear (`.tar.gz` archive) to main branch
```plaintext
gsf install -r https://git.company.com/test.git \
            -b main -t <GITLAB_TOKEN> \
            packages/my-archive@1.0.0.tar.gz
```

Installing the gear (directory with source code) to main branch
```plaintext
gsf install -r https://git.company.com/test.git \
            -b main -t <GITLAB_TOKEN> \
            packages/my-project
```

Specify multiple gears for installation:
```plantext
gsf install -r https://git.company.com/test.git \
            -b main -t <GITLAB_TOKEN> \
            artifactory.company.com/my-image:1.0.0 \
            packages/some-other-package.tar.gz \
            projects/my-project
```

Specify multiple branches for installing
```plantext
gsf install -r https://git.company.com/test.git \
            -b main -b develop -b feature\DTWO-0000 \
            -t <GITLAB_TOKEN> \
            packages/my-gear@1.0.0
```

Passing extra parameters to API package during installation:
```plantext
gsf install -r https://git.company.com/test.git \
            -b main -t <GITLAB_TOKEN> \
            --extra FIRST_VAR_NAME FIRST_VAR_VALUE no-masked \
            --extra PASSWORD Pa$$w0rd masked \
            packages/my-gear@1.0.0
```

## Advanced
### Authentication Methods for Registry Access
You can work with private registries by providing authentication credentials.

There are three ways to specify credentials, listed in order of priority:

1. Pass the credentials directly using `--registry-username` and `--registry-password`
2. Credentials can be provided via stdin: `echo "<username>:<password>" | gsf download ...`
3. Set `GSF_REGISTRY_USERNAME` and `GSF_REGISTRY_PASSWORD` as environment variables
4. If only username or only password has been provided then git-system-follower will request
the rest of credentials using prompt (in interactive mode)

If multiple methods are used, command-line parameters take precedence over stdin, and stdin takes precedence over environment variables.
<!-- markdownlint-disable MD046 -->
!!! info
    How it works internally: if you pass a string that contains `:`,
    then git-system-follower parse that string as username everything before that character,
    everything after it as password.

    If this string doesn't contain `:` git-system-follower will try to unmask this string
    using `base64` and will parse unmasked string again.

    If `:` is not in the string again, git-system-follower recognizes the entire string as a passed password

#### Specific registry authentication
Some registries, such as **AWS ECR**, introduce their own custom "enhancements" on top of the classic
Docker authentication mechanisms like **Basic** and **Bearer**. In this case, git-system-follower follows
the standard [Docker Registry HTTP API v2](https://docker-docs.uclv.cu/registry/spec/api/) specification,
and any additional authentication logic is left to the user or the orchestration system in place.

For AWS ECR specifically, you can authenticate using the AWS CLI (after configuring your local AWS account) like so:
```bash
aws ecr get-authorization-token --output text --query 'authorizationData[].authorizationToken' | gsf install ...
```

!!! note
    AWS ECR does not use Bearer authentication. Instead, it relies on **Basic** authentication,
    where the **username** is literally `AWS`, and the **password** is a temporary token (which lasts for 12 hours) obtained
    via `aws ecr get-authorization-token`.

### Carefully update/delete created resources
git-system-follower provides an interface for creating file structure and creating CI/CD variables,
so that when installing, git-system-follower tries to carefully update/delete created resources.

For example, if a CI/CD variable has already been created and does not match what the gear
being installed provides, git-system-follower will skip processing that variable. But if the `--force` parameter is specified or
`is_force=True` is specified in creating variable in package API,
git-system-follower will update/delete the variable regardless of its contents.

Works the same way with files in the repository.

### Installation order
Install dependencies first, then root gear.

### Authorization and commits to the repository
The token from `--token` does not have to belong to the user from `--git-username`/`--git-email`.
Commit changes can be made under a user who does not have permissions to the repository.
But the push of these changes must be done under a user who has access to the repository.

### Rollback
git-system-follower supports automatic rollback of installed gears.

When a gear is installed, its source (for example `domain:port/gear:1.0.0` or `/tmp/gear@1.0.0`) is recorded in `.state.yaml` under the `source` field.

To perform a rollback, run the `gsf install` command as usual and provide a gear version **older than the currently installed version**.  
git-system-follower will then:

1. Use the stored `source` value from `.state.yaml`
2. Uninstall the currently installed version
3. Install the specified older version

Sample gear structure when rollback would auto-detect using the field source -

```yaml
hash: Hash of 'packages' section
packages: # List of installed packages
- cicd_variables: # Section of created CI/CD variables
    hash: Hash of 'names' section
    names: # Name list of created CI/CD variables
      - Name of CI/CD variable
  dependencies: # List of dependencies of this package
    - 'dependency-name@dependency-version'
  last_update: Date in 'YYYY-MM-DD HH:MM:SS.ffffff' format
  name: Gear name
  source: domain:port/gear:1.0.0 # Source tracking of installed gear
  template_variables: # Section of used variables to create template
    variable_name: Masked Base64-encoded value
  used_template: Installation template used
  version: Gear version
```

**Important**

If `.state.yaml` does **not contain the `source` field**, rollback cannot be performed automatically.

To enable rollback:
1. Re-run the `install` command using the **currently installed gear's path or registry link**.
2. git-system-follower will detect the source and update `.state.yaml`.
3. After this, rollback to older versions will work normally.