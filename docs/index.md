**git-system-follower (gsf)** is a package manager for Git providers.

[![PyPI](https://img.shields.io/pypi/v/qubership-git-system-follower)](https://pypi.org/project/qubership-git-system-follower/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/qubership-git-system-follower)
![Build](https://github.com/Netcracker/qubership-git-system-follower/actions/workflows/checks.yaml/badge.svg)
![Repo Size](https://img.shields.io/github/repo-size/Netcracker/qubership-git-system-follower)
[![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

<div class="grid cards" markdown>

- **Supported Git providers**  

    ---

    :simple-gitlab: Gitlab

- **Supported Gear registries**

    ---

    :simple-docker: Dockerhub  
    :simple-jfrog: Artifactory  
    :simple-sonatype: Nexus

</div>

## Overview
**gsf** designed to streamline the management of repository branch content and configuration.
By automating installations, updates, and removals, **gsf** reduces manual intervention,
prevents errors, and ensures a consistent state across projects.

If you’re managing CI/CD pipelines, infrastructure configurations, or any repository-bound tools,
**gsf** is here to make your work easier, faster, and more reliable using [Git packages, aka Gears](concepts/gears.md).

## Problems It Solves
Have you used versioned `.gitlab-ci.yml` that require a specific file structure in the repository?

If so, you've probably encountered configuration issues: you forgot to specify
a mandatory parameter, didn't create the right file, and eventually the Pipeline
doesn't work. Or maybe everything was working, and suddenly the Pipeline starts crashing
for no apparent reason - and you waste time figuring out that someone accidentally changed
the startup parameters. And if you need to update an old `.gitlab-ci.yml` to the latest version,
you often have to manually migrate through multiple versions.

**gsf solves all of these problems** by automatically managing your config file version
and structure, eliminating all of these errors and saving you a lot of work:

<div class="grid cards" markdown>

- :material-hand-back-right-off-outline: **Reduced manual work**

    ---

    Package developers handle installation and updates automatically, eliminating manual configuration work.

- :material-update: **Version management** 

    ---

    Supports automated migrations between versions to ensure smooth updates without errors.

- :material-file-check: **Preserving user changes**

    ---

    Smart file comparison prevents overwriting custom modifications during updates.

- :material-security: **Security and control**
    
    ---

    Tracks installed packages in `.state.yaml` with hash verification to prevent unauthorized changes.

</div>

## Key Features
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

## Key Beneficiaries
DevOps engineers, SRE engineers and other professionals working with GitOps repositories, for example, configuring projects linked to ArgoCD, GitLab CI/CD, or similar tools.

## Install
See [Installation Guide](getting_started/installation.md).

## Docs
Get started with the [Quick Start Guide](getting_started/quickstart.md) or plunge into the [complete documentation](home.md).

## Contributing 
* [CODE-OF-CONDUCT.md](https://github.com/Netcracker/qubership-git-system-follower/blob/main/CODE-OF-CONDUCT.md)  
This document outlines the expected behavior for everyone interacting with the project. It fosters a respectful and inclusive environment for developers, contributors, and users.

* [CONTRIBUTING.md](https://github.com/Netcracker/qubership-git-system-follower/blob/main/CONTRIBUTING.md)  
This document acts as a guide for anyone interested in contributing to the project. It clarifies the contribution process and helps maintainers manage contributions effectively.

* [SECURITY.md](https://github.com/Netcracker/qubership-git-system-follower/blob/main/SECURITY.md)  
This document focuses on security practices and reporting vulnerabilities. It aims to promote a secure development environment and responsible handling of security issues.

## Changelog
Detailed changes for each release are documented in the **TBD**.

## License
[Apache License 2.0](https://github.com/Netcracker/qubership-git-system-follower/blob/main/LICENSE)
