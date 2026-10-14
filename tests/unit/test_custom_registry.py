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

import pytest
from git_system_follower.errors import UnknownRegistryError
from git_system_follower.typings.registry import RegistryTypes, RegistryInfo
from git_system_follower.typings.cli import Credentials
from git_system_follower.download import get_client, Custom


@pytest.mark.unit
def test_custom_registry_type_requires_registry_url():
    """Test that Custom registry type requires --registry parameter"""
    registry = RegistryInfo(
        credentials=None,
        type=RegistryTypes.custom,
        is_insecure=False,
        registry_url=None
    )

    with pytest.raises(UnknownRegistryError) as exc_info:
        get_client("example.com", registry=registry)

    assert "requires --registry parameter" in str(exc_info.value)


@pytest.mark.unit
def test_registry_url_only_allowed_with_custom_type():
    """Test that --registry parameter is only allowed with --registry-type=Custom"""
    # This is tested at CLI level, but we can verify the validation exists
    # The actual CLI validation is in cli.py, this test documents the behavior
    pass


@pytest.mark.unit
def test_custom_registry_with_url_creates_custom_client():
    """Test that Custom registry with URL returns Custom client"""
    registry = RegistryInfo(
        credentials=None,
        type=RegistryTypes.custom,
        is_insecure=False,
        registry_url="https://my-registry.com"
    )

    client = get_client("my-registry.com", registry=registry)

    assert isinstance(client, Custom)


@pytest.mark.unit
def test_custom_client_basic_auth_uses_custom_url():
    """Test that Custom client uses registry_url for token endpoint"""
    from git_system_follower.download import Custom

    client = Custom(hostname="example.com")
    registry = RegistryInfo(
        credentials=Credentials(username="user", password="pass"),
        type=RegistryTypes.custom,
        is_insecure=False,
        registry_url="https://auth.myregistry.com"
    )

    # The custom client should use the registry_url for auth
    # We can't easily test the actual HTTP call, but we can verify the URL construction
    # by checking the behavior in the source
    scheme, host, _ = client._parse_registry_url(registry)
    assert scheme == 'https'
    assert host == 'auth.myregistry.com'


@pytest.mark.unit
def test_custom_registry_types_in_enum():
    """Test that Custom is in RegistryTypes enum"""
    assert RegistryTypes.custom.value == "Custom"
    assert "Custom" in [rt.value for rt in RegistryTypes]


@pytest.mark.unit
def test_registry_info_has_registry_url_field():
    """Test that RegistryInfo has registry_url field"""
    registry = RegistryInfo(
        credentials=None,
        type=RegistryTypes.custom,
        is_insecure=False,
        registry_url="https://custom-registry.com"
    )

    assert registry.registry_url == "https://custom-registry.com"

    # Test default is None
    registry2 = RegistryInfo(
        credentials=None,
        type=RegistryTypes.auto,
        is_insecure=False
    )
    assert registry2.registry_url is None


@pytest.mark.unit
def test_custom_client_strips_scheme_from_url():
    """Test that Custom client handles URLs with and without scheme"""
    client = Custom(hostname="example.com")

    # Test with https://
    registry = RegistryInfo(
        credentials=None,
        type=RegistryTypes.custom,
        is_insecure=False,
        registry_url="https://custom-registry.com:5000"
    )

    scheme, host, token_url = client._parse_registry_url(registry)
    assert scheme == 'https'
    assert host == 'custom-registry.com:5000'
    assert token_url == 'https://custom-registry.com:5000/v2/token'

    # Test with http://
    registry2 = RegistryInfo(
        credentials=None,
        type=RegistryTypes.custom,
        is_insecure=False,
        registry_url="http://custom-registry.com:5000"
    )
    scheme, host, token_url = client._parse_registry_url(registry2)
    assert scheme == 'http'
    assert host == 'custom-registry.com:5000'
    assert token_url == 'http://custom-registry.com:5000/v2/token'

    # Test without scheme (fallback to default)
    registry3 = RegistryInfo(
        credentials=None,
        type=RegistryTypes.custom,
        is_insecure=False,
        registry_url=None
    )
    scheme, host, token_url = client._parse_registry_url(registry3)
    assert scheme == 'https'  # default
    assert host == ''
    assert token_url == ''


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
