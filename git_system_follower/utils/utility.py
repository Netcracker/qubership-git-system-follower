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
import re
import sys
import runpy
import site
import logging
import tempfile
from pathlib import Path
from git_system_follower.logger import logger
from git_system_follower.errors import PackageApiError


def normalized_in_string_match(tocompare: str, comparedto: str)-> bool:
    """
    Remove all non-alphanumeric characters (hyphens, underscores, dots, slashes, colons)
    This turns both strings into pure blocks of letters and numbers
    """
    flat1 = re.sub(r'[^a-zA-Z0-9]', '', tocompare)
    flat2 = re.sub(r'[^a-zA-Z0-9]', '', comparedto)
    return flat1 in flat2

def run_pip(args: list[str]) -> int:
    log_file = Path(tempfile.mktemp(suffix='.log'))
    old_argv = sys.argv
    sys.argv = ['pip', 'install', '--progress-bar', 'off', '--log', str(log_file)] + args

    pip_logger = logging.getLogger('pip')
    root_logger = logging.getLogger()

    original_pip_handlers = pip_logger.handlers[:]
    original_root_handlers = root_logger.handlers[:]
    try:
        runpy.run_module('pip', run_name='__main__')
        return 0

    except SystemExit as e:
        return e.code if e.code is not None else 0
    finally:
        sys.argv = old_argv
        pip_logger.handlers = original_pip_handlers
        root_logger.handlers = original_root_handlers
        if log_file.exists():
            seen = set()
            keywords = ('Collecting', 'Downloading', 'Installing', 'Successfully',
                        'Building', 'Requirement', 'Getting', 'Preparing')
            for line in log_file.read_text().splitlines():
                clean = re.sub(r'^\d{4}-\d{2}-\d{2}T[\d:,]+\s*', '', line).strip()
                if clean and clean not in seen and clean.startswith(keywords):
                    seen.add(clean)
                    logger.info(clean)
            log_file.unlink()

def get_package_dependency(path: Path):
    """
    Get package dependency of Gears from requirements.txt, and install them before running package api
    This is to ensure that the package api can run successfully even if the dependencies are not installed
    """
    req_path = path.parents[1] / 'requirements.txt'
    if not req_path.exists():
        return

    pip_cache_dir = Path.home() / '.cache' / 'pip'
    with open(req_path) as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    failed_reqs = []
    # Check if exist in cache, else it will attempt to download.
    for req in requirements:
        if run_pip([req, '--cache-dir', str(pip_cache_dir)]) != 0:
            failed_reqs.append(req)

    # If the wheel is pre-downloaded to gear wheels directory. For air-gapped environments.
    if failed_reqs:
        site_packages_dirs = [Path(p) for p in site.getsitepackages()]
        wheel_cache = path.parents[1] / 'wheels'
        package_cache = path.parents[1] / 'site-packages'
        find_links = [arg for c in [wheel_cache, package_cache] + site_packages_dirs if c.exists()
            for arg in ['--find-links', str(c)]]

        if not find_links:
            logger.error(f'Failed packages and no site-packages found: {failed_reqs}')
            raise PackageApiError(f'Failed packages and no site-packages found: {failed_reqs}')

        for req in failed_reqs:
            if run_pip([req] + find_links + ['--no-index']) != 0:
                logger.error(f'Failed to install {req} from site-packages')
                sys.exit(1)
