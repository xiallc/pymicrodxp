""" SPDX-License-Identifier: Apache-2.0 """
import pytest

from unittest.mock import patch
from pymicrodxp.core.transport import Transport, SerialTransport, USBTransport
from .test_base import TestBase, HAS_USB

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


class TestTransport(TestBase):
    """Tests related to the base transport class"""

    # --- Transport Factory Gaps ---
    def test_transport_factory_success(self):
        """Coverage for transport.py: create() success paths."""
        with patch('pymicrodxp.core.transport.serial.Serial'):
            t_serial = Transport.create("serial://COM3", 1.0)
            assert isinstance(t_serial, SerialTransport)

        if HAS_USB:
            with patch('pymicrodxp.core.transport.usb.core.find'):
                t_usb = Transport.create("usb://", 1.0)
                assert isinstance(t_usb, USBTransport)

    def test_transport_factory_fail(self):
        """Coverage for transport.py: create() unsupported scheme."""
        with pytest.raises(ValueError, match="Unsupported URI scheme"):
            Transport.create("invalid://port", 1.0)

    def test_transport_base_unimplemented(self):
        """Ensures that if we provide a URI base that we don't know we error out."""
        base = Transport("none://", 1.0)
        with pytest.raises(NotImplementedError): base.exchange(b'')
        with pytest.raises(NotImplementedError): base.close()
        with pytest.raises(ValueError, match="requires a USB connection"):
            base.read_memory(0, 0)
