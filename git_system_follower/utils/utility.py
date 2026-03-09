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

def normalized_in_string_match(tocompare: str, comparedto: str)-> bool:
    """
    Remove all non-alphanumeric characters (hyphens, underscores, dots, slashes, colons)
    This turns both strings into pure blocks of letters and numbers
    """
    flat1 = re.sub(r'[^a-zA-Z0-9]', '', tocompare)
    flat2 = re.sub(r'[^a-zA-Z0-9]', '', comparedto)
    return flat1 in flat2
