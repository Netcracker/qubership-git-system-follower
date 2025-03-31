# download
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
   1. **[download](download.md)**
   2. [install](install.md) 
   3. [list](list.md)
   4. [uninstall](uninstall.md)
   5. [version](version.md)
6. [API reference](../api_reference.md)  
   1. [Develop interface](../api_reference/develop_interface.md)  
      1. [types Module](../api_reference/develop_interface/types.md)
      2. [cicd_variables Module](../api_reference/develop_interface/cicd_variables.md)
      3. [templates Module](../api_reference/develop_interface/templates.md)

---

Download gears

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
```plaintext
$ gsf packages download artifactory.company.com/my-image:1.0.0 -d packages

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

Downloading package (next times)
```plaintext
$ gsf packages download artifactory.company.com/my-image:1.0.0 -d packages

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
The images don't download because the git-system-follower has remembered what it downloaded and 
where it downloaded it to: it uses its `.git-system-follower/packages` directory and `.git-system-follower/image-package-map.json` file
to map the image to the package directory it downloaded (see [Image-to-package mapping](#image-to-package-mapping))

## Advanced
### Authentication Methods for Registry Access
You can work with private registries by providing authentication credentials.

There are three ways to specify credentials, listed in order of priority: 
1. Pass the credentials directly using `--registry-username` and `--registry-password`
2. Credentials can be provided via stdin using `echo`: `echo -e "<username>\n<password>" | gsf download ...`
3. Set `GSF_REGISTRY_USERNAME` and `GSF_REGISTRY_PASSWORD` as environment variables

If multiple methods are used, command-line parameters take precedence over stdin, and stdin takes precedence over environment variables.

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