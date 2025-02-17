<div align="center">
<br />
<img src="/logo.svg" alt="git-system-follower logo" width="100">

# git-system-follower
**git-system-follower (GSF)** is a package manager for Git providers.

[:eyes: Overview](#eyes-overview) •
[:wrench: Problems It Solves](#wrench-problems-it-solves) •
[:star2: Key Features](#star2-key-features) •
[:dart: Key Beneficiaries](#dart-key-beneficiaries) •
[:package: Install](#package-install) •
[:page_with_curl: Docs](#page_with_curl-docs)

</div>

## :eyes: Overview
**GSF** designed to streamline the management of repository branch content and configuration.
By automating installations, updates, and removals, **GSF** reduces manual intervention,
prevents errors, and ensures a consistent state across projects.

If you’re managing CI/CD pipelines, infrastructure configurations, or any repository-bound tools,
**GSF** is here to make your work easier, faster, and more reliable using [Git packages, aka Gears](docs/concepts/gears.md).

## :wrench: Problems It Solves
Have you used versioned `.gitlab-ci.yml` that require a specific file structure in the repository?

If so, you've probably encountered configuration issues: you forgot to specify
a mandatory parameter, didn't create the right file, and eventually the Pipeline
doesn't work. Or maybe everything was working, and suddenly the Pipeline starts crashing
for no apparent reason - and you waste time figuring out that someone accidentally changed
the startup parameters. And if you need to update an old `.gitlab-ci.yml` to the latest version,
you often have to manually migrate through multiple versions.

**GSF solves all of these problems** by automatically managing your config file version
and structure, eliminating all of these errors and saving you a lot of work:

* **Reduced manual work**  
Engineers no longer need to handle installation or updates manually — **this is done by the package
developer**, who knows all the details.

* **Version management**  
The package manager supports **migrations between versions**. When updating, it automatically
performs intermediate steps, ensuring no errors occur from skipping versions.

* **Preserving user changes**  
During template generation, the tool **carefully compares files** to avoid overwriting
user-made changes.

* **Security and control**  
The state of all installed packages is stored in a special `.state.yaml` file.
The data inside is hashed to **prevent unauthorized changes or misuse**.

## :star2: Key Features
* **Works only with repository branch content**  
The manager operates exclusively within branches, managing the repository’s content
without altering branches, commits, or other repository elements.

* **GitLab-specific support**  
The current implementation is tailored to work with GitLab repositories.

* **Package installation**  
Quickly add new tools or configurations to a repository.

* **Package updates**  
Ensure smooth migrations between versions.

* **Package removal**  
Completely remove configurations and tools without leaving traces.

* **Variable management**  
Add or update variables in CI/CD systems like GitLab.

* **Template generation**  
Create configuration files while considering existing settings and user changes.

* **Developer interface**  
Provides API and tools for package developers to define how their packages
are installed, updated, and removed. This ensures that package developers can define
migration steps and other actions with precision.

## :dart: Key Beneficiaries
DevOps engineers, SRE engineers and other professionals working with GitOps repositories, for example, configuring projects linked to ArgoCD, GitLab CI/CD, or similar tools.

## :package: Install
See [Installation Guide](docs/getting_started/installation.md).

## :page_with_curl: Docs
Get started with the [Quick Start Guide](docs/getting_started/quickstart.md) or plunge into the [complete documentation](docs/docs_home.md).

### Navigation
1. [Docs Home](docs/docs_home.md)
2. [Getting Started Guides](docs/getting_started.md)  
   1. [Quickstart Guide](docs/getting_started/quickstart.md)
   2. [Installation Guide](docs/getting_started/installation.md)
3. [Concepts Guides](docs/concepts.md)  
   1. [Gears Guide](docs/concepts/gears.md)
   2. [apiVersion list](docs/concepts/api_version_list.md)
      1. [apiVersion v1](docs/concepts/api_version_list/v1.md) 
   3. [.state.yaml Guide](docs/concepts/state.md)
   4. [Plugins Guide](docs/concepts/plugins.md)
      1. [CLI Arguments Extension Point](docs/concepts/plugins/cli_arguments.md)
4. [How-to Guides](docs/how_to.md)  
   1. [Build Guide](docs/how_to/build.md)
   2. [Gear Development Cases](docs/how_to/gear_development_cases.md)
   3. [Integration with semantic-release](docs/how_to/integration_with_semantic_release.md)
5. [CLI reference](docs/cli_reference.md) 
   1. [download](docs/cli_reference/download.md)
   2. [install](docs/cli_reference/install.md) 
   3. [list](docs/cli_reference/list.md)
   4. [uninstall](docs/cli_reference/uninstall.md)
   5. [version](docs/cli_reference/version.md)
6. [API reference](docs/api_reference.md)  
   1. [Develop interface](docs/api_reference/develop_interface.md)  
      1. [types Module](docs/api_reference/develop_interface/types.md)
      2. [cicd_variables Module](docs/api_reference/develop_interface/cicd_variables.md)
      3. [templates Module](docs/api_reference/develop_interface/templates.md)

## :handshake: Contributing 
* [CODE-OF-CONDUCT.md](CODE-OF-CONDUCT.md)  
This document outlines the expected behavior for everyone interacting with the project. It fosters a respectful and inclusive environment for developers, contributors, and users.

* [CONTRIBUTING.md](CONTRIBUTING.md)  
This document acts as a guide for anyone interested in contributing to the project. It clarifies the contribution process and helps maintainers manage contributions effectively.

* [SECURITY.md](SECURITY.md)  
This document focuses on security practices and reporting vulnerabilities. It aims to promote a secure development environment and responsible handling of security issues.

## :arrows_counterclockwise: Changelog
Detailed changes for each release are documented in the **TBD**.

## :black_nib: License
[Apache License 2.0](LICENSE)
