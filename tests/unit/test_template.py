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

"""Tests for the `template` command."""
import json
from unittest.mock import patch

import pytest

from git_system_follower.template import show_template
from git_system_follower.typings.registry import RegistryInfo
from git_system_follower.typings.package import PackageLocalData
from git_system_follower.variables import PACKAGE_DIRNAME, SCRIPTS_DIR


def _make_gear(tmp_path, name='simple', version='1.0.0', templates=None):
    """Create a minimal gear directory structure in <tmp_path>/gear_root.

    Returns the gear root path (the directory that contains git-system-follower-package/).
    """
    gear_root = tmp_path / 'gear_root'
    pkg_dir = gear_root / PACKAGE_DIRNAME
    scripts_dir = pkg_dir / SCRIPTS_DIR
    templates_dir = scripts_dir / 'templates'
    templates_dir.mkdir(parents=True)

    pkg_yaml = {
        'apiVersion': 'v1',
        'name': name,
        'type': 'gitlab-ci-pipeline',
        'version': version,
    }
    (pkg_dir / 'package.yaml').write_text(json.dumps(pkg_yaml), encoding='utf-8')

    for tmpl_name, extra_ctx in (templates or {'default': {}}).items():
        tmpl_dir = templates_dir / tmpl_name
        tmpl_dir.mkdir(parents=True)
        cookie_ctx = {
            'gsf_repository_name': '',
            'name': 'World',
            'tags': 'default',
        }
        cookie_ctx.update(extra_ctx)
        (tmpl_dir / 'cookiecutter.json').write_text(json.dumps(cookie_ctx), encoding='utf-8')
        render_dir = tmpl_dir / '{{ cookiecutter.gsf_repository_name }}'
        render_dir.mkdir(parents=True)
        (render_dir / 'hello.txt').write_text('Hello, {{ cookiecutter.name }}!')

    return gear_root, PackageLocalData(
        apiVersion='v1', type='gitlab_ci_pipeline', name=name,
        version=version, dependencies=(), path=gear_root,
    )


def _make_empty_gear(tmp_path):
    """Create a gear with no templates directory."""
    gear_root = tmp_path / 'gear_root'
    pkg_dir = gear_root / PACKAGE_DIRNAME
    scripts_dir = pkg_dir / SCRIPTS_DIR
    scripts_dir.mkdir(parents=True)
    (pkg_dir / 'package.yaml').write_text(
        json.dumps({
            'apiVersion': 'v1', 'name': 'empty', 'type': 'gitlab-ci-pipeline',
            'version': '1.0.0',
        }),
        encoding='utf-8',
    )
    return gear_root, PackageLocalData(
        apiVersion='v1', type='gitlab_ci_pipeline', name='empty',
        version='1.0.0', dependencies=(), path=gear_root,
    )


def _registry():
    return RegistryInfo(credentials=None, type='Autodetect', is_insecure=False)


@pytest.mark.unit
def test_show_template_previews_gear_files(tmp_path, capsys):
    gear_root, pkg_data = _make_gear(tmp_path)

    with patch('git_system_follower.template.download', return_value=[pkg_data]):
        show_template((), (), registry=_registry())

    captured = capsys.readouterr().out
    assert 'Package: simple@1.0.0' in captured
    assert 'Available templates: default' in captured
    assert 'Hello, World!' in captured
    assert 'Generated files (1):' in captured
    assert 'hello.txt' in captured


@pytest.mark.unit
def test_show_template_extravars_override_defaults(tmp_path, capsys):
    gear_root, pkg_data = _make_gear(tmp_path)

    with patch('git_system_follower.template.download', return_value=[pkg_data]):
        show_template((), (('name', 'Alice'),), registry=_registry())

    assert 'Hello, Alice!' in capsys.readouterr().out


@pytest.mark.unit
def test_show_template_multiple_templates(tmp_path, capsys):
    gear_root, pkg_data = _make_gear(
        tmp_path, templates={'default': {}, 'library': {'name': 'Lib'}},
    )

    with patch('git_system_follower.template.download', return_value=[pkg_data]):
        show_template((), (), registry=_registry())

    captured = capsys.readouterr().out
    assert 'Available templates: default, library' in captured
    assert 'Hello, World!' in captured
    assert 'Hello, Lib!' in captured


@pytest.mark.unit
def test_show_template_writes_files_to_directory(tmp_path, caplog):
    gear_root, pkg_data = _make_gear(tmp_path)
    target_dir = tmp_path / 'output'

    with patch('git_system_follower.template.download', return_value=[pkg_data]):
        show_template((), (), registry=_registry(), directory=target_dir)

    written_file = target_dir / 'hello.txt'
    assert written_file.exists()
    assert written_file.read_text() == 'Hello, World!'
    assert f'Files have been written to {target_dir.absolute()}' in caplog.text


@pytest.mark.unit
def test_show_template_writes_preview_to_output_file(tmp_path, caplog):
    gear_root, pkg_data = _make_gear(tmp_path)
    output_file = tmp_path / 'preview.txt'

    with patch('git_system_follower.template.download', return_value=[pkg_data]):
        show_template((), (), registry=_registry(), output_file=output_file)

    content = output_file.read_text()
    assert 'Package: simple@1.0.0' in content
    assert 'Hello, World!' in content
    assert f'Template output written to {output_file.absolute()}' in caplog.text


@pytest.mark.unit
def test_show_template_includes_static_files(tmp_path, capsys):
    gear_root, pkg_data = _make_gear(tmp_path)
    static_dir = gear_root / PACKAGE_DIRNAME / SCRIPTS_DIR / 'templates' / 'default' / 'files'
    (static_dir / 'nested').mkdir(parents=True)
    (static_dir / 'static.txt').write_text('static content')
    (static_dir / 'nested' / 'inner.txt').write_text('inner static content')
    target_dir = tmp_path / 'output'

    with patch('git_system_follower.template.download', return_value=[pkg_data]):
        show_template((), (), registry=_registry(), directory=target_dir)

    captured = capsys.readouterr().out
    assert 'Generated files (3):' in captured
    assert 'static content' in captured
    assert 'inner static content' in captured
    assert (target_dir / 'static.txt').read_text() == 'static content'
    assert (target_dir / 'nested' / 'inner.txt').read_text() == 'inner static content'
    assert (target_dir / 'hello.txt').read_text() == 'Hello, World!'


@pytest.mark.unit
def test_show_template_no_templates_raises(tmp_path):
    gear_root, pkg_data = _make_empty_gear(tmp_path)

    with patch('git_system_follower.template.download', return_value=[pkg_data]):
        with pytest.raises(Exception, match='No templates found'):
            show_template((), (), registry=_registry())


@pytest.mark.unit
def test_show_template_prints_no_files_when_no_templates(tmp_path, capsys):
    gear_root, pkg_data = _make_empty_gear(tmp_path)

    with patch('git_system_follower.template.download', return_value=[pkg_data]):
        with pytest.raises(Exception):
            show_template((), (), registry=_registry())

    captured = capsys.readouterr().out
    assert 'Available templates' not in captured
