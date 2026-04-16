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


class TestPeripheralCommands(TestBase):

    @pytest.mark.parametrize("addr, cmd_len, read_len, err_msg", [
        (1, 2, 2, "invalid address"),
        (-1, 2, 2, "invalid address"),  # Negative Test
        (255, 2, 2, "invalid address"),
        (0x29, 0, 2, "invalid command byte length"),
        (0x29, -1, 2, "invalid command byte length"),  # Negative Test
        (0x29, 16, 2, "invalid command byte length"),
        (0x29, 2, 0, r"read length out of range: 64"),
        (0x29, 2, -1, r"read length out of range: 64"),  # Negative Test
        (0x29, 2, 65, r"read length out of range: 64"),
    ])
    def test_i2c_read_validation(self, addr, cmd_len, read_len, err_msg):
        """Failure: ValueError if parameters are out of range for read operation."""
        with pytest.raises(ValueError, match=err_msg):
            self.dxp.peripheral.read_i2c(address=addr, command_bytes=b'\x00' * cmd_len,
                                         read_len=read_len)

    @pytest.mark.parametrize("addr, cmd_len, write_len, err_msg", [
        (1, 2, 2, "invalid address"),
        (0x29, 0, 2, "invalid command byte length"),
        (0x29, 2, 0, r"write length out of range: 80"),
        (0x29, 2, 81, r"write length out of range: 80"),
    ])
    def test_i2c_write_validation(self, addr, cmd_len, write_len, err_msg):
        """Failure: ValueError if parameters are out of range for write operation."""
        with pytest.raises(ValueError, match=err_msg):
            self.dxp.peripheral.write_i2c(address=addr, command_bytes=b'\x00' * cmd_len,
                                          data=b'\x00' * write_len)

    def test_i2c_read_success(self):
        """Success: 0x40 I2C Read."""
        self.setup_response(b'\xde\xad')
        res = self.dxp.peripheral.read_i2c(0x29, b'\x00\x00', 2)
        assert res == b'\xde\xad'
        self.dxp._transceive.assert_called_with(0x40, b'\x00\x29\x02\x02\x00\x00')

    def test_i2c_write_success(self):
        """Success: 0x40 I2C Write."""
        self.setup_response(b'')
        self.dxp.peripheral.write_i2c(address=0x98, command_bytes=b'\x01', data=b'\x01\x02')
        self.dxp._transceive.assert_called_with(0x40, b'\x01\x98\x01\x02\x01\x01\x02')

    def test_hardware_error_propagation(self):
        """Failure: MicroDXPError raised on hardware fault."""
        self.setup_error(0x40, 0x01)
        with pytest.raises(MicroDXPError) as exc:
            self.dxp.peripheral.read_i2c(0x29, b'\x00', 2)
        assert exc.value.status == 0x01
