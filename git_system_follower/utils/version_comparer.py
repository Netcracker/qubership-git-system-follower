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
from dataclasses import dataclass
from typing import Literal

CompareResult = Literal[-2, -1, 0, 1, 2]

# Matches the first occurrence of MAJOR.MINOR.PATCH anywhere in a string.
# Negative look-around prevents matching sub-sequences of longer dotted
# numbers such as "1.2.3.4".
_SEMVER_RE = re.compile(r"(?<!\d)(\d+)\.(\d+)\.(\d+)(?!\.\d)")
_QUARTERLY_RE = re.compile(r"(?<!\d)\d{2}\.(\d)(?!\d)_")


@dataclass(frozen=True)
class _ParsedVersion:
    prefix: str
    semver: tuple[int, int, int]
    suffix: str


class VersionComparer:
    def compare(self, v1: str, v2: str) -> CompareResult:
        """Compare two version strings.

        Returns:
            -2  if v1 < v2  and SEMVER major version differs (upgrade)
            -1  if v1 < v2  and SEMVER major is the same (or fallback lex)
             0  if v1 == v2
            +1  if v1 > v2  and SEMVER major is the same (or fallback lex)
            +2  if v1 > v2  and SEMVER major version differs (downgrade)
        """
        v1, v2 = v1.strip(), v2.strip()

        # Check for quarterly vs semver comparison first
        q1 = bool(_QUARTERLY_RE.search(v1))
        q2 = bool(_QUARTERLY_RE.search(v2))

        # If one is quarterly and the other is not, quarterly is always older
        if q1 and not q2:
            return -1
        if not q1 and q2:
            return 1

        p1 = self._parse(v1)
        p2 = self._parse(v2)

        if p1 is not None and p2 is not None:
            r = self._cmp(p1.prefix, p2.prefix)
            if r != 0:
                return r
            r = self._cmp_semver(p1.semver, p2.semver)
            if r != 0:
                return r
            return self._cmp(p1.suffix, p2.suffix)

        return self._cmp(v1, v2)

    def has_semver(self, version: str) -> bool:
        return self._parse(version.strip()) is not None

    def is_quarterly(self, version: str) -> bool:
        """Check if version uses quarterly versioning pattern"""
        return bool(_QUARTERLY_RE.search(version.strip()))

    @staticmethod
    def _parse(version: str) -> _ParsedVersion | None:
        m = _SEMVER_RE.search(version)
        if m is None:
            return None
        return _ParsedVersion(
            prefix=version[: m.start()],
            semver=(int(m.group(1)), int(m.group(2)), int(m.group(3))),
            suffix=version[m.end() :],
        )

    @staticmethod
    def _cmp_semver(
        parts1: tuple[int, int, int], parts2: tuple[int, int, int]
    ) -> CompareResult:
        maj1, min1, pat1 = parts1
        maj2, min2, pat2 = parts2
        if maj1 != maj2:
            return -2 if maj1 < maj2 else 2
        if (min1, pat1) < (min2, pat2):
            return -1
        if (min1, pat1) > (min2, pat2):
            return 1
        return 0

    @staticmethod
    def _cmp(a, b) -> CompareResult:
        if a < b:
            return -1
        if a > b:
            return 1
        return 0
