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

""" Module with output info related utils """
from typing import Mapping, Iterable, Callable, Sequence
import textwrap

from git_system_follower.typings.package import PackageLocalData


__all__ = ['print_params', 'print_list', 'banner', 'print_dependency_tree_one_level']


WIDTH = 100


def print_params(
        params: Mapping, title='', width: int = WIDTH,
        hidden_params: Iterable = (), *,
        output_func: Callable = print
) -> None:
    """ Print parameters as "window" from value as dict

    :param params: value as dict: key/value
    :param title: window's title
    :param width: parameters window width
    :param hidden_params: list of <params> keys to hide
    :param output_func: output function
    """
    width = width - 2  # subtract the sides
    max_length_param = len(max(params.keys(), key=lambda x: len(x)))

    content = f'\n{_get_header(title, width=width)}\n'
    for key, value in params.items():
        param = key.ljust(max_length_param)
        if key in hidden_params:
            value = '*****' if value else ''
        content += f'  {param} = {value}\n'
    content += f"╰{'═' * width}╯"
    output_func(content)


def _get_header(title: str, *, width: int) -> str:
    title = f' {title} ' if title != '' else ''
    header = title.center(width, '═')
    return f'╭{header}╮'


def print_list(
        elements: Sequence, title: str, width: int = WIDTH, *,
        key: Callable, output_func: Callable = print
) -> None:
    """ Print the list by filtering the information from the list using the function

    :param elements: value as dict: key/value
    :param title: list's title
    :param width: text content width
    :param key: function for filtering the information from the list
    :param output_func: output function
    (e.g. key=lambda package: f"{package['name']}@{package['version']}")
    """
    content = f'{title} ({len(elements)})'
    if len(elements) != 0:
        elements_content = '  '.join([key(elem) for elem in elements])
        content += f':\n{textwrap.fill(elements_content, width)}'
    output_func(content)


def banner(version: str, *, output_func: Callable = print):
    # This logo is colored #F4511E
    content = f"""
    \033[38;2;244;81;30m.-,\033[0m
 \033[38;2;244;81;30m.^.: :.^.\033[0m   ┏┓╻┳ ┏┓╻╻┏┓┳┏┓┏┳┓ ┏┓┏┓╻ ╻ ┏┓┏ ┓┏┓┳┓
\033[38;2;244;81;30m,-' .-. '-,\033[0m  ┃┓┃┃ ┗┓┗┃┗┓┃┣ ┃┃┃ ┣ ┃┃┃ ┃ ┃┃┃┃┃┣ ┣┛
\033[38;2;244;81;30m'-. '-' .-'\033[0m  ┗┛╹╹ ┗┛┗┛┗┛╹┗┛╹ ╹ ╹ ┗┛┗┛┗┛┗┛┗┻┛┗┛┛┗
 \033[38;2;244;81;30m'.`; ;`.'\033[0m   git-system-follower v{version}
    \033[38;2;244;81;30m`-`\033[0m"""
    output_func(content)


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
