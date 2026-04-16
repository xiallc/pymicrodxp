""" SPDX-License-Identifier: Apache-2.0 """

import struct
from typing import Dict, List, Any, Union

from ..core.logging import trace_command
from ..core.utils import ticks_to_sec, sec_to_ticks

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


class RunControlCommands:
    """Run control commands"""

    def __init__(self, driver):
        self._driver = driver
        self.log = driver.log

    @trace_command(0x00)
    def start_run(self, clear_mca: bool = True) -> int:
        """
        0x00: Enable data taking.
        :param clear_mca: When True starts a new MCA data run. If False, resumes previous run.
        :returns: The run number provided by the hardware.
        """
        payload = b'\x01' if clear_mca else b'\x00'
        data = self._driver._transceive(0x00, payload)
        run_number = struct.unpack('<H', data[0:2])[0]
        return run_number

    @trace_command(0x01)
    def end_run(self):
        """
        0x01: Stop data taking.
        :returns: Nothing because an error would already raise a MicroDXPError.
        """
        self._driver._transceive(0x01)

    @trace_command(0x02)
    def read_mca(self, first: int, num: int, bpb: int, snapshot: bool = False) -> List:
        """
        0x02 | 0x09: Read MCA spectrum
        :param first: The first bin MCA bin.
        :param num: The number of MCA bins that will be read.
        :param bpb: The number of bytes each bin represents.
        :param snapshot: If True, we will read an MCA snapshot. False, will read a normal MCA.
        :returns: A dictionary containing the spectrum data.
        """
        if not (0 <= first <= 0xFFFF):
            raise ValueError("invalid first bin")
        if not (0 < num <= 0xFFFF):
            raise ValueError("invalid number of MCA bins")
        if bpb not in (1, 2, 3):
            raise ValueError("invalid bytes per bin")

        payload = struct.pack('<HHB', first, num, bpb)
        if not snapshot:
            data = self._driver._transceive(0x02, payload)
        else:
            data = self._driver._transceive(0x09, payload)

        mca = []
        for i in range(0, len(data), bpb):
            mca.append(int.from_bytes(data[i:i + bpb], 'little'))

        return mca

    @trace_command(0x04)
    def read_multisca(self):
        """
        0x04 | 0x0C: Reads the number of events in defined SCA regions.
        :return: Not implemented.
        """
        raise NotImplementedError("Command 0x04 (Read MultiSCA) is not supported.")

    @trace_command(0x06, 'read')
    def read_run_statistics(self, mode: int = 0, snapshot: bool = False) -> Dict[str, Any]:
        """
        0x06 | 0x0A: Reads run statistics from the hardware.
        Statistics data include real time, livetime, input events, output events, overflows and
        underflows.
        :param mode: Determined the specific data that get read out. 0 omits over and underflows.
                     1 includes all data.
        :param snapshot: If True, we will read a snapshot, and set mode = 1. If False, the data will
                         be read as a normal statistics read, and mode will follow requested value.
        :return: A dictionary containing the statistics data with all times in seconds.
        """
        """Reads the snapshot statistics."""
        if mode not in (0, 1):
            raise ValueError("invalid mode")

        if not snapshot:
            data = self._driver._transceive(0x06, bytes([mode]))
        else:
            data = self._driver._transceive(0x0A)
            mode = 1

        lt_ticks = int.from_bytes(data[0:6], 'little')
        rt_ticks = int.from_bytes(data[6:12], 'little')

        stats = {
            "livetime": ticks_to_sec(lt_ticks, self._driver.STAT_CLK_PERIOD_S),
            "realtime": ticks_to_sec(rt_ticks, self._driver.STAT_CLK_PERIOD_S),
            "input_events": int.from_bytes(data[12:16], 'little'),
            "output_events": int.from_bytes(data[16:20], 'little'),
        }
        if mode == 1:
            stats["underflows"] = int.from_bytes(data[20:24], 'little')
            stats["overflows"] = int.from_bytes(data[24:28], 'little')

        return stats

    def _decode_run_preset(self, data: bytes) -> Dict[str, Union[float, int]]:
        result = {
            "preset_type": data[0],
        }

        length = int.from_bytes(data[1:], 'little')
        if data[0] in [1, 2]:
            length = ticks_to_sec(length, self._driver.PRESET_CLK_PERIOD_S)
        result['length'] = length
        return result

    @trace_command(0x07, 'read')
    def read_run_preset(self) -> Dict[str, Union[float, int]]:
        """
        0x07: Read preset run configuration.
        :returns: A dictionary containing the preset type and stop condition.
        """
        data = self._driver._transceive(0x07, b'\x01')
        return self._decode_run_preset(data)

    @trace_command(0x07, 'write')
    def write_run_preset(self, preset_type: int, length: float = 0) -> Dict[str, Union[float, int]]:
        """
        0x07: Set preset run configuration.
        System defaults to no preset run length (i.e. 0). Values are persistent once set.
        :param preset_type: Sets the preset run type to one of the following stop conditions:
                            0 -> no preset, indefinite run length;
                            1 -> stops when real time matches defined run length in seconds;
                            2 -> stops when live time matches defined run length in seconds;
                            3 -> stops when reaching the specified number of output counts;
                            4 -> stops when reaching the specified number of input counts.
        :param length: The value to use to stop the data run. If setting this value for a timed
                       mode, then the units are seconds. If setting for count modes, then this
                       is unitless.
        :returns: The current preset run configuration.
        """
        if preset_type not in (0, 1, 2, 3, 4):
            raise ValueError("invalid preset type")
        if length < 0:
            raise ValueError("preset length cannot be negative")

        if preset_type in [1, 2]:
            val = sec_to_ticks(length, self._driver.PRESET_CLK_PERIOD_S)
        else:
            val = int(round(length, 0))

        low = val & 0xFFFF
        mid = (val >> 16) & 0xFFFF
        high = (val >> 32) & 0xFFFF
        if high != 0:
            payload = struct.pack('<BBHHH', 0, preset_type, low, mid, high)
        else:
            payload = struct.pack('<BBHH', 0, preset_type, low, mid)
        data = self._driver._transceive(0x07, payload)
        return self._decode_run_preset(data)

    @trace_command(0x08)
    def take_snapshot(self, clear: bool = False):
        """
        0x08: Take MCA Snapshot.
        Requires that the MCA length be 4096 or less.
        :param clear: If True, the system clears the snapshot MCA and stats after read. If False,
                      then the MCA and stats will continue to accumulate.
        """
        payload = b'\x01' if clear else b'\x00'
        self._driver._transceive(0x08, payload)

    @trace_command(0x0B)
    def set_run_mode(self, mode: int) -> None:
        """
        0x0B: Set Run Mode **Not supported by standard firmware**
        """
        raise NotImplementedError("Command 0x0B (Set Run Mode) is not supported.")
