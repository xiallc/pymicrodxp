""" SPDX-License-Identifier: Apache-2.0 """

import struct
import pytest
from unittest.mock import MagicMock, patch

from pymicrodxp.driver import MicroDXP
from pymicrodxp.core.error import MicroDXPError
from pymicrodxp.core.protocol import MicroDXPBase

from pymicrodxp.commands.status import StatusCommands
from pymicrodxp.commands.diagnostic import DiagnosticCommands
from pymicrodxp.commands.spectrometer_control import SpectrometerControlCommands

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


class TestBase:
    @pytest.fixture(autouse=True)
    def initialize_dxp(self):
        with patch('pymicrodxp.core.transport.serial.Serial') as mock_serial_class:
            self.mock_ser = mock_serial_class.return_value
            self.mock_ser.read.return_value = b''

            with patch.object(DiagnosticCommands, 'echo', return_value=b"PING", autospec=True), \
                    patch.object(StatusCommands, 'read_serial_number', return_value="1234",
                                 autospec=True), \
                    patch.object(StatusCommands, 'get_board_information', return_value={},
                                 autospec=True), \
                    patch.object(StatusCommands, 'read_dsp_parameter_names',
                                 return_value={'names': []}, autospec=True), \
                    patch.object(SpectrometerControlCommands, 'read_parameter_set', return_value=0,
                                 autospec=True), \
                    patch.object(SpectrometerControlCommands, 'read_general_set', return_value=0,
                                 autospec=True), \
                    patch.object(MicroDXPBase, '_auto_baud', autospec=True):
                self.dxp = MicroDXP(uri="serial://MOCK_PORT")

            self.dxp._transceive = MagicMock()
            self.dxp.board_info = {
                'pic_variant': 36,
                'pic_major_version': 4,
                'pic_minor_version': 22,
                'dsp_variant': 17,
                'dsp_major_version': 10,
                'dsp_minor_version': 30,
                'dsp_clock_speed_mhz': 40,
                'clock_enable_register': 1,
                'nfippi': 1,
                'gain_mode': 3,
                'nominal_gain': 1.0,
                'nyquist_filter': 2,
                'adc_speed_grade': 1,
                'adc_clk_period_s': 25e-9,
                'fpga_speed': 4,
                'analog_power_supply': 0,
                'fippi_decimation': 0,
                'fippi_version': 18,
                'fippi_variant': 17,
            }

    def setup_response(self, data_payload):
        """Helper to simulate a hardware data payload (no status byte)."""
        self.dxp._transceive.return_value = data_payload

    def setup_error(self, cmd_byte, status_code):
        """Simulates a hardware error by making the mock raise MicroDXPError."""
        self.dxp._transceive.side_effect = MicroDXPError(cmd_byte, status_code)

    def create_raw_packet(self, cmd_byte, status_byte, data=b''):
        """Helper to build a full raw binary packet for low-level serial testing."""
        payload = bytes([status_byte]) + data
        ndata = struct.pack('<H', len(payload))

        header_and_body = bytes([cmd_byte]) + ndata + payload
        checksum = 0
        for b in header_and_body:
            checksum ^= b

        return bytes([0x1B]) + header_and_body + bytes([checksum])
