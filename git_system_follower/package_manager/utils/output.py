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

from typing import Iterable, Callable

from git_system_follower.package_manager.typings.package import PackageLocalData


__all__ = ['print_dependency_tree_one_level']


def print_dependency_tree_one_level(
        packages: Iterable[PackageLocalData], title='', *,
        key: Callable, output_func: Callable = print
) -> None:
    """ Print dependency tree

    :param packages: packages which need to print
    :param title: title of tree
    :param key: function for filtering the information from the list
    :param output_func: output function
    """
    content = f'{title}:\n'
    for i, package in enumerate(packages, 1):
        content += f'{i}. {key(package)}\n'
        prefix = ' ' * len(str(i)) + '  '  # spaces before connector to level the tree
        for j, dependency in enumerate(package['dependencies']):
            connector = '└── ' if j == len(package['dependencies']) - 1 else '├── '
            content += f'{prefix}{connector}{dependency}\n'

    if content[-1] == '\n':
        content = content[:-1]
    output_func(content)
