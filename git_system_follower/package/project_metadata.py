# Copyright 2024-2025 NetCracker Technology Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""" Module with core functions to manage project metadata from package.yaml """
import gitlab
import logging
import hashlib
from urllib.parse import urlparse
from git_system_follower.develop.api.v2.types import GraphQLClient, ProjectMetadata
from git_system_follower.package.permissions import AccessLevel, check_token_permissions, register_requirement
from git_system_follower.typings.package import PackageLocalData
from git_system_follower.typings.repository import RepositoryInfo
from git_system_follower.utils.utility import get_current_avatar_hash
from git_system_follower.logger import logger

logging.getLogger("httpx").setLevel(logging.WARNING)

class PackageMetadataError(Exception):
    pass

def initialize_metadata(package: PackageLocalData, repo: RepositoryInfo) -> None:
    """Initialize ProjectMetadata and GraphQLClient singletons before running
    a package's scripts, so the scripts see exactly this package's metadata.

    No-op for packages that carry no `description`/`icon` (nothing to sync).
    """
    if 'description' not in package or 'icon' not in package:
        return
    ProjectMetadata().initialize(
        description=package["description"],
        icon=package["icon"],
    )
    parsed_url = urlparse(repo.gitlab.manager.gitlab.url)
    gitlab_root = f"{parsed_url.scheme}://{parsed_url.netloc}"
    GraphQLClient().initialize(url=gitlab_root, token=repo.token)

def sync_project_metadata(parameters, script_dir) -> None:
    """Sync project description, icon, and CI/CD catalog from ProjectMetadata."""
    ctx = ProjectMetadata()
    project = parameters._Parameters__system_params.project

    # Project metadata synchronization is an Owner-level operation. It is only
    # registered when there is actually metadata (or a catalog extra) to sync:
    # ctx is initialized per-package, right before the scripts run, and only
    # when the package.yaml carries description/icon (see initialize_metadata).
    has_catalog_extra = any(name == "gitlab_cicd_project_catalog" for name in parameters.extras)
    if ctx._data is not None or has_catalog_extra:
        register_requirement(AccessLevel.OWNER, "project metadata synchronization (description/icon/CI/CD catalog)")
        check_token_permissions(project)

    try:
        logger.info("==> Project metadata synchronization")

        needs_save = False

        needs_save |= sync_description(project, ctx)
        needs_save |= sync_icon(project, ctx, script_dir)
        needs_save |= sync_catalog(project, ctx, parameters)

        if needs_save:
            project.save()

    except gitlab.GitlabError as e:
        raise PackageMetadataError(f"GitLab API error: {e}") from e

def sync_description(project, ctx) -> bool:
    if ctx.description and project.attributes.get("description") != ctx.description:
        project.description = ctx.description
        logger.info(f"\tSetting project description to: {ctx.description}")
        return True

    logger.info("\tNo changes to project description")
    return False

def sync_icon(project, ctx, script_dir) -> bool:
    if ctx.icon is None:
        # No icon declared: leave any existing avatar untouched. The avatar may
        # have been set by another package, externally, or by a previous version
        # of this gear -- it is not ours to remove.
        logger.info("\tNo icon declared. Skipping icon synchronization")
        return False

    current_hash = get_current_avatar_hash(project)
    with open(script_dir / ctx.icon, "rb") as f:
        ctx.icon_hash = hashlib.sha256(f.read()).hexdigest()

    if current_hash == ctx.icon_hash:
        logger.info("\tNo changes to project icon")
        return False

    icon_file = script_dir / ctx.icon
    if not icon_file.exists():
        raise PackageMetadataError(f"\tIcon not found: {icon_file}")

    with open(icon_file, "rb") as f:
        project.avatar = f.read()

    logger.info(f"\tSetting project icon from {icon_file}")
    return True

def sync_catalog(project, ctx, parameters) -> bool:
    for name, extra in parameters.extras.items():
        if name != "gitlab_cicd_project_catalog":
            continue
        desired_status = (
            extra.value.lower() == "true"
            if isinstance(extra.value, str)
            else extra.value
        )

        current_status = get_catalog_status(project)
        logger.info(
            f"\tCurrent CI/CD catalog status: {current_status}, "
            f"Desired status: {desired_status}"
        )

        if current_status == desired_status:
            return False
        update_catalog(project, ctx, desired_status)
        return True

    return False

def update_catalog(project, ctx, desired_status: bool) -> None:
    gq = GraphQLClient().client
    logger.info(f"\t{'Enabling' if desired_status else 'Disabling'} CI/CD catalog")
    if desired_status:
        mutation = """
            mutation($projectPath: ID!) {
                catalogResourcesCreate(input: {projectPath: $projectPath}) {
                    errors
                }
            }
        """
        result = gq.execute(
            mutation,
            variable_values={"projectPath": project.path_with_namespace},
        )

        errors = result.get("catalogResourcesCreate", {}).get("errors", [])

    else:
        mutation = """
            mutation($projectPath: ID!) {
                catalogResourcesDestroy(input: {projectPath: $projectPath}) {
                    errors
                }
            }
        """
        result = gq.execute(
            mutation,
            variable_values={"projectPath": project.path_with_namespace},
        )

        errors = result.get("catalogResourcesDestroy", {}).get("errors", [])

    if errors:
        action = "enable" if desired_status else "disable"
        raise PackageMetadataError(
            f"Failed to {action} CI/CD catalog: {errors}"
        )
    ctx.cicd_catalog = desired_status
    logger.info(f"\tCI/CD catalog updated to {desired_status}")

def get_catalog_status(project) -> bool:
    gq = GraphQLClient().client

    query = """
        query checkCatalogStatus($projectPath: ID!) {
            project(fullPath: $projectPath) {
                isCatalogResource
            }
        }
    """

    result = gq.execute(
        query,
        variable_values={"projectPath": project.path_with_namespace},
    )

    return result.get("project", {}).get("isCatalogResource", False)
