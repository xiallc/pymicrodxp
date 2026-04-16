""" SPDX-License-Identifier: Apache-2.0 """

from typing import Dict

from .registry import COMMAND_REGISTRY

"""
Copyright 2026 XIA LLC, All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


def add_registry_entries(self, entries: Dict[int, Dict]):
    """Dynamically expand the command registry for extensions."""
    COMMAND_REGISTRY.update(entries)


def calculate_checksum(payload: bytes) -> int:
    """
    Calculate the checksum using a payload of bytes.
    :param payload: The payload, excluding the escape prefix.
    :return: The exclusive-OR checksum.
    """
    checksum = 0
    for byte in payload:
        checksum ^= byte
    return checksum


def sec_to_ticks(seconds: float, s_per_tick: int) -> int:
    """
    Helper to convert seconds to hardware ticks.
    Uses round() to prevent truncation errors from floating point precision.
    """
    return int(round(seconds / s_per_tick))


def ticks_to_sec(ticks: int, s_per_tick: int) -> float:
    """Helper to convert hardware ticks to seconds."""
    return ticks * s_per_tick
