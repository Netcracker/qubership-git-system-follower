# download

Downloading all listed gears (docker images) and then finding the package layer in that image
and saving it as `.tar.gz` file

## Display help text
To list the help on any command just execute the command, followed by the `--help` option
```bash
gsf download --help
```

## Arguments
| Name    | Description                                                                | Example                                            |
|---------|----------------------------------------------------------------------------|----------------------------------------------------|
| `GEARS` | Download all listed gears as image: `<registry>/<repository>/<name>:<tag>` | `artifactory.company.com/path-to/your-image:1.0.0` |

## Options
| Name                  | Description                                                              | Mandatory |      Default value      |  Environment variable   | Example                                           |
|-----------------------|--------------------------------------------------------------------------|:---------:|:-----------------------:|:-----------------------:|---------------------------------------------------|
| `-d`, `--directory`   | Directory where gears will be downloaded                                 |     -     | `.` (Current directory) |            -            | `/opt/gsf-packages`                               |
| `--registry-type`     | Specify the registry type or use automatic detection                     |     -     |      `Autodetect`       |            -            | `Autodetect`, `Dockerhub`, `Artifactory`, `Nexus` |
| `--registry-username` | Username for basic authentication in the registry when downloading Gears |     -     |            -            | `GSF_REGISTRY_USERNAME` | `myusername`, `k1shk1n`                           |
| `--registry-password` | Password for basic authentication in the registry when downloading Gears |     -     |            -            | `GSF_REGISTRY_PASSWORD` | `MyPa$$w0rd`                                      |
| `--insecure-registry` | Allow insecure connections to the registry (use HTTP instead of HTTPS)   |     -     |         `False`         |            -            |                                                   |
| `--debug`             | Show debug level messages                                                |     -     |         `False`         |            -            |                                                   |
               
## Examples
Downloading the package (for the first time)
<!-- TODO: add an example of a package that will not be lost (released package). So that users can try it out -->

```bash
gsf download artifactory.company.com/my-image:1.0.0 -d packages
```

<div class="result" markdown>
```plaintext
[04:26:54.404] INFO     |
     .-,
  .^.: :.^.    ┏┓╻┳ ┏┓╻╻┏┓┳┏┓┏┳┓ ┏┓┏┓╻ ╻ ┏┓┏ ┓┏┓┳┓
 ,-' .-. '-,   ┃┓┃┃ ┗┓┗┃┗┓┃┣ ┃┃┃ ┣ ┃┃┃ ┃ ┃┃┃┃┃┣ ┣┛
 '-. '-' .-'   ┗┛╹╹ ┗┛┗┛┗┛╹┗┛╹ ╹ ╹ ┗┛┗┛┗┛┗┛┗┻┛┗┛┛┗
  '.`; ;`.'    git-system-follower v0.0.1
     `-`
[04:26:54.404] INFO     |
╭════════════════════════════════════════ Start parameters ════════════════════════════════════════╮
  gears             = artifactory.company.com/my-image:1.0.0
  directory         = /home/tests/packages
  registry_type     = Autodetect
  registry-username =
  registry-password =
  insecure-registry =
  debug             = False
╰══════════════════════════════════════════════════════════════════════════════════════════════════╯
[04:26:54.405] INFO     | :: Downloading packages
[04:26:54.405] INFO     | -> Downloading artifactory.company.com/my-image:1.0.0
[04:26:54.424] INFO     | artifactory.company.com is of type Artifactory
[04:26:55.461] INFO     | my-gear@1.0.0 package is provided as docker image (Image: artifactory.company.com/my-image:1.0.0)
[04:26:55.461] SUCCESS  | Downloaded package from artifactory.company.com/my-image:1.0.0 to packages/my-gear@1.0.0.tar.gz
[04:26:55.465] SUCCESS  | Download complete
```
</div>

Downloading package (next times):

```bash
gsf download artifactory.company.com/my-image:1.0.0 -d packages
```

<div class="result" markdown>

```plaintext
[04:44:11.786] INFO     |
    .-,
 .^.: :.^.   ┏┓╻┳ ┏┓╻╻┏┓┳┏┓┏┳┓ ┏┓┏┓╻ ╻ ┏┓┏ ┓┏┓┳┓
,-' .-. '-,  ┃┓┃┃ ┗┓┗┃┗┓┃┣ ┃┃┃ ┣ ┃┃┃ ┃ ┃┃┃┃┃┣ ┣┛
'-. '-' .-'  ┗┛╹╹ ┗┛┗┛┗┛╹┗┛╹ ╹ ╹ ┗┛┗┛┗┛┗┛┗┻┛┗┛┛┗
 '.`; ;`.'   git-system-follower v0.0.1
    `-`
[04:44:11.786] INFO     |
╭════════════════════════════════════════ Start parameters ════════════════════════════════════════╮
  gears     = artifactory.company.com/my-image:1.0.0
  directory = /home/tests/packages
  debug     = False
╰══════════════════════════════════════════════════════════════════════════════════════════════════╯
[04:44:11.787] INFO     | :: Downloading packages
[04:44:11.787] INFO     | -> Downloading artifactory.company.com/my-image:1.0.0
[04:44:11.789] INFO     | my-gear@1.0.0 package is provided as docker image (Image: artifactory.company.com/my-image:1.0.0)
[04:44:11.789] INFO     | Package has already been downloaded to packages/my-gear@1.0.0.tar.gz from artifactory.company.com/my-image:1.0.0. Skip downloading
[04:44:11.790] SUCCESS  | Download complete
```

</div>

The images don't download because the git-system-follower has remembered what it downloaded and 
where it downloaded it to: it uses its `.git-system-follower/packages` directory and `.git-system-follower/image-package-map.json` file
to map the image to the package directory it downloaded (see [Image-to-package mapping](#image-to-package-mapping))

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
aws ecr get-authorization-token --output text --query 'authorizationData[].authorizationToken' | gsf download ...
```

!!! note
    AWS ECR does not use Bearer authentication. Instead, it relies on **Basic** authentication, 
    where the **username** is literally `AWS`, and the **password** is a temporary token (which lasts for 12 hours) obtained 
    via `aws ecr get-authorization-token`.

### Why docker is not a required
When the git-system-follower downloads the docker image it doesn't need `docker` because we use the `oras` library
(it doesn't use the docker socket)

### Downloading process
git-system-follower downloads the image using the `oras` library, finds the layer that contains the gear source code.
It saves this layer (`.tar.gz`) to the passed directory, extracts it to the `.git-system-follower/packages` directory
to figure out what file name to assign to this `.tar.gz` archive like `<name>@<version>.tar.gz` and for next following
use: installation, uninstallation

### Image-to-package mapping
In order not to download the same image repeatedly because of possible differences between the image name and version
and the name and version of the gear itself (from `package.yaml`), an additional logic of saving
image-to-package mapping in a separate file was made - `.git-system-follower/image-package-map.json`

git-system-follower compares the gears with and images that are specified in `.git-system-follower/image-package-map.json` file with
the package names in the `.git-system-follower/packages` directory. If there is no such comparison, or if there is a comparison but no gear, 
git-system-follower will download the gear