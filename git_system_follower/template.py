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

""" Module with api for `template` command """
import contextlib
from pathlib import Path

from cookiecutter.main import cookiecutter

from git_system_follower.typings.cli import PackageCLIImage, PackageCLITarGz, PackageCLISource
from git_system_follower.typings.registry import RegistryInfo
from git_system_follower.variables import PACKAGES_PATH, PACKAGE_DIRNAME, SCRIPTS_DIR
from git_system_follower.download import download
from git_system_follower.package.templates import get_template_names
from git_system_follower.package.package_info import get_scripts_dir_by_complexity
from git_system_follower.utils.tmpdir import tempdir
from git_system_follower.logger import logger

__all__ = ['show_template']


@tempdir
def show_template(
        packages: tuple[PackageCLIImage | PackageCLITarGz | PackageCLISource, ...],
        extravars: tuple[tuple[str, str], ...], *, registry: RegistryInfo,
        tmpdir: Path, directory: Path | None = None, output_file: Path | None = None
) -> None:
    """ Render gear templates and show the generated files.

    Downloads each gear, finds its ``scripts/templates/`` directories,
    renders every template with cookiecutter using the supplied extravars,
    and prints the result to stdout.

    If ``output_file`` is specified, the generated output is captured and
    written to that file instead of being printed to the terminal.

    :param packages: gear specifications (image, tar.gz or source directory)
    :param extravars: extra context variables (name, value) to pass to each template
    :param registry: registry information (credentials, type, insecure mode) for image gears
    :param tmpdir: temporary directory for cookiecutter output
    :param directory: directory where generated files will be written.
        If not specified, only a preview is shown in stdout
    :param output_file: path to a file where the output will be captured.
        If not specified, output goes to the terminal
    """
    extra_context = dict(extravars)
    packages_data = download(packages, PACKAGES_PATH, registry=registry, is_deps_first=True)

    if output_file is not None:
        with open(output_file, 'w', encoding='utf-8') as f, contextlib.redirect_stdout(f):
            _render_gears(packages_data, extra_context, directory, tmpdir)
        logger.success(f'Template output written to {output_file.absolute()}')
    else:
        _render_gears(packages_data, extra_context, directory, tmpdir)

    if directory is not None:
        logger.success(f'Files have been written to {directory.absolute()}')


def _render_gears(packages_data, extra_context, directory, tmpdir):
    """Internal helper that does the actual rendering and printing."""
    for package in packages_data:
        # Ensure package supports dict-style access
        pname = package.get('name', package.name if hasattr(package, 'name') else '')
        pversion = package.get('version', package.version if hasattr(package, 'version') else '')

        script_dir, _ = get_scripts_dir_by_complexity(
            path=package['path'] / PACKAGE_DIRNAME / SCRIPTS_DIR / package['version'],
            is_force=False,
        )
        template_names = get_template_names(script_dir)

        print(f'\nPackage: {pname}@{pversion}')
        print(f'Available templates: {", ".join(template_names)}')

        for tmpl_name in template_names:
            template_path = script_dir / 'templates' / tmpl_name
            project_dir = Path(cookiecutter(
                template=str(template_path),
                output_dir=tmpdir,
                no_input=True,
                overwrite_if_exists=True,
                extra_context=extra_context,
            ))

            rendered = [(f, f.relative_to(tmpdir)) for f in sorted(project_dir.rglob('*')) if f.is_file()]

            static_dir = template_path / 'files'
            static = [(f, f.relative_to(static_dir)) for f in sorted(static_dir.rglob('*')) if f.is_file()] \
                if static_dir.exists() else []

            all_files = rendered + static
            print(f'Generated files ({len(all_files)}):')
            for i, (_, relative) in enumerate(all_files, 1):
                print(f'  {i}. {relative}')

            if all_files:
                print('\nPreview (what the generated files look like):')
            for f, relative in all_files:
                print(f'\n--- {relative} ---')
                content = f.read_text(encoding='utf-8', errors='replace')
                print(content if content.strip() else '<empty file>')

            if directory is not None:
                for f, relative in all_files:
                    target_path = directory / relative
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    target_path.write_bytes(f.read_bytes())
