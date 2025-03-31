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

""" Module for local package download """
from typing import Iterable
from pathlib import Path
from pprint import pformat
from abc import ABC, abstractmethod
import tarfile
import json
import shutil

import oras.client
import oras.container
import oras.defaults
import requests
from requests.auth import HTTPBasicAuth
import yaml

from git_system_follower.variables import IMAGE_PACKAGE_MAP, PACKAGES_PATH, PACKAGE_DIRNAME
from git_system_follower.logger import logger
from git_system_follower.errors import (
    RemoteRepositoryError, DownloadPackageError, UnknownRegistryError, PackageNotFoundError
)
from git_system_follower.typings.cli import (
    PackageCLI, PackageCLITypes,
    PackageCLIImage, PackageCLITarGz, PackageCLISource
)
from git_system_follower.typings.registry import RegistryTypes, RegistryInfo
from git_system_follower.plugins.cli.packages.default import TarGzPlugin
from git_system_follower.typings.package import PackageLocalData
from git_system_follower.package.package_info import (
    DESCRIPTION_FILENAME, get_package_info, check_dependency_depth, add_dependencies
)
from git_system_follower.utils.tmpdir import tempdir


__all__ = ['download']


class Registry(ABC, oras.client.OrasClient):
    """ Base class of any new Registry """

    @abstractmethod
    def download(self, target: str, outdir: Path, *, registry: RegistryInfo) -> Path | None:
        """ Download package function from OCI artifact or image

        Similar command "oras copy <target> --to-oci-layout <outdir>" with custom:
        downloading regular docker image (<target>) with package inside it and unpacking this package from layer to
        <outdir>/<package name>@<package version>.tar.gz, where package name and version are taking from package.yaml
        inside package(.tar.gz file) itself

        :param target: OCI artifact or image url without protocol
        :param outdir: directory where need to save package
        :param registry: registry information like credentials for auth, insecure mode, etc.
        :return: content of downloaded OCI artifact or image
        """
        pass

    @abstractmethod
    def _get_anonymous_token(self, container: oras.container.Container, *, registry: RegistryInfo) -> str:
        """ Get anonymous token for getting manifest and downloading layers (`docker pull` simulation with possibility
        of anonymous image downloading)

        :param container: Oras container with information about target
        :param registry: registry information like credentials for auth, insecure mode, etc.
        :return: anonymous token
        """
        pass

    @staticmethod
    def _check_anonymous_token_request(response: requests.Response, container: oras.container.Container) -> str:
        """ Verification of the received anonymous token """
        response.raise_for_status()
        token = response.json().get('token')
        if token is None:
            raise RemoteRepositoryError(f'Failed to get an anonymous token for {container}')
        return token

    def get_manifest_wrapper(self, container: oras.container.Container) -> dict:
        """ Wrapper for getting manifest

        :param container: Oras container with information about target
        :return: manifest
        """
        manifest = self.get_manifest(
            container, allowed_media_type=['application/vnd.docker.distribution.manifest.v2+json']
        )
        logger.debug(f'Found manifest:\n{pformat(manifest)}')
        return manifest

    def is_gear(self, manifest: dict, container: oras.container.Container) -> bool:
        """ Check if the image is a GSF package

        :param manifest: manifest of OCI artifact or image
        :param container: Oras container with information about target
        """
        # OCI artifact
        if manifest['mediaType'] == 'application/vnd.oci.image.manifest.v1+json':
            return True

        # Docker image with: LABEL gsf.package="true"
        digest = manifest['config']['digest']
        response = requests.get(
            f'{self.prefix}://{container.registry}/v2/{container.namespace}/{container.repository}/blobs/{digest}',
            headers=self.auth.get_auth_header()
        )
        response.raise_for_status()
        labels = response.json().get('config', {}).get('Labels', {})
        if labels is None:  # case when label specified and is None
            return False

        required_label = 'gsf.package'
        return required_label in labels.keys() and labels[required_label] == 'true'

    def _download_layer(self, container: oras.container.Container, manifest: dict, outdir: Path) -> Path:
        """ Download layer of GSF package
        The GSF package has specific rules that there can only be one directory in an OCI artifact or image

        :param container: Oras container with information about target
        :param manifest: manifest of OCI artifact or image
        :param outdir: directory where need to save package
        :return: content of downloaded OCI artifact or image
        """
        layers = manifest.get("layers")
        if layers is None:
            raise DownloadPackageError(f'Failed to parse the layers of {container} image to get package '
                                       f'in it: layers not found')
        if len(layers) != 1:
            raise DownloadPackageError(f'{container} image should contain only one layer with the package. '
                                       f'The number of layers found: {len(layers)}')

        layer = layers[0]
        digest = layer['digest']
        package_path = outdir / 'package.tar.gz'
        self.download_blob(container, digest, str(package_path.absolute()))
        logger.debug(f'Downloaded {digest} layer to {package_path}')
        try:
            package_new_path = package_path.parent / self._get_package_filename(package_path)
        except DownloadPackageError as error:
            raise DownloadPackageError(f'{error}. Image: {container}, layer digest: {digest}')

        package_path.rename(package_new_path)
        logger.debug(f'Renamed {package_path} to {package_new_path}')
        return package_new_path

    @staticmethod
    def _get_package_filename(path: Path) -> str:
        """ Get current filename for package (.tar.gz file) using parsing pacakge.yaml inside this package

        :param path: path to package (.tar.gz)
        :return: current filename for package
        """
        name, version = get_name_and_version_version_from_targz(path)
        return f'{name}@{version}.tar.gz'


class RegistryV2(Registry):
    """ Oras client for downloading git-system-follower packages from docker registries
    using Docker Registry HTTP API V2 spec

    for more details, see https://docker-docs.uclv.cu/registry/spec/api/
    """

    def download(self, target: str, outdir: Path, *, registry: RegistryInfo) -> Path | None:
        if registry.is_insecure:
            self.prefix="http"
        container = self.get_container(target)
        token = self._get_anonymous_token(container, registry=registry)
        self.auth.set_token_auth(token)

        manifest = self.get_manifest_wrapper(container)
        if not self.is_gear(manifest, container):
            logger.warning(f'{target} is not a git-system-follower package. Skip downloading')
            return None

        return self._download_layer(container, manifest, outdir)

    def _get_anonymous_token(self, container: oras.container.Container, *, registry: RegistryInfo) -> str:
        auth = None
        if registry.credentials is not None:
            auth = HTTPBasicAuth(registry.credentials.username, registry.credentials.password)
        response = requests.get(
            f'{self.prefix}://{container.registry}/v2/token',
            params={
                'service': container.registry,
                'scope': f'repository:{container.namespace}/{container.repository}:pull'
            }, auth=auth, verify=not registry.is_insecure
        )
        return self._check_anonymous_token_request(response, container)


class Dockerhub(RegistryV2):
    """ Oras client for downloading git-system-follower packages from DockerHub

    It also works as well as RegistryV2, but have custom logic
    (TODO: fix it using Docker Registry HTTP API V2 spec for a single solution for all registries)
    """

    def download(self, target: str, outdir: Path, *, registry: RegistryInfo) -> Path | None:
        container = self.get_container(target)
        token = self._get_anonymous_token(container, registry=registry)
        self.auth.set_token_auth(token)

        # fix oras get_manifest for docker.io. For example, we set the image as docker.io/path/to/image:tag
        # then oras will try to download the image from www.docker.io, which is an invalid link.
        container.registry = 'index.docker.io'

        manifest = self.get_manifest_wrapper(container)
        if not self.is_gear(manifest, container):
            logger.warning(f'{target} is not a git-system-follower package. Skip downloading')
            return None

        return self._download_layer(container, manifest, outdir)

    def _get_anonymous_token(self, container: oras.container.Container, *, registry: RegistryInfo) -> str:
        auth = None
        if registry.credentials is not None:
            auth = HTTPBasicAuth(registry.credentials.username, registry.credentials.password)
        response = requests.get(
            f'{self.prefix}://auth.{container.registry}/token',
            params={
                'service': f'registry.{container.registry}',
                'scope': f'repository:{container.namespace}/{container.repository}:pull'
            }, auth=auth, verify=not registry.is_insecure
        )
        return self._check_anonymous_token_request(response, container)


class Artifactory(RegistryV2):
    pass


class Nexus(RegistryV2):
    pass


def get_name_and_version_version_from_targz(path: Path) -> tuple[str, str]:
    """ Get name and version of package for .tar.gz archive

    :param path: path to package (.tar.gz)
    :return: current name and version of package
    """
    description = f'{PACKAGE_DIRNAME}/{DESCRIPTION_FILENAME}'
    with tarfile.open(path, 'r:gz') as tar:
        if description not in tar.getnames():
            raise DownloadPackageError(f'Could not find {description} file inside image')
        with tar.extractfile(description) as file:
            content = yaml.safe_load(file)

    return _get_name_and_version_from_description(content, description)


def get_name_and_version_version_from_source(path: Path) -> tuple[str, str]:
    """ Get name and version of package for source

    :param path: path to package (directory)
    :return: current name and version of package
    """
    description = f'{PACKAGE_DIRNAME}/{DESCRIPTION_FILENAME}'
    with open(path / description, 'r') as file:
        content = yaml.safe_load(file)

    return _get_name_and_version_from_description(content, description)


def _get_name_and_version_from_description(content: dict, description: str) -> tuple[str, str]:
    """ Get name and version of package from description package file

    :param content: content of description package file
    :return: current name and version of package
    """
    name, version = content.get('name'), content.get('version')
    if name is None:
        raise DownloadPackageError(f"Section 'name' not found in {description} file")
    if version is None:
        raise DownloadPackageError(f"Section 'version' not found in {description} file")
    return name, version


def download(
        packages: Iterable[PackageCLI | PackageCLIImage | PackageCLITarGz | PackageCLISource],
        directory: Path = PACKAGES_PATH, *,
        registry: RegistryInfo, dependency_tree: str = '', dependency_level: int = 0, is_deps_first: bool
) -> list[PackageLocalData]:
    """ Download packages

    :param packages: packages to be downloaded
    :param directory: directory where need to download package
    :param registry: registry information like credentials for auth, insecure mode, etc.
    :param dependency_tree: current dependency tree, e.g. `root-package -> root's-dependency`
    :param dependency_level: current dependency depth level
    :param is_deps_first: whether dependencies should be specified first, and then the main package. This is necessary
                          for the order in which package are handled, e.g. installation starts with dependencies,
                          uninstallation with the main package
    :return: paths to packages (.tar.gz files)
    """
    if not packages:
        return []

    if dependency_level == 0:
        logger.info(':: Downloading packages')

    result = []
    for i, package in enumerate(packages, 1):
        logger.info(f'-> Downloading {package}')
        new_dep_tree = f'{dependency_tree} -> {package.name}' if dependency_level != 0 else package.name
        check_dependency_depth(dependency_level, new_dep_tree)

        source = get_source(package, directory, registry=registry)
        if source is None:
            continue
        data = get_package_info(source.parent, source.name)
        if data['dependencies']:
            logger.info(f"Package dependencies: {', '.join([str(dep) for dep in data['dependencies']])}")
        dependencies_data = download(
            data['dependencies'], directory, registry=registry,
            dependency_tree=new_dep_tree, dependency_level=dependency_level + 1, is_deps_first=is_deps_first
        )
        fixed_dependency_names = []
        for dependency in data['dependencies']:
            fixed_dependency_names.append(_get_fixed_package_using_mapping(dependency))
        data['dependencies'] = tuple(fixed_dependency_names)
        result.append(data)
        result = add_dependencies(result, dependencies_data, is_deps_first)

    if dependency_level == 0:
        logger.success('Download complete')
    return result


def get_source(
        package: PackageCLI | PackageCLIImage | PackageCLITarGz | PackageCLISource, directory: Path, *,
        registry: RegistryInfo
) -> Path | None:
    """ Wrapper to handle different package input values

    :param package: packages to be downloaded
    :param directory: directory where need to download package
    :param registry: registry information like credentials for auth, insecure mode, etc.
    :return: source code (download package with unpacking or unpacking .tar.gz archive or already ready-made code)
    """
    if package.type == PackageCLITypes.source:
        source = package.path
        name, version = get_name_and_version_version_from_source(source)
        logger.info(f'{name}@{version} package is provided as source code (Path: {source})')
        if not source.exists():
            raise PackageNotFoundError(f'{source.absolute()} directory does not exist')
        return source / PACKAGE_DIRNAME

    if package.type == PackageCLITypes.image:
        path = download_package(package, directory, registry=registry)
        if path is None:
            return None
    else:  # package.type == PackageCLITypes.targz
        path = package.path
        name, version = get_name_and_version_version_from_targz(path)
        logger.info(f'{name}@{version} package is provided as .tar.gz archive (Path: {path})')
        if not path.exists():
            raise PackageNotFoundError(f'{path.absolute()} archive does not exist')

    return unpack(path, PACKAGES_PATH)


@tempdir
def download_package(
        package: PackageCLIImage, outdir: Path, *,
        tmpdir: Path, registry: RegistryInfo
) -> Path | None:
    """ Download package from registry using oras

    An explanation of how version detection works: we have the version inside package.yaml and the version (image tag)
    We take as true the version that is specified in package.yaml.

    That is, we definitely need to download the package to find out the correct version.
    To avoid repeated downloads we use a `IMAGE_PACKAGE_MAP` file where we specify which image
    corresponds to which package

    How IMAGE_PACKAGE_MAP file works:
        1. if package doesn't exist in `outdir` and package with image doesn't exist in `IMAGE_PACKAGE_MAP`:
           download package from image, save info in `IMAGE_PACKAGE_MAP`
        2. if package exists in `outdir`, but package with image doesn't exist in `IMAGE_PACKAGE_MAP`
           (e.g. this package/.tar.gz file was brought in from outside):
           download package from image to a temporary directory and skip moving to outdir,
           save info in `IMAGE_PACKAGE_MAP`
        3. if package doesn't exist in `outdir`, but package with image exists in `IMAGE_PACKAGE_MAP`:
           download package from image, save info in `IMAGE_PACKAGE_MAP`
        4. if package exists in `outdir` and package with image exists in `IMAGE_PACKAGE_MAP`:
           skip downloading package from image

    :param package: package to be downloaded
    :param outdir: directory where need to download package
    :param tmpdir: temporary directory where package will be downloaded and manipulated
    :param registry: registry information like credentials for auth, insecure mode, etc.
    :return: downloaded package (tar.gz file): `<outdir>/<package tar.gz file>`
    """
    if not IMAGE_PACKAGE_MAP.exists():
        with open(IMAGE_PACKAGE_MAP, 'w') as file:
            json.dump({}, file)

    outfile = _get_current_path_using_mapping(package, outdir)
    if outfile is not None:
        logger.info(f'{_get_filename_without_suffix(outfile)} package is provided as docker image (Image: {package})')
        logger.info(f'Package has already been downloaded to {outfile} from {package}. Skip downloading')
        return outfile

    client = get_client(package.registry, registry=registry)
    image = package.get_image_path()
    package_tmp_path = client.download(image, outdir=tmpdir, registry=registry)
    if package_tmp_path is None:  # image is not git-system-follower package
        return None

    outfile = outdir / package_tmp_path.name
    if outfile.exists():
        logger.warning(f'Package {outfile} already exist. Skip Moving {package_tmp_path} to {outfile}')
    else:
        shutil.move(package_tmp_path, outfile)
        logger.debug(f'Moved {package_tmp_path} to {outfile}')
    logger.info(f'{_get_filename_without_suffix(outfile)} package is provided as docker image (Image: {package})')
    logger.success(f'Downloaded package from {package} to {outfile}')
    _save_info_about_downloaded_package(package, outfile)
    return outfile


def _get_current_path_using_mapping(package: PackageCLI | PackageCLIImage, packages_dir: Path) -> Path | None:
    """ Get ratio of downloaded package to image from which they were obtained

    :param package: package to be downloaded
    :param packages_dir: directory with downloaded packages
    :return: path to downloaded package or None if no package is downloaded
    """
    with open(IMAGE_PACKAGE_MAP, 'r') as file:
        content: dict[str, str] = json.load(file)
    downloaded_packages = packages_dir.glob('*.tar.gz')
    for downloaded_package in downloaded_packages:
        filename = _get_filename_without_suffix(downloaded_package, suffix=TarGzPlugin.suffix)
        file_target = content.get(filename)
        if file_target is None:
            continue
        if file_target == str(package):
            return downloaded_package
    return None


def get_client(
        registry_address: str, *, registry: RegistryInfo
) -> Dockerhub | Artifactory | Nexus:
    """ Identifies registry type and returns appropriate client

    :param registry_address: image registry (eg 'docker.io', 'artifactory.example.com:17001', 'nexus.host.com:16001')
    :param registry: registry information like credentials for auth, insecure mode, etc.
    :returns: Instance of Dockerhub, Artifactory, or Nexus client

    :raises UnknownRegistryError: registry could not be identified
    """
    scheme = 'http' if registry.is_insecure else 'https'
    if is_dockerhub(scheme, registry_address, registry_type=registry.type, is_insecure=registry.is_insecure):
        logger.info(f'{registry_address} is of type DockerHub')
        return Dockerhub(hostname=registry_address)

    if is_artifactory(scheme, registry_address, registry_type=registry.type, is_insecure=registry.is_insecure):
        logger.info(f'{registry_address} is of type Artifactory')
        return Artifactory(hostname=registry_address)

    if is_nexus(scheme, registry_address, registry_type=registry.type, is_insecure=registry.is_insecure):
        logger.info(f'{registry_address} is of type Nexus')
        return Nexus(hostname=registry_address)

    raise UnknownRegistryError(
        f'Could not determine the registry type for {registry_address}. '
        f'Supported registries: DockerHub, Artifactory, Nexus'
    )


def is_dockerhub(scheme: str, registry: str, *, registry_type: RegistryTypes, is_insecure: bool) -> bool:
    """ Check if the given registry is Dockerhub """
    if registry_type == RegistryTypes.dockerhub:
        return True
    if registry_type != RegistryTypes.auto:
        return False

    url = f'{scheme}://index.{registry}/v2'
    try:
        response = requests.get(url, timeout=3, verify=not is_insecure)
    except requests.exceptions.RequestException as error:
        logger.debug(f'DockerHub REST API call error: {error}')
        return False
    # dockerhub always returns 401 code and 'www-authenticate' header in this end point
    return response.status_code == 401 and 'docker.io/token' in response.headers.get('www-authenticate', '')


def is_artifactory(scheme: str, registry: str, *, registry_type: RegistryTypes, is_insecure: bool) -> bool:
    """ Check if the given registry is Artifactory """
    if registry_type == RegistryTypes.artifactory:
        return True
    if registry_type != RegistryTypes.auto:
        return False

    url = f'{scheme}://{registry}/artifactory/api/system/version'
    try:
        response = requests.get(url, timeout=3, verify=not is_insecure)
    except requests.exceptions.RequestException as error:
        logger.debug(f'Artifactory REST API call error: {error}')
        return False
    return response.status_code == 200


def is_nexus(scheme: str, registry: str, *, registry_type: RegistryTypes, is_insecure: bool) -> bool:
    """ Check if the given registry is Nexus """
    if registry_type == RegistryTypes.nexus:
        return True
    if registry_type != RegistryTypes.auto:
        return False

    url = f'{scheme}://{registry}/v2/_catalog'
    try:
        response = requests.get(url, timeout=3, verify=not is_insecure)
    except requests.exceptions.RequestException as error:
        logger.debug(f'Nexus REST API call error: {error}')
        return False
    return response.status_code == 200 and 'Nexus' in response.headers.get('Server', '')


def _save_info_about_downloaded_package(package: PackageCLI, current_package: Path) -> None:
    """ Save name and version mapping information from package.yaml with docker image name and tag

    :param package: package to be downloaded (docker image)
    :param current_package: downloaded package (tar.gz file)
    """
    with open(IMAGE_PACKAGE_MAP, 'r') as file:
        content: dict[str, str] = json.load(file)
    current_package_filename = _get_filename_without_suffix(current_package, suffix=TarGzPlugin.suffix)
    content[current_package_filename] = str(package)
    with open(IMAGE_PACKAGE_MAP, 'w') as file:
        json.dump(content, file, indent=4)


def _get_filename_without_suffix(path: Path, suffix: str = TarGzPlugin.suffix) -> str:
    """ Get file name without `suffix`

    :param path: file path
    :param suffix: file suffix, e.g. `.tar.gz`
    :return: file name without `suffix`
    """
    return path.name[:-len(suffix)]


def unpack(path: Path, outdir: Path) -> Path:
    """ Unpack package/.tar.gz file

    :param path: package/.tar.gz file path
    :param outdir: output directory
    :return: sources path of this package
    """
    filename = _get_filename_without_suffix(path, suffix=TarGzPlugin.suffix)
    package_dir = outdir / filename / PACKAGE_DIRNAME
    if package_dir.exists():
        return package_dir

    with tarfile.open(path) as tar:
        tar.extractall(package_dir.parent)
    return package_dir


def _get_fixed_package_using_mapping(package: PackageCLIImage | PackageCLITarGz | PackageCLISource) -> PackageCLI:
    """ Get ratio of downloaded package to image from which they were obtained

    :param package: package to be downloaded
    :return: path to downloaded package or None if no package is downloaded
    """
    with open(IMAGE_PACKAGE_MAP, 'r') as file:
        content: dict[str, str] = json.load(file)
    for key, value in content.items():
        if value == str(package):
            name, version = key.split('@')
            return PackageCLI(name=name, version=version)
    raise DownloadPackageError(f'Failed to parse dependency package name, version for {package}')
