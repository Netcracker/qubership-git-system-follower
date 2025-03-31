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

""" Module with custom errors """


class CLIParamsError(Exception):
    def __init__(self, msg, *args):
        super().__init__(msg, *args)


class ParsePackageNameError(CLIParamsError):
    def __init__(self, msg, *args):
        super().__init__(msg, *args)


class RemoteRepositoryError(Exception):
    def __init__(self, msg, *args):
        super().__init__(msg, *args)


class InstallationError(Exception):
    def __init__(self, msg, *args):
        super().__init__(msg, *args)


class UninstallationError(Exception):
    def __init__(self, msg, *args):
        super().__init__(msg, *args)


""" --------------------------------------- """


class PackageNotFoundError(Exception):
    def __init__(self, msg, *args):
        super().__init__(msg, *args)


class MaxDependencyDepthError(Exception):
    def __init__(self, msg, *args):
        super().__init__(msg, *args)


class PackageDescriptionFileError(Exception):
    def __init__(self, msg, *args):
        super().__init__(msg, *args)


class DescriptionSectionError(PackageDescriptionFileError):
    def __init__(self, msg, *args):
        super().__init__(msg, *args)


""" --------------------------------------- """


class PackageNamePolicyError(Exception):
    def __init__(self, msg, *args):
        super().__init__(msg, *args)


class PackageApiError(Exception):
    def __init__(self, msg, *args):
        super().__init__(msg, *args)


class PackageInterfaceError(PackageApiError):
    def __init__(self, msg, *args):
        super().__init__(msg, *args)


class PackageAPIDevelopmentError(PackageInterfaceError):
    def __init__(self, msg, *args):
        super().__init__(msg, *args)


class PackageCICDVariablePolicyError(PackageInterfaceError):
    def __init__(self, msg, *args):
        super().__init__(msg, *args)


class PackageTemplatePolicyError(PackageInterfaceError):
    def __init__(self, msg, *args):
        super().__init__(msg, *args)


class StateFileError(Exception):
    def __init__(self, msg, *args):
        super().__init__(msg, *args)


class HashesMismatch(StateFileError):
    def __init__(self, msg, state_file_hash: str, generated_hash: str, *args):
        self.state_file_hash = state_file_hash
        self.generated_hash = generated_hash
        super().__init__(msg, *args)


class DownloadPackageError(Exception):
    def __init__(self, msg, *args):
        super().__init__(msg, *args)


class UnknownRegistryError(DownloadPackageError):
    """ Raised when the registry type cannot be determined """
    def __init__(self, msg, *args):
        super().__init__(msg, *args)

""" --------------------------------------- """

class PluginError(Exception):
    def __init__(self, msg, *args):
        super().__init__(msg, *args)


class InvalidPlugin(PluginError):
    def __init__(self, msg, *args):
        super().__init__(msg, *args)


class PluginExecutionError(PluginError):
    def __init__(self, msg, *args):
        super().__init__(msg, *args)
