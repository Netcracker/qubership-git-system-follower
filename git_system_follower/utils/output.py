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
from typing import Iterable, Callable

from outlify.panel import ParamsPanel
from outlify.style import AnsiCodes, Colors, Styles

from git_system_follower.logger import logger
from git_system_follower.typings.package import PackageLocalData


__all__ = ['BrandedColors', 'banner', 'display_params', 'print_dependency_tree_one_level']


WIDTH = 100


class BrandedAnsiCodes(AnsiCodes):
    orange = (38, 2, 244, 81, 30)  # color: #F4511E


BrandedColors = BrandedAnsiCodes()
COMMON_SETTINGS = {
    'width': 100,
    'title_style': [Colors.white],
    'title_align': 'left',
    'subtitle_style': [Colors.gray],
    'subtitle_align': 'right',
    'border': '╭╮╰╯═',
    'border_style': [Colors.gray],
}


def banner(version: str, *, output_func: Callable = print):
    content = f"""
    {BrandedColors.orange}.-,{Colors.reset}
 {BrandedColors.orange}.^.: :.^.{Colors.reset}   ┏┓╻┳ ┏┓╻╻┏┓┳┏┓┏┳┓ ┏┓┏┓╻ ╻ ┏┓┏ ┓┏┓┳┓
{BrandedColors.orange},-' .-. '-,{Colors.reset}  ┃┓┃┃ ┗┓┗┃┗┓┃┣ ┃┃┃ ┣ ┃┃┃ ┃ ┃┃┃┃┃┣ ┣┛
{BrandedColors.orange}'-. '-' .-'{Colors.reset}  ┗┛╹╹ ┗┛┗┛┗┛╹┗┛╹ ╹ ╹ ┗┛┗┛┗┛┗┛┗┻┛┗┛┛┗
 {BrandedColors.orange}'.`; ;`.'{Colors.reset}   {Colors.white}{Styles.bold}git-system-follower{Styles.reset} v{version}
    {BrandedColors.orange}`-`{Colors.reset}"""
    output_func(content)


def display_params(data: dict[str, dict]) -> None:
    """ Display parameters in a compact format

    :param data: data to display where key - section name, value - parameters
    """
    for i, (name, params) in enumerate(data.items(), 1):
        title, subtitle = f'{i}. {name} parameters', f'total: {len(params)}'
        logger.info(ParamsPanel(params, title=title, subtitle=subtitle, **COMMON_SETTINGS))


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
