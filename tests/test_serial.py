""" SPDX-License-Identifier: Apache-2.0 """
import pytest

from unittest.mock import patch
from pymicrodxp.core.transport import Transport, SerialTransport
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


class TestSerial(TestBase):

    def test_read_memory_with_serial(self):
        """Ensures that if we try to access read_memory with Serial, that we error. """
        with pytest.raises(ValueError, match="requires a USB connection"):
            base = Transport("serial://COM3", 1.0)
            base.read_memory(0, 0)

    def test_serial_transport_failures(self):
        """Covers various transport errors get handled properly"""
        with patch('pymicrodxp.core.transport.serial.Serial') as mock_serial:
            mock_inst = mock_serial.return_value
            transport = SerialTransport("serial://COM3", 1.0)

            transport.set_baudrate(9600)
            assert mock_inst.baudrate == 9600

            mock_inst.read_until.return_value = b''
            with pytest.raises(ConnectionError, match="no start packet marker"):
                transport.exchange(b'tx')

            mock_inst.read_until.return_value = b'\x1B'
            mock_inst.read.side_effect = [b'\x41', b'\x0A\x00',
                                          b'\x00']  # ndata=10, but only 1 byte read
            with pytest.raises(ConnectionError, match="Expected 10 bytes"):
                transport.exchange(b'tx')

            transport.close()
            assert transport.handle is None
