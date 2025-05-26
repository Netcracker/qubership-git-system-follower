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

""" Module with api to work with templates """
from pathlib import Path
import hashlib
import shutil
import os
from cookiecutter.main import cookiecutter

from git_system_follower.logger import logger
from git_system_follower.errors import PackageApiError
from git_system_follower.utils.tmpdir import tempdir, multi_tempdirs


__all__ = ['get_template_names', 'create_template', 'delete_template']


def get_template_names(script_dir: Path) -> tuple[str, ...]:
    """ Get available template names in package api """
    path = script_dir / 'templates'
    if not path.exists():
        raise PackageApiError(f'Template directory is missing. Path: {path}')

    return tuple(template.name for template in path.iterdir() if (path / template).is_dir())


@multi_tempdirs(2)
def create_template(
        script_dir: Path, template: str | None, target: Path, *,
        tmpdir: list[Path], variables: dict[str, str], is_force: bool,
        current_version_dir: Path | None = None
) -> None:
    logger.info(f'\t-> Creating project using {template} template')
    if template is None:
        logger.info('\t\tNo template specified. Skip operations')
        return
    path = script_dir / 'templates' / template

    if not path.exists():
        raise PackageApiError(f'Template is missing. Template path: {path}')

    new_version_path = tmpdir[0]
    current_version_path = tmpdir[1]
    cookiecutter(
        template=str(path), output_dir=new_version_path, no_input=True,
        extra_context=_get_extra_content(target, variables=variables)
    )
    if current_version_dir is not None:
        current_version_dir = current_version_dir / 'templates' / template
        cookiecutter(
            template=str(current_version_dir), output_dir=current_version_path, no_input=True,
            extra_context=_get_extra_content(target, variables=variables)
        )
    _copy_files(new_version_path / target.name, current_version_path / target.name, target, is_force=is_force)
    logger.info(f'\t\tSuccessful use template ({path})')


def _copy_files(source: Path, source_current: Path, target: Path, *, is_force: bool) -> None:
    paths = source.glob('**/*')
    for path in paths:
        if path.is_dir():
            continue
        relative_path = path.relative_to(source)
        target_path = target / relative_path
        current_path = source_current / relative_path
        if not target_path.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(path, target_path)
            logger.info(f'\t\tFile {relative_path} does not exist. Copied it from template')
            continue

        path_hash = _calculate_hash(path)
        current_path_hash = _calculate_hash(current_path)
        target_path_hash = _calculate_hash(target_path)
        if path_hash == target_path_hash:
            logger.info(f'\t\tContent of {relative_path} file is same. Skip operations')
            continue
        elif path_hash != target_path_hash and current_path_hash == target_path_hash:
            logger.info(f'\t\tNo user changes for {relative_path} hence upgrading from template')
            shutil.copy(path, target_path)
            continue
        elif path_hash != target_path_hash and current_path_hash != target_path_hash:
            logger.warning(f'\t\tUser changes found for file {relative_path}. Cannot copy. Skip operations')
            continue

        if is_force:
            shutil.copy(path, target_path)
            logger.warning(f'\t\tFile {relative_path} already exists. Force flag enabled. '
                           f'Overwrote it from template')
            continue
        logger.warning(f'\t\tFile {relative_path} already exists. Cannot copy. Skip operations')


def _calculate_hash(path: Path) -> str:
    """ Calculating file content hash

    :param path: file path
    :return: file content hash
    """
    hash_func = hashlib.sha256()
    if Path(path).exists():
        with open(path, 'rb') as file:
            content = file.read().decode('utf-8-sig', errors='ignore')
            content = content.replace('\r\n', '\n').replace('\r', '\n')
            hash_func.update(content.encode('utf-8'))
            return hash_func.hexdigest()
    return "File not found"


@tempdir
def delete_template(
        script_dir: Path, template: str | None, target: Path, *,
        variables: dict[str, str], tmpdir: Path, is_force: bool
) -> None:
    logger.info(f'\t-> Deleting project files using {template} template')
    if template is None:
        logger.info('\t\tNo template specified. Skip operations')
        return
    path = script_dir / 'templates' / template
    if not path.exists():
        raise PackageApiError(f'Template is missing. Template path: {path}')

    cookiecutter(
        template=str(path), output_dir=tmpdir, no_input=True,
        extra_context=_get_extra_content(target, variables=variables)
    )
    _delete_files(tmpdir / target.name, target, is_force=is_force)
    logger.info(f'\t\tSuccessful delete files using template ({path})')


def _get_extra_content(target: Path, *, variables: dict[str, str]) -> dict[str, str]:
    content = {'gsf_repository_name': target.name}
    content.update(variables)
    return content


def _delete_files(source: Path, target: Path, *, is_force: bool) -> None:
    paths = source.glob('**/*')
    for path in paths:
        if path.is_dir():
            continue
        relative_path = path.relative_to(source)
        target_path = target / relative_path
        if not target_path.exists():
            logger.info(f'\t\tFile {relative_path} does not exist. Skip operations')
            continue

        path_hash, target_path_hash = _calculate_hash(path), _calculate_hash(target_path)
        if path_hash == target_path_hash:
            os.remove(target_path)
            logger.info(f'\t\tContent of {relative_path} file is same. Deleted this file')
            continue

        if is_force:
            os.remove(target_path)
            logger.warning(f'\t\tFile {relative_path} exists and does not match the template. '
                           f'Overwrote it from template')
            continue
        logger.warning(f'\t\tFile {relative_path} exists and does not match the template. '
                       f'Cannot delete. Skip operations')
