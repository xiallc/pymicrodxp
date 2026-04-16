""" SPDX-License-Identifier: Apache-2.0 """
import struct
import pytest

from pymicrodxp.core.protocol import MicroDXPBase
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


class TestProtocol(TestBase):

    @pytest.fixture(autouse=True)
    def restore_transceive(self, initialize_dxp):
        """Ensure we use the real _transceive logic for these tests instead of the mock."""
        self.dxp._transceive = MicroDXPBase._transceive.__get__(self.dxp, self.dxp.__class__)

    def test_transceive_success(self):
        """Happy Path: Verify successful command execution and payload stripping."""
        cmd = 0x41  # READ_TEMPERATURE
        status_byte = 0x00
        data_payload = b'\x14\x80'  # 20.5 C
        packet = self.create_raw_packet(cmd, status_byte, data_payload)

        # Mock the serial sequence
        self.mock_ser.read_until.return_value = b'\x1B'
        self.mock_ser.read.side_effect = [
            bytes([packet[1]]),  # Cmd
            packet[2:4],  # Ndata
            packet[4:-1],  # Payload (Status + Data)
            bytes([packet[-1]])  # Checksum
        ]

        result = self.dxp._transceive(cmd)
        assert result == data_payload

    def test_transceive_timeout_no_esc(self):
        """Error: ConnectionError raised if ESC marker is never found."""
        self.mock_ser.read_until.return_value = b''

        with pytest.raises(ConnectionError, match="timeout: no start packet marker"):
            self.dxp._transceive(0x41)

    def test_transceive_command_mismatch(self):
        """Error: ValueError raised if response command byte doesn't match request."""
        self.mock_ser.read_until.return_value = b'\x1B'

        self.mock_ser.read.side_effect = [
            bytes([0x99]),  # Cmd (mismatched)
            b'\x00\x00',  # Ndata (0)
            b'',  # Data
            b'\x00'  # Checksum
        ]

        with pytest.raises(ValueError, match="Command mismatch"):
            self.dxp._transceive(0x41)

    def test_transceive_incomplete_ndata(self):
        """Error: ConnectionError raised if Ndata length bytes are missing."""
        self.mock_ser.read_until.return_value = b'\x1B'
        self.mock_ser.read.side_effect = [bytes([0x41]), b'\x01']  # Only 1 byte of Ndata

        with pytest.raises(ConnectionError, match="Incomplete Ndata length received"):
            self.dxp._transceive(0x41)

    def test_transceive_incomplete_payload(self):
        """Error: ConnectionError raised if actual payload is shorter than Ndata."""
        cmd = 0x41
        # Claim 10 bytes (Ndata), but return only 2
        ndata_bytes = struct.pack('<H', 10)
        self.mock_ser.read_until.return_value = b'\x1B'
        self.mock_ser.read.side_effect = [bytes([cmd]), ndata_bytes, b'\x00\x01']

        with pytest.raises(ConnectionError, match="Expected 10 bytes, received 2"):
            self.dxp._transceive(cmd)

    def test_transceive_checksum_mismatch(self):
        """Error: ValueError raised if calculated checksum fails."""
        cmd = 0x41
        packet = self.create_raw_packet(cmd, 0x00, b'\x01\x02')

        self.mock_ser.read_until.return_value = b'\x1B'
        self.mock_ser.read.side_effect = [
            bytes([packet[1]]),
            packet[2:4],
            packet[4:-1],
            b'\xFF'  # Intentional wrong checksum
        ]

        with pytest.raises(ValueError, match="Checksum mismatch"):
            self.dxp._transceive(cmd)

    def test_transceive_hardware_error(self):
        """Error: MicroDXPError raised if status byte is non-zero."""
        cmd = 0x08  # TAKE_MCA_SNAPSHOT
        status_err = 0x01  # MCALEN > 4096
        packet = self.create_raw_packet(cmd, status_err)

        self.mock_ser.read_until.return_value = b'\x1B'
        self.mock_ser.read.side_effect = [
            bytes([packet[1]]),
            packet[2:4],
            packet[4:-1],
            bytes([packet[-1]])
        ]

        # Verify that the specific hardware error is raised
        with pytest.raises(MicroDXPError) as exc:
            self.dxp._transceive(cmd)
        assert exc.value.status == status_err

    def test_transceive_echo_special_handling(self):
        """Special Case: ECHO (0x4A) returns the full payload including the first byte."""
        cmd = 0x4A
        # ECHO does not have a status byte in the payload; the whole thing is data
        echo_payload = b'HelloDXP'

        # Build packet manually since ECHO doesn't follow the status-byte convention
        ndata = struct.pack('<H', len(echo_payload))
        cs = cmd ^ ndata[0] ^ ndata[1]
        for b in echo_payload: cs ^= b
        packet = b'\x1B' + bytes([cmd]) + ndata + echo_payload + bytes([cs])

        self.mock_ser.read_until.return_value = b'\x1B'
        self.mock_ser.read.side_effect = [
            bytes([cmd]),
            ndata,
            echo_payload,
            bytes([cs])
        ]

        result = self.dxp._transceive(cmd, b'HelloDXP')
        # Ensure the first byte is NOT stripped for ECHO commands
        assert result == echo_payload
