""" SPDX-License-Identifier: Apache-2.0 """

import pytest
from pymicrodxp.core.error import MicroDXPError
from .test_base import TestBase

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


class TestDiagnosticCommands(TestBase):

    @pytest.mark.parametrize("data_type", [-1, 6])
    def test_read_diagnostic_histogram_validation(self, data_type):
        """Failure: ValueError if data_type is out of range."""
        with pytest.raises(ValueError, match="Invalid data_type"):
            self.dxp.diagnostic.read_diagnostic_histogram(data_type=data_type)

    def test_read_diagnostic_histogram(self):
        """Success: 0x10 Read diagnostic histogram."""
        fake_data = bytearray([0] * 2048)
        fake_data[1000] = 0xD2  # Low byte
        fake_data[1001] = 0x04  # High byte
        self.setup_response(bytes(fake_data))

        result = self.dxp.diagnostic.read_diagnostic_histogram(data_type=0)

        assert len(result) == 1024
        assert result[500] == 1234
        self.dxp._transceive.assert_called_with(0x10, b'\x00')

    @pytest.mark.parametrize("interval, t_pos, t_type, tr_type, err_msg", [
        (0x10000, 0, 0, 0, "sampling_interval must be between 0 and 0xFFFF"),
        (-1, 0, 0, 0, "sampling_interval must be between 0 and 0xFFFF"),  # Negative Test
        (0, 1, 0, 0, "Invalid trigger_position"),
        (0, -1, 0, 0, "Invalid trigger_position"),  # Negative Test
        (0, 0, 3, 0, "Invalid trigger_type"),
        (0, 0, -1, 0, "Invalid trigger_type"),  # Negative Test
        (0, 0, 0, 9, "Invalid trace_type"),
        (0, 0, 0, -1, "Invalid trace_type"),  # Negative Test
    ])
    def test_read_diagnostic_trace_validation(self, interval, t_pos, t_type, tr_type, err_msg):
        with pytest.raises(ValueError, match=err_msg):
            self.dxp.diagnostic.read_diagnostic_trace(interval, t_pos, t_type, tr_type)

    def test_transceive_validation(self):
        """Failure: ValueError if command byte is out of range."""
        with pytest.raises(ValueError, match="invalid command byte"):
            self.dxp.diagnostic.transceive(-1, b'\x00')
        with pytest.raises(ValueError, match="invalid command byte"):
            self.dxp.diagnostic.transceive(0x100, b'\x00')

    def test_read_diagnostic_trace(self):
        """Success: 0x11 Read diagnostic trace."""
        fake_data = bytearray([0] * 16000)
        fake_data[0] = 0x00
        fake_data[1] = 0x10
        self.setup_response(bytes(fake_data))

        result = self.dxp.diagnostic.read_diagnostic_trace(0, 128, 0, 0)
        assert len(result) == 8000
        assert result[0] == 4096

    def test_echo_command(self):
        """Success: 0x4A Echo command."""
        test_payload = b"Hello microDXP!"
        self.setup_response(test_payload)

        result = self.dxp.diagnostic.echo(test_payload)
        assert result == test_payload
        self.dxp._transceive.assert_called_with(0x4A, test_payload)

    def test_hardware_error_propagation(self):
        """Failure: MicroDXPError raised on hardware fault."""
        self.setup_error(0x10, 0x01)
        with pytest.raises(MicroDXPError) as exc:
            self.dxp.diagnostic.read_diagnostic_histogram()
        assert exc.value.status == 0x01
