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

import logging
from pathlib import Path

import click
from colorama import Fore, Style


# for banner + print_params
NO_FORMAT = '%(message)s'
NO_DATE_FORMAT = ''

# for stdout
SHORT_FORMAT = f'{Fore.CYAN}%(asctime)s.%(msecs)03d{Fore.RESET} %(message)s'
SHORT_DATE_FORMAT = '%H:%M:%S'

# for debug stdout
SHORT_DEBUG_FORMAT = f'{Fore.CYAN}%(asctime)s.%(msecs)03d{Fore.RESET} %(levelname)-18s | %(message)s'
SHORT_DEBUG_DATE_FORMAT = '%H:%M:%S'

# for log file
FORMAT = '[%(asctime)s.%(msecs)03d] %(levelname)-8s | %(filename)s:%(funcName)s:%(lineno)d - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# New logging level
SUCCESS_LEVEL_NUM = 25
SUCCESS_LEVEL_NAME = 'SUCCESS'


class ColoredFormatter(logging.Formatter):

    COLORS = {
        'DEBUG': Fore.BLUE,
        'INFO': Fore.WHITE,
        'SUCCESS': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': f'{Fore.RED}{Style.BRIGHT}',
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname, '')
        if color:
            record.name = f'{color}{record.name}{Fore.WHITE}'
            record.levelname = f'{color}{record.levelname}{Fore.WHITE}'
            record.msg = f'{color}{record.msg}{Fore.WHITE}'
        return logging.Formatter.format(self, record)


class RemoveColorFilter(logging.Filter):
    # for file handlers
    def filter(self, record):
        if record and record.msg and isinstance(record.msg, str):
            record.levelname = click.unstyle(record.levelname)
            record.msg = click.unstyle(record.msg)
        return True


file_formatter = logging.Formatter(fmt=FORMAT, datefmt=DATE_FORMAT)


def disable_info_for_other_loggers(names: list[str]) -> None:
    for name in names:
        logger = logging.getLogger(name)
        logger.setLevel(logging.WARNING)


def get_stream_handler() -> logging.StreamHandler:
    handler = logging.StreamHandler()
    handler.setLevel(level=logging.INFO)
    handler.setFormatter(ColoredFormatter(fmt=NO_FORMAT, datefmt=NO_DATE_FORMAT))
    return handler


def get_file_handler(path: Path) -> logging.FileHandler:
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(path, mode='w', encoding='utf-8')
    handler.setLevel(level=logging.DEBUG)
    handler.addFilter(RemoveColorFilter())
    handler.setFormatter(file_formatter)
    return handler


def success(self, message, *args, **kwargs):
    if self.isEnabledFor(SUCCESS_LEVEL_NUM):
        self._log(SUCCESS_LEVEL_NUM, message, args, **kwargs)
