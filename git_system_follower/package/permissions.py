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

""" Module with token permission checks and requirement detection

A single place to detect which GitLab access level a package/repository operation
requires and to validate that the provided token has it. It is meant to be called
from multiple places depending on the moment the requirement becomes known:

    - statically, right after a package description file is parsed
      (description/icon => Owner) via ``detect_package_requirements``;
    - at the execution point, when a package api actually performs an operation
      (CI/CD variables/webhooks => Maintainer) via ``register_requirement``.

Whenever the current token is insufficient the run is aborted with a clear
message naming the required role and the reason, before any merge request or
push is made.
"""
import sys
from dataclasses import dataclass
from enum import IntEnum

from gitlab.v4.objects import Project

from git_system_follower.logger import logger
from git_system_follower.typings.package import PackageLocalData


__all__ = [
    'AccessLevel', 'Requirements', 'detect_package_requirements',
    'register_requirement', 'reset_registered_requirements',
    'get_registered_requirements', 'get_effective_access_level', 'check_token_permissions'
]


class AccessLevel(IntEnum):
    """ GitLab project access levels (https://docs.gitlab.com/ee/user/permissions.html) """
    DEVELOPER = 30
    MAINTAINER = 40
    OWNER = 50


_ACCESS_LEVEL_NAMES = {
    AccessLevel.DEVELOPER: 'Developer',
    AccessLevel.MAINTAINER: 'Maintainer',
    AccessLevel.OWNER: 'Owner',
}


@dataclass
class Requirements:
    """ Aggregated token requirements for a package/repository run

    The maximum required access level wins:
        - Owner for project metadata synchronization (description/icon/CI/CD catalog)
        - Maintainer for CI/CD variables and webhooks management
        - Developer for plain repository operations
    """
    needs_metadata_sync: bool = False
    needs_cicd_variables: bool = False
    needs_webhooks: bool = False

    def required_access(self) -> AccessLevel:
        """ The most privileged access level required by these requirements """
        if self.needs_metadata_sync:
            return AccessLevel.OWNER
        if self.needs_cicd_variables or self.needs_webhooks:
            return AccessLevel.MAINTAINER
        return AccessLevel.DEVELOPER

    @property
    def reasons(self) -> list[str]:
        reasons = []
        if self.needs_metadata_sync:
            reasons.append('project metadata synchronization (description/icon/CI/CD catalog)')
        if self.needs_cicd_variables:
            reasons.append('CI/CD variables management')
        if self.needs_webhooks:
            reasons.append('webhooks management')
        return reasons


def detect_package_requirements(package: PackageLocalData) -> Requirements:
    """ Statically detect token requirements from a parsed package description file

    Called as soon as the package.yaml contents are known (package_info stage),
    before any script is executed. description/icon presence means project
    metadata will be synchronized and, therefore, Owner access is required.

    :param package: local package info (data from package.yaml)
    :return: requirements detected from the package description file
    """
    return Requirements(
        needs_metadata_sync='description' in package or 'icon' in package,
    )


# ---------------------------------------------------------------------------
# Runtime registration (execution point)
#
# Whether a gear needs CI/CD variables/webhooks cannot be known from the
# package.yaml: it only becomes clear at the execution point, when a gear's
# script actually calls the package api functions. Those functions register
# what they need here.
# ---------------------------------------------------------------------------
_registered_reasons: dict[AccessLevel, list[str]] = {
    AccessLevel.DEVELOPER: [],
    AccessLevel.MAINTAINER: [],
    AccessLevel.OWNER: [],
}


def register_requirement(level: AccessLevel, reason: str) -> None:
    """ Register that the current run performed an operation requiring <level>

    :param level: required access level
    :param reason: human readable explanation of why the access level is needed
    """
    _registered_reasons[level].append(reason)


def reset_registered_requirements() -> None:
    """ Reset requirements registered during a run (per package, per branch, etc.) """
    for reasons in _registered_reasons.values():
        reasons.clear()


def get_registered_requirements() -> Requirements:
    """ Requirements accumulated from operations performed at the execution point """
    req = Requirements()
    if _registered_reasons[AccessLevel.OWNER]:
        req.needs_metadata_sync = True
    if _registered_reasons[AccessLevel.MAINTAINER]:
        req.needs_cicd_variables = True
        req.needs_webhooks = True
    return req


def _registered_reasons_for(requirements: Requirements) -> list[str]:
    """ Human readable reasons behind <requirements>

    Uses the actual reasons registered at the execution point (they name the
    exact operation, e.g. "CI/CD variable 'FOO' management"), falling back to
    the generic per-requirement reasons.
    """
    required = requirements.required_access()
    reasons = _registered_reasons[required]
    if reasons:
        return reasons
    return requirements.reasons


def access_level_name(level: AccessLevel) -> str:
    """ Human readable name of an access level """
    return _ACCESS_LEVEL_NAMES.get(level, str(level))


def get_effective_access_level(project: Project) -> AccessLevel:
    """ Determine the access level of the token's user on the given project

    Prefers the `permissions` section of the already fetched project attributes
    (no extra request). That attribute can go stale: python-gitlab's ``save()``
    replaces the object attributes with the update response, which does not carry
    ``permissions``. In that case the level is resolved from the authenticated
    user (``gl.user``, set by ``gl.auth()``) via the project membership list.

    :param project: GitLab project
    :return: effective access level (Developer is assumed when it cannot be resolved)
    """
    permissions = project.attributes.get('permissions') or {}
    project_access = (permissions.get('project_access') or {}).get('access_level') or 0
    group_access = (permissions.get('group_access') or {}).get('access_level') or 0
    level = max(project_access, group_access)
    if level:
        return AccessLevel(level)

    user = getattr(getattr(project.manager, 'gitlab', None), 'user', None)
    if user is not None:
        if getattr(user, 'is_admin', False):
            return AccessLevel.OWNER
        try:
            member = project.members_all.get(user.id)
            return AccessLevel(member.access_level)
        except Exception:
            pass
    return AccessLevel.DEVELOPER


def check_token_permissions(project: Project, requirements: Requirements | None = None) -> None:
    """ Abort with a clear message if the token cannot satisfy the requirements

    :param project: GitLab project
    :param requirements: requirements to validate; when None, requirements
                         registered at the execution point are used
    """
    if requirements is None:
        requirements = get_registered_requirements()
    required = requirements.required_access()
    effective = get_effective_access_level(project)
    if effective >= required:
        return

    reasons = _registered_reasons_for(requirements) or ['regular repository operations']
    logger.critical(
        f"Token has {access_level_name(effective)} access, but {access_level_name(required)} access "
        f"is required for {project.path_with_namespace}. Required because: {', '.join(reasons)}. "
        f"Please use a token with sufficient permissions."
    )
    sys.exit(1)
