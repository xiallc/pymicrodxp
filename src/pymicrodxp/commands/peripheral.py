""" SPDX-License-Identifier: Apache-2.0 """
import struct

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


class PeripheralCommands:
    """Commands related to controlling peripheral devices via the general I2C cmd interface."""

    def __init__(self, driver):
        self._driver = driver
        self.log = driver.log

    MAX_ADDRESS = 0xFE
    MIN_ADDRESS = 0x2
    MAX_CMD_BYTES = 0xF
    MAX_READ_LEN_BYTES = 64
    MAX_WRITE_LEN_BYTES = 80

    def _validate_i2c_input(self, address: int, cmd_len: int, length: int, isread: bool):
        if not (self.MIN_ADDRESS <= address <= self.MAX_ADDRESS):
            raise ValueError("invalid address")

        if not (0 < cmd_len <= self.MAX_CMD_BYTES):
            raise ValueError("invalid command byte length")

        max_len = self.MAX_WRITE_LEN_BYTES
        op = 'write'
        if isread:
            max_len = self.MAX_READ_LEN_BYTES
            op = 'read'

        if not (0 < length <= max_len):
            raise ValueError(f"{op} length out of range: {max_len}")

    @trace_command(0x40, 'read')
    def read_i2c(self, address: int, command_bytes: bytes, read_len: int) -> bytes:
        """
        0x40: I2C Read
        :param address: 7-bit I2C address (2-254).
        :param command_bytes: Bytes to send as register/command prefix.
        :param read_len: Number of bytes to read.
        :returns: A bytes array of the response from the provided I2C address.
        """
        n_cmd = len(command_bytes)
        self._validate_i2c_input(address, n_cmd, read_len, isread=True)
        payload = struct.pack('<BBBB', 0, address, n_cmd, read_len) + command_bytes
        return self._driver._transceive(0x40, payload)

    @trace_command(0x40, 'write')
    def write_i2c(self, address: int, command_bytes: bytes, data: bytes) -> bytes:
        """
        0x40: I2C Write
        :param address: 7-bit I2C address (2-254).
        :param command_bytes: The command bytes to send to the provided I2C address.
        :param data: A list of bytes to send as the command payload.
        :returns: Nothing on a write operation
        """
        n_cmd = len(command_bytes)
        ni2cd = len(data)
        self._validate_i2c_input(address, n_cmd, ni2cd, isread=False)
        payload = struct.pack('<BBBB', 1, address, n_cmd, ni2cd) + command_bytes + data
        self._driver._transceive(0x40, payload)
