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

""" v2 api with types for package developers (re-exported from common) """
import hashlib
import gitlab
from git_system_follower.develop.api.common.types import (
    Parameters, SystemParameters, System,
    CICDVariable, CICDVariables, CICDVariableName,
    ExtraParam, ExtraParams, ExtraParamName,
    Webhook, Webhooks, WebhookURL
)
from typing import Optional
from dataclasses import dataclass
from git_system_follower.utils.singleton import Singleton


@dataclass(frozen=True)
class ProjectMetadataData:
    description: Optional[str] = None
    icon: Optional[str] = None


class ProjectMetadata(Singleton):
    def __init__(self):
        if not hasattr(self, '_data'):
            self._data: Optional[ProjectMetadataData] = None
            self._cicd_catalog: bool = False

    def initialize(self, description: Optional[str] = None,
        icon: Optional[str] = None, cicd_catalog: bool = False) -> 'ProjectMetadata':
        # Re-initializable on purpose: a single process runs scripts for
        # multiple packages (e.g. delete old + init new during a rollback),
        # and each package's scripts must see exactly its own metadata.
        self._data = ProjectMetadataData(description, icon)
        self._cicd_catalog = cicd_catalog
        self._icon_hash = hashlib.sha256(icon.encode()).hexdigest() if icon else ""
        return self

    @property
    def description(self) -> Optional[str]:
        if self._data is None:
            raise RuntimeError("ProjectMetadata not initialized")
        return self._data.description

    @property
    def icon(self) -> Optional[str]:
        if self._data is None:
            raise RuntimeError("ProjectMetadata not initialized")
        return self._data.icon

    @property
    def cicd_catalog(self) -> bool:
        return self._cicd_catalog

    @cicd_catalog.setter
    def cicd_catalog(self, value: bool) -> None:
        self._cicd_catalog = value

    @property
    def icon_hash(self) -> str:
        if self._data is None:
            raise RuntimeError("ProjectMetadata not initialized")
        return self._icon_hash

    @icon_hash.setter
    def icon_hash(self, value: str) -> None:
        self._icon_hash = value

@dataclass(frozen=True)
class GraphQLClientData:
    client: gitlab.GraphQL


class GraphQLClient(Singleton):
    def __init__(self):
        if not hasattr(self, '_data'):
            self._data: Optional[GraphQLClientData] = None

    def initialize(self, url: str, token: str) -> 'GraphQLClient':
        # The gitlab root URL and token are constant for the whole process,
        # so creating the client more than once is neither needed nor cheap.
        if self._data is None:
            self._data = GraphQLClientData(gitlab.GraphQL(url, token=token))
        return self

    @property
    def client(self) -> gitlab.GraphQL:
        if self._data is None:
            raise RuntimeError("GraphQLClient not initialized")
        return self._data.client

__all__ = [
    'Parameters', 'SystemParameters', 'System',
    'CICDVariable', 'CICDVariables', 'CICDVariableName',
    'ExtraParam', 'ExtraParams', 'ExtraParamName',
    'Webhook', 'Webhooks', 'WebhookURL',
    'ProjectMetadata', 'GraphQLClient'
]
