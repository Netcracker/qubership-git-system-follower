# Package api reference
## Documentation
1. [Docs Home](docs_home.md)
2. [Getting Started Guides](getting_started.md) 
   1. [Quickstart Guide](getting_started/quickstart.md)
   2. [Installation Guide](getting_started/installation.md)
3. [Concepts Guides](concepts.md)  
   1. [Gears Guide](concepts/gears.md)
   2. [apiVersion list](concepts/api_version_list.md)
      1. [apiVersion v1](concepts/api_version_list/v1.md) 
   3. [.state.yaml Guide](concepts/state.md)
4. [How-to Guides](how_to.md)  
   1. [Build Guide](how_to/build.md)
   2. [Gear Development Cases](how_to/gear_development_cases.md)
   3. [Integration with semantic-release](how_to/integration_with_semantic_release.md)
5. [CLI reference](cli_reference.md) 
   1. [download](cli_reference/download.md)
   2. [install](cli_reference/install.md) 
   3. [list](cli_reference/list.md)
   4. [uninstall](cli_reference/uninstall.md)
   5. [version](cli_reference/version.md)
6. **[API reference](api_reference.md)**  
   1. [Develop interface](api_reference/develop_interface.md)  
      1. [types Module](api_reference/develop_interface/types.md)
      2. [cicd_variables Module](api_reference/develop_interface/cicd_variables.md)
      3. [templates Module](api_reference/develop_interface/templates.md)

---

git-system-follower provides an interface for developers for creating/deleting CI/CD variables
and generate/update/delete a `cookiecutter` template in a repository branch

## General information
git-system-follower always calls `main` function from package api with `parameters` argument which are of type
`Parameters` from `git_system_follower.develop.api.types`

