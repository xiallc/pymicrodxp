""" SPDX-License-Identifier: Apache-2.0 """

import struct
from typing import List

from ..core.logging import trace_command

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


class DiagnosticCommands:
    """Mixin for Diagnostic Tools and tests."""

    def __init__(self, driver):
        self._driver = driver
        self.log = driver.log

    @trace_command(0x10, 'read')
    def read_diagnostic_histogram(self, data_type: int = 0) -> List[int]:
        """
        0x10: Read diagnostic histogram. The histogram is 1 kword of diagnostic samples.
        :param data_type: Type of diagnostic histogram that we want to collect. Changing the data
                          type will reset the histogram. If unmodified, then it reads back the
                          latest histogram.
                          Values:
                          0 = Baseline
                          1 = ADC
                          2 = Fast-filter output
                          3 = Raw baseline
                          4 = Subtracted raw baseline
                          5 = Slow-filter baseline
        :returns: The diagnostic histogram.
        """
        if data_type not in range(0, 6):
            raise ValueError("Invalid data_type")

        data = self._driver._transceive(0x10, bytes([data_type]))
        return [
            int.from_bytes(data[i:i + 2], byteorder='little')
            for i in range(0, 2048, 2)
        ]

    @trace_command(0x11, 'read')
    def read_diagnostic_trace(self, sampling_interval: int = 0, trigger_position: int = 0,
                              trigger_type: int = 0, trace_type: int = 0) -> List[int]:
        """
        0x11: Read diagnostic trace.

        Fills the 8000-deep HISTORY buffer with 16-bit unsigned data samples of the selected type,
        each separated by the specified number of clock ticks.

        :param sampling_interval: Interval in digitizing clock periods.
        :param trigger_position: 0 (No pre-trigger), 128 (50%), 255 (All pre-trigger).
        :param trigger_type: 0 (Free run), 1 (Fast-filter), 2 (Intermediate/slow),
                          4 (Good event), 8 (Overflow), 16 (Underflow),
                          32 (Fast pileup), 64 (Slow pileup), 128 (ADC out-of-range).
        :param trace_type: 0 (ADC), 1 (ADC Avg), 2 (Fast Filter), 3 (Raw Intermediate),
                        4 (Baseline Samples), 5 (Baseline Avg), 6 (Scaled Intermediate),
                        7 (Raw Slow Filter), 8 (Scaled Slow Filter).
        :returns:
        """
        if not (0 <= sampling_interval <= 0xFFFF):
            raise ValueError("sampling_interval must be between 0 and 0xFFFF")
        if trigger_position not in (0, 128, 255):
            raise ValueError("Invalid trigger_position")
        if trigger_type not in (0, 1, 2, 4, 8, 16, 32, 64, 128):
            raise ValueError("Invalid trigger_type")
        if trace_type not in range(0, 9):
            raise ValueError("Invalid trace_type")

        payload = struct.pack('<HBBBB', sampling_interval, 0, trigger_position, trigger_type,
                              trace_type)
        data = self._driver._transceive(0x11, payload)
        num_samples = len(data) // 2
        return list(struct.unpack(f'<{num_samples}H', data))

    @trace_command(0x4A)
    def echo(self, payload: bytes) -> bytes:
        """Command 0x4A: Echoes command payload back."""
        return self._driver._transceive(0x4A, payload)

    def transceive(self, cmd_byte: int, data: bytes = b'') -> bytes:
        """
        Public wrapper for the internal transceive call. This API function may change without
        notice. It's provided as a convenience for internal testing and not for general use.
        :param cmd_byte: The command byte that we'll execute the call with.
        :param data: The data to be sent with the command.
        :returns: The response payload from the transceive call with the status byte stripped.
        """
        if not (0 <= cmd_byte <= 0xFF):
            raise ValueError("invalid command byte")
        return self._driver._transceive(cmd_byte, data)
