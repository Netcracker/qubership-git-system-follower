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

""" Unit tests for OCI Image Index / Docker manifest list resolution
(git_system_follower/download.py), as produced by e.g. `docker buildx build --provenance=true`.

Platform selection is tested for both amd64 and arm64 by passing `target_platform` explicitly to
`Registry._resolve_index()`, rather than relying on `get_host_platform()` - this exercises the
arm64 branch correctly even when the CI/dev machine running these tests is amd64.
"""
from unittest.mock import patch

import pytest
import oras.container

from git_system_follower.download import RegistryV2, IMAGE_MANIFEST_MEDIA_TYPE, get_host_platform
from git_system_follower.errors import DownloadPackageError


AMD64_DIGEST = 'sha256:' + 'a' * 64
ARM64_DIGEST = 'sha256:' + 'b' * 64
ATTESTATION_DIGEST = 'sha256:' + 'c' * 64

# mirrors the shape of a `list.manifest.json` produced by `--provenance=true`:
# one runnable manifest per built platform, plus one attestation manifest marked unknown/unknown
SAMPLE_INDEX = {
    'schemaVersion': 2,
    'mediaType': 'application/vnd.oci.image.index.v1+json',
    'manifests': [
        {
            'mediaType': 'application/vnd.oci.image.manifest.v1+json',
            'digest': AMD64_DIGEST,
            'platform': {'architecture': 'amd64', 'os': 'linux'},
        },
        {
            'mediaType': 'application/vnd.oci.image.manifest.v1+json',
            'digest': ARM64_DIGEST,
            'platform': {'architecture': 'arm64', 'os': 'linux'},
        },
        {
            'mediaType': 'application/vnd.oci.image.manifest.v1+json',
            'digest': ATTESTATION_DIGEST,
            'platform': {'architecture': 'unknown', 'os': 'unknown'},
        },
    ],
}


def _make_container() -> oras.container.Container:
    return oras.container.Container('myregistry.example.com/namespace/repo:v1')


def _make_registry() -> RegistryV2:
    return RegistryV2(hostname='myregistry.example.com')


@pytest.mark.unit
@pytest.mark.parametrize('target_platform, expected_digest', [
    (('linux', 'amd64'), AMD64_DIGEST),
    (('linux', 'arm64'), ARM64_DIGEST),
])
def test_resolve_index_selects_correct_platform(target_platform, expected_digest):
    """Index resolution should pick the manifest matching the target platform and skip the
    unknown/unknown attestation manifest, for both amd64 and arm64 - independent of the host
    machine actually running the test"""
    registry = _make_registry()
    container = _make_container()
    resolved_manifest = {'mediaType': IMAGE_MANIFEST_MEDIA_TYPE, 'config': {'digest': 'sha256:' + 'd' * 64},
                          'layers': [{'digest': 'sha256:' + 'e' * 64}]}

    with patch.object(RegistryV2, 'get_manifest', return_value=resolved_manifest) as mock_get_manifest:
        result = registry._resolve_index(SAMPLE_INDEX, container, target_platform=target_platform)

    assert result == resolved_manifest
    # the container should have been re-pointed at the resolved digest before re-fetching
    assert container.digest == expected_digest
    mock_get_manifest.assert_called_once_with(container, allowed_media_type=[IMAGE_MANIFEST_MEDIA_TYPE])


@pytest.mark.unit
def test_resolve_index_raises_when_platform_not_found():
    """Should raise a clear error rather than silently picking the wrong manifest or the
    attestation manifest, if no entry matches the target platform"""
    registry = _make_registry()
    container = _make_container()

    with pytest.raises(DownloadPackageError, match='linux/riscv64'):
        registry._resolve_index(SAMPLE_INDEX, container, target_platform=('linux', 'riscv64'))


@pytest.mark.unit
@pytest.mark.parametrize('system, machine, expected', [
    ('Linux', 'x86_64', ('linux', 'amd64')),
    ('Linux', 'aarch64', ('linux', 'arm64')),
    ('Linux', 'arm64', ('linux', 'arm64')),
])
def test_get_host_platform_mapping(system, machine, expected):
    """`platform.machine()` values should map to OCI/Docker arch names correctly for both
    amd64 and arm64 hosts, simulated via mocking rather than needing that actual hardware"""
    with patch('git_system_follower.download.platform.system', return_value=system), \
            patch('git_system_follower.download.platform.machine', return_value=machine):
        assert get_host_platform() == expected


@pytest.mark.unit
def test_get_host_platform_unsupported_arch_raises():
    """An unrecognized host architecture should fail loudly instead of guessing"""
    with patch('git_system_follower.download.platform.system', return_value='Linux'), \
            patch('git_system_follower.download.platform.machine', return_value='riscv64'):
        with pytest.raises(DownloadPackageError, match='riscv64'):
            get_host_platform()


@pytest.mark.unit
def test_get_manifest_wrapper_passes_through_single_manifest():
    """A registry returning a plain single-image manifest (the common, non-index case) should be
    returned unchanged - no index resolution triggered, existing behavior preserved"""
    registry = _make_registry()
    container = _make_container()
    plain_manifest = {'mediaType': IMAGE_MANIFEST_MEDIA_TYPE, 'config': {'digest': 'sha256:' + 'd' * 64},
                       'layers': [{'digest': 'sha256:' + 'e' * 64}]}

    with patch.object(RegistryV2, 'get_manifest', return_value=plain_manifest) as mock_get_manifest, \
            patch.object(RegistryV2, '_resolve_index') as mock_resolve_index:
        result = registry.get_manifest_wrapper(container)

    assert result == plain_manifest
    mock_resolve_index.assert_not_called()
    mock_get_manifest.assert_called_once()


@pytest.mark.unit
def test_get_manifest_wrapper_resolves_index():
    """A registry returning an OCI Image Index should be transparently resolved to the
    host-platform manifest"""
    registry = _make_registry()
    container = _make_container()
    resolved_manifest = {'mediaType': IMAGE_MANIFEST_MEDIA_TYPE, 'config': {'digest': 'sha256:' + 'd' * 64},
                          'layers': [{'digest': 'sha256:' + 'e' * 64}]}

    with patch.object(RegistryV2, 'get_manifest', return_value=SAMPLE_INDEX), \
            patch.object(RegistryV2, '_resolve_index', return_value=resolved_manifest) as mock_resolve_index:
        result = registry.get_manifest_wrapper(container)

    assert result == resolved_manifest
    mock_resolve_index.assert_called_once_with(SAMPLE_INDEX, container)
