<div align="center">
<br />

<img src="https://raw.githubusercontent.com/Netcracker/qubership-git-system-follower/master/docs/assets/logo.svg" alt="git-system-follower logo" width="100">

# git-system-follower
**git-system-follower (gsf)** is a package manager for Git providers.

[![PyPI](https://img.shields.io/pypi/v/qubership-git-system-follower)](https://pypi.org/project/qubership-git-system-follower/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/qubership-git-system-follower)
![Build](https://github.com/Netcracker/qubership-git-system-follower/actions/workflows/checks.yaml/badge.svg)
![Repo Size](https://img.shields.io/github/repo-size/Netcracker/qubership-git-system-follower)
[![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

[:eyes: Overview](#eyes-overview) •
[:wrench: Problems It Solves](#wrench-problems-it-solves) •
[:star2: Key Features](#star2-key-features) •
[:dart: Key Beneficiaries](#dart-key-beneficiaries) •
[:package: Install](#package-install) •
[:page_with_curl: Docs](#page_with_curl-docs)


Supported resources

Git providers
![GitLab](https://img.shields.io/badge/GitLab-%231E1E1E.svg?style=flat&logo=gitlab&logoColor=orange)
•
Gear registries
![Dockerhub](https://img.shields.io/badge/Dockerhub-%230db7ed.svg?style=flat&logo=docker&logoColor=white)
![Artifactory](https://img.shields.io/badge/Artifactory-%41bf47.svg?style=flat)
![Nexus](https://img.shields.io/badge/Nexus-%333333.svg?style=flat)

</div>

## :eyes: Overview
**gsf** designed to streamline the management of repository branch content and configuration.
By automating installations, updates, and removals, **gsf** reduces manual intervention,
prevents errors, and ensures a consistent state across projects.

If you’re managing CI/CD pipelines, infrastructure configurations, or any repository-bound tools,
**gsf** is here to make your work easier, faster, and more reliable using [Git packages, aka Gears](https://netcracker.github.io/qubership-git-system-follower/latest/concepts/gears/).

## :wrench: Problems It Solves
Have you used versioned `.gitlab-ci.yml` that require a specific file structure in the repository?

If so, you've probably encountered configuration issues: you forgot to specify
a mandatory parameter, didn't create the right file, and eventually the Pipeline
doesn't work. Or maybe everything was working, and suddenly the Pipeline starts crashing
for no apparent reason - and you waste time figuring out that someone accidentally changed
the startup parameters. And if you need to update an old `.gitlab-ci.yml` to the latest version,
you often have to manually migrate through multiple versions.

**gsf solves all of these problems** by automatically managing your config file version
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
See [Installation Guide](https://netcracker.github.io/qubership-git-system-follower/latest/getting_started/installation/).

## :page_with_curl: Docs
Get started with the [Quick Start Guide](https://netcracker.github.io/qubership-git-system-follower/latest/getting_started/quickstart/) or plunge into the [complete documentation](https://netcracker.github.io/qubership-git-system-follower/latest/home/).

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
