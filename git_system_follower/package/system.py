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

""" Module for defining system information, such as gitlab domain on which package will be installed """

from urllib.parse import urlparse

from gitlab.v4.objects import Project

from git_system_follower.develop.api.types import System, ExtraParams


__all__ = ['get_system_info']


DOMAIN_VAR_NAME = 'GSF_HOST_DOMAIN'


def get_system_info(project: Project, extras: ExtraParams) -> System:
    """ Get system information

    :param project: gitlab project
    :param extras: extra parameters to be passed to package api
    :return: system information
    """
    if DOMAIN_VAR_NAME in extras.keys():
        domain = extras[DOMAIN_VAR_NAME].value
    else:
        domain = urlparse(project.http_url_to_repo).netloc
    return System(host_domain=domain)
