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

from colorama import init

from git_system_follower.variables import ROOT_DIR
from git_system_follower.utils.logger import SUCCESS_LEVEL_NUM, SUCCESS_LEVEL_NAME
from git_system_follower.utils.logger import (get_stream_handler, get_file_handler, success,
                                              disable_info_for_other_loggers)


__all__ = ['LOG_FILE_PATH', 'logger', 'set_level']


LOG_FILE_PATH = ROOT_DIR / 'git-system-follower.log'


init(autoreset=True)

# New logging level
logging.addLevelName(SUCCESS_LEVEL_NUM, SUCCESS_LEVEL_NAME)
logging.Logger.success = success


def _get_logger(name: str = 'package_manager') -> logging.Logger:
    logger_ = logging.getLogger(name)
    logger_.setLevel(level=logging.NOTSET)
    logger_.addHandler(get_stream_handler())
    logger_.addHandler(get_file_handler(LOG_FILE_PATH))
    return logger_


disable_info_for_other_loggers([
    'urllib3', 'requests', 'charset_normalizer', 'git', 'cookiecutter', 'rich', 'binaryornot'
])

# Logger for use in project
logger = _get_logger('root')


def set_level(is_debug: bool) -> None:
    level = logging.DEBUG if is_debug else logging.INFO
    logger.handlers[0].setLevel(level=level)  # set level only for stream handler
