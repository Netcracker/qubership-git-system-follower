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

from pathlib import Path
from functools import wraps
import tempfile
import shutil

from git_system_follower.logger import logger


__all__ = ['tempdir', 'multi_tempdirs']


def tempdir(func):
    """ Creating temporary directory while executing function """
    def wrapper(*args, **kwargs):
        directory = Path(tempfile.mkdtemp(prefix='gsf-package-manager-'))
        logger.debug(f'Temporary directory was created at {directory}')
        result = func(*args, **kwargs, tmpdir=directory)
        shutil.rmtree(directory)
        logger.debug(f'Temporary directory was removed at {directory}')
        return result
    return wrapper


def multi_tempdirs(count: int):
    """Creating multiple temporary directories while executing function."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            dirs = []
            try:
                for _ in range(count):
                    d = Path(tempfile.mkdtemp(prefix='gsf-package-manager-'))
                    logger.debug(f'Temporary directory was created at {d}')
                    dirs.append(d)

                return func(*args, **kwargs, tmpdir=tuple(dirs))
            finally:
                for d in dirs:
                    shutil.rmtree(d)
                    logger.debug(f'Temporary directory was removed at {d}')
        return wrapper
    return decorator
