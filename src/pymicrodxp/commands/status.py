""" SPDX-License-Identifier: Apache-2.0 """

import struct
from typing import Dict, Union, List

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


class StatusCommands:
    """General Communications and Control commands."""

    def __init__(self, driver):
        self._driver = driver
        self.log = driver.log

    @trace_command(0x41)
    def read_temperature(self) -> float:
        """
        0x41: Read Temperature
        :returns: The board temperature in Celsius
        """
        data = self._driver._transceive(0x41)
        int_temp = struct.unpack('<b', data[0:1])[0]
        frac_temp = data[1] / 256.0
        return int_temp + frac_temp

    @trace_command(0x42)
    def read_dsp_parameter_names(self, readout_option: int) -> Dict[str, Union[int, List[str]]]:
        """
        0x42: Read the ordered list of DSP parameter names.
        :param readout_option: 0: Return names and lengths, 1: Return lengths only.
        :returns: Dictionary with 'num_parameters', 'string_len', and optionally 'names'.
        """
        if readout_option not in (0, 1):
            raise ValueError("invalid readout option")

        data = self._driver._transceive(0x42, bytes([readout_option]))
        num_params = struct.unpack('<H', data[0:2])[0]
        string_len = struct.unpack('<H', data[2:4])[0]

        result = {
            "num_parameters": int(num_params),
            "string_len": int(string_len)
        }

        if readout_option == 0:
            names_raw = data[4:4 + string_len].decode('ascii')
            result["names"] = names_raw.rstrip('\x00').split('\x00')

        return result

    @trace_command(0x48)
    def read_serial_number(self) -> str:
        """
        0x48: Read Serial Number
        :returns: The board serial number
        """
        data = self._driver._transceive(0x48)
        return data.decode('ascii').rstrip('\x00')

    @trace_command(0x49)
    def get_board_information(self) -> Dict[str, Union[int, float, None]]:
        """
        0x49: Read board information

        Board information includes things like DSP, PIC and FIPPI versions, ADC speed grades,
        gain, and Nyquist filter info.

        Warning: The ADC Speed grade cannot be mapped to the ADC's sampling frequency despite the
                 information from the specification. The DSP clock speed will always match the
                 ADC's sampling frequency, so it gets used to calculate ADC clock periods.

        Warning: The FIPPI version and variant only contain the bottom byte of the full value.
                 This makes them an incomplete identifier for the actual version and variant.
                 Reading the values directly from the DSP memory is the only way to obtain the
                 full data.

        :returns: The board information
        """
        data = self._driver._transceive(0x49)

        mantissa = struct.unpack('<H', data[10:12])[0]
        exponent = struct.unpack('<b', data[12:13])[0]
        nominal_gain = (mantissa / 32768.0) * (2 ** exponent)

        self._driver.board_info.update({
            "pic_variant": data[0],
            "pic_major_version": data[1],
            "pic_minor_version": data[2],
            "dsp_variant": data[3],
            "dsp_major_version": data[4],
            "dsp_minor_version": data[5],
            "dsp_clock_speed_mhz": data[6],
            "clock_enable_register": data[7],
            "nfippi": data[8],
            "gain_mode": data[9],
            "nominal_gain": nominal_gain,
            "nyquist_filter": data[13],
            "adc_speed_grade": data[14],
            "adc_clk_period_s": 1. / data[6],
            "fpga_speed": data[15],
            "analog_power_supply": data[16],
            "fippi_decimation": data[17],
            "fippi_version": data[18],
            "fippi_variant": data[19]
        })

        return self._driver.board_info

    @trace_command(0x4B)
    def get_status(self) -> Dict[str, int]:
        """
        0x4B: Status

        Status information:
            * PIC status (0: OK)
            * DSP boot status (0: OK)
            * Run state (0: idle, 1: running)
            * DSP BUSY
            * DSP RUNERROR

        :returns: The board status
        """
        data = self._driver._transceive(0x4B)

        return {
            "pic_status": data[0],
            "dsp_boot_status": data[1],
            "run_state": data[2],
            "dsp_busy": data[3],
            "dsp_runerror": data[4]
        }

    @trace_command(0x4E)
    def reset_fpga(self) -> None:
        """0x4E: Reset the FPGA."""
        self._driver._transceive(0x4E, b'\xAA\x55\xAA\x55')

    @trace_command(0x4F)
    def reset_dsp(self) -> None:
        """0x4F: Reset the processor (DSP and FPGA)."""
        self._driver._transceive(0x4F, b'\xAA\x55\xAA\x55')
