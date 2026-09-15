# template

Render gear templates using cookiecutter and show the generated files in stdout.

This command works like `gsf install` — it accepts gear specifications (Docker image,
tar.gz archive, or source directory), downloads them (with registry credentials if needed),
finds the templates included in the gear, and renders them.

## Display help text
To list the help on any command just execute the command, followed by the `--help` option
```bash
gsf template --help
```

## Arguments
| Name | Description | Example |
|------|-------------|---------|
| `GEARS` | One or more gears to render templates from, specified as: <ul><li>`image`: `<registry>/<repository>/<name>:<tag>`, e.g. `artifactory.company.com/path-to/your-image:1.0.0`</li><li>`tar.gz` archive: `/path/to/archive.tar.gz`, e.g. `your-archive@1.0.0.tar.gz`</li><li>`source` directory: `/path/to/gear`, e.g. `your-gear@1.0.0`</li></ul> | `my-gear@1.0.0` |

## Options
| Name | Description | Mandatory | Default value | Environment variable | Example |
|------|-------------|:---------:|:-------------:|:--------------------:|---------|
| `--extravar` | Extra context variable for template rendering: variable name and value (repeatable) | - | - | - | `project_name my-proj` |
| `--registry-type` | Specify the registry type or use automatic detection | - | `Autodetect` | - | `Autodetect`, `Dockerhub`, `Artifactory`, `Nexus` |
| `--registry-username` | Username for basic authentication in the registry when downloading Gears | - | - | `GSF_REGISTRY_USERNAME` | `myusername` |
| `--registry-password` | Password for basic authentication in the registry when downloading Gears | - | - | `GSF_REGISTRY_PASSWORD` | `MyPa$$w0rd` |
| `--insecure-registry` | Allow insecure connections to the registry (use HTTP instead of HTTPS) | - | `False` | - | |
| `-d`, `--directory` | Directory where generated files will be written. If not specified, a preview is shown in stdout | - | - | - | `/opt/gsf-templated` |
| `-o`, `--output` | File where the rendered template output will be captured (instead of stdout) | - | - | - | `/opt/gsf-templated/preview.txt` |
| `--debug` | Show debug level messages | - | `False` | - | |

!!! note
    The **banner**, the **start-parameters box**, and the final **"written to ..."**
    confirmation messages are printed by the logger to **stderr**.
    The examples below show the **stdout** output only, which is exactly what the
    `template` command is designed to produce.

## Authentication
When the gear is a Docker image from a registry, the `--registry-username` and
`--registry-password` options (or `GSF_REGISTRY_USERNAME`/`GSF_REGISTRY_PASSWORD`
environment variables) are used to authenticate the image download.
Credentials are resolved in the following priority order:

1. Command-line parameters (`--registry-username` / `--registry-password`)
2. Stdin: `echo "<username>:<password>" | gsf template ...`
3. Environment variables (`GSF_REGISTRY_USERNAME` / `GSF_REGISTRY_PASSWORD`)
4. Interactive prompt if only one of username/password is specified

Command-line parameters take precedence over stdin, and stdin takes precedence over
environment variables.

## Examples
Render templates from a gear and show what files they would look like (stdout only):

```bash
gsf template my-gear@1.0.0 --extravar project_name my-proj
```

<div class="result" markdown>

```plaintext
Package: my-gear@1.0.0
Available templates: default
Generated files (1):
  1. README.md

Preview (what the generated files look like):

--- README.md ---
# my-proj

Project generated from the template.
```

</div>

Render templates from a gear and write the generated files into a directory:

```bash
gsf template my-gear@1.0.0 -d /opt/gsf-templated --extravar project_name my-proj
```

<div class="result" markdown>

```plaintext
Package: my-gear@1.0.0
Available templates: default
Generated files (1):
  1. README.md

Preview (what the generated files look like):

--- README.md ---
# my-proj

Project generated from the template.
```

</div>

The `Files have been written to /opt/gsf-templated` confirmation is printed to **stderr**
(see note above), in addition to the stdout preview shown above.

Render templates from a gear and capture the preview output into a file instead of stdout:

```bash
gsf template my-gear@1.0.0 -o /opt/gsf-templated/preview.txt --extravar project_name my-proj
```

Stdout is empty — the preview is written to `/opt/gsf-templated/preview.txt` instead.
Only the confirmation message is printed to **stderr**:

<div class="result" markdown>

```plaintext
Template output written to /opt/gsf-templated/preview.txt
```

</div>

Render a gear from a Docker registry using basic authentication:

```bash
gsf template my-registry.io/my-gear:1.0.0 --registry-username myusername --registry-password MyPa$$w0rd
```

<div class="result" markdown>

```plaintext
Package: my-gear@1.0.0
Available templates: default
Generated files (1):
  1. README.md

Preview (what the generated files look like):

--- README.md ---
# my-proj

Project generated from the template.
```

</div>