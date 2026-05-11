""" SPDX-License-Identifier: Apache-2.0 """
import pytest
from unittest.mock import MagicMock, patch, ANY
from pymicrodxp.core.transport import USBTransport
from .test_base import TestBase, HAS_USB, USB_ERROR

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


@pytest.mark.skipif(not HAS_USB, reason="pyusb not installed")
class TestUSBTransport(TestBase):
    def test_usb_transport_init_warnings(self):
        """Tests that we fail properly when we can't detach from the kernel driver."""
        with patch('pymicrodxp.core.transport.usb.core.find') as mock_find:
            mock_handle = mock_find.return_value = MagicMock()
            mock_handle.is_kernel_driver_active.return_value = True
            mock_handle.detach_kernel_driver.side_effect = USB_ERROR("Fail")
            USBTransport("usb://invalid_uri", timeout=1.0)

    def test_usb_init_bus_address_parsing(self):
        """Verify bus/address parsing and filtering in usb.core.find."""
        with patch('pymicrodxp.core.transport.usb.core.find') as mock_find:
            mock_handle = mock_find.return_value = MagicMock()
            mock_handle.is_kernel_driver_active.return_value = False

            # Test valid bus/address URI
            USBTransport("usb://2/10", timeout=2.0)

            _, kwargs = mock_find.call_args
            match_func = kwargs['custom_match']

            device = MagicMock()
            device.idVendor, device.idProduct = 0x10E9, 0x0B01
            device.bus, device.address = 2, 10

            assert match_func(device) is True
            device.bus = 3
            assert match_func(device) is False

    def test_usb_init_invalid_uri_parsing(self):
        """Verify fallback to standard find if URI path is invalid or missing."""
        with patch('pymicrodxp.core.transport.usb.core.find') as mock_find:
            mock_handle = mock_find.return_value = MagicMock()
            mock_handle.is_kernel_driver_active.return_value = False

            # URI with non-integer path
            USBTransport("usb://invalid/path", timeout=2.0)
            # Should have called find with default VID/PID instead of custom_match
            mock_find.assert_called_with(idVendor=0x10E9, idProduct=0x0B01)

    def test_usb_init_kernel_detach_failure(self):
        """Cover path where detaching a kernel driver fails with a warning."""
        with patch('pymicrodxp.core.transport.usb.core.find') as mock_find:
            mock_handle = mock_find.return_value = MagicMock()
            mock_handle.is_kernel_driver_active.return_value = True
            mock_handle.detach_kernel_driver.side_effect = USB_ERROR("Access Denied")

            transport = USBTransport("usb://", timeout=2.0)
            assert transport.handle == mock_handle

    # --- Memory and DMA Coverage ---

    def test_usb_read_memory_unhandled_error(self, initialize_usb_dxp):
        """Verify that non-timeout USBErrors are re-raised."""
        self.mock_usb_handle.read.reset_mock()
        self.mock_usb_handle.read.side_effect = USB_ERROR("Hardware Fault")
        with pytest.raises(USB_ERROR, match="Hardware Fault"):
            self.dxp.transport.read_memory(0x0, 10)

    def test_setup_packet_logic(self, initialize_usb_dxp):
        """Verify 32-bit mapping of address and length in setup packet."""
        addr, n_bytes = 0x12345678, 0xAABBCCDD
        self.dxp.transport._send_usb_setup_packet(addr, n_bytes, 1)

        sent_pkt = self.mock_usb_handle.write.call_args[0][1]
        assert sent_pkt[0:2] == b'\x78\x56'  # Addr low
        assert sent_pkt[2:6] == b'\xDD\xCC\xBB\xAA'  # Length 32-bit (fixed mapping)
        assert sent_pkt[7:9] == b'\x34\x12'  # Addr high

    # --- Protocol Exchange Coverage ---

    def test_exchange_small_packet(self, initialize_usb_dxp):
        """Verify that exchange() does NOT perform a second read for small packets."""
        cmd = 0x42
        small_packet = self.create_raw_packet(cmd, 0x00, b'\x00' * 10)

        with patch.object(USBTransport, 'read_memory', return_value=small_packet) as mock_read:
            result = self.dxp.transport.exchange(b'tx')
            assert result == small_packet
            assert mock_read.call_count == 1

    def test_usb_read_memory_alignment_padding(self, initialize_usb_dxp):
        """
        Verify that requests are rounded up to the nearest 512 bytes
        to prevent Overflow errors.
        """
        self.mock_usb_handle.read.reset_mock()
        # Request an unaligned size (2701 bytes)
        unaligned_size = 2701
        expected_req_size = 3072 # 512 * 6

        # Return a buffer of the padded size
        self.mock_usb_handle.read.return_value = b'\x00' * expected_req_size

        result = self.dxp.transport.read_memory(0x01000000, unaligned_size)

        # Verify the actual low-level request was padded to 3072
        self.mock_usb_handle.read.assert_called_with(0x82, expected_req_size, timeout=ANY)
        # Verify the returned data was sliced back to the original request
        assert len(result) == unaligned_size

    def test_usb_exchange_large_packet_re_read(self, initialize_usb_dxp):
        """Verify that exchange() triggers second read and pads the size."""
        cmd = 0x42
        # Data = 2696. Payload (+Status) = 2697. Total (+ESC,CMD,NDATA,CHK) = 2702.
        full_packet = self.create_raw_packet(cmd, 0x00, b'\x00' * 2696)

        with patch.object(USBTransport, 'read_memory') as mock_read:
            # Initial read returns partial, second read handles the logic
            mock_read.side_effect = [full_packet[:512], full_packet]

            result = self.dxp.transport.exchange(b'tx')

            assert len(result) == 2702
            # The second call to read_memory in exchange() passes total_len (2702)
            # which read_memory() itself will then pad to 3072 in the low-level call.
            mock_read.assert_called_with(0x01000000, 2702)

    def test_exchange_framing_error(self, initialize_usb_dxp):
        """Verify error if response doesn't start with ESC."""
        with patch.object(USBTransport, 'read_memory', return_value=b'\x00\x01\x02'):
            with pytest.raises(ConnectionError, match="USB framing error"):
                self.dxp.transport.exchange(b'tx')

    def test_exchange_empty_buffer(self, initialize_usb_dxp):
        """Ensures that we raise a connection error if we send an empty buffer."""
        with patch.object(USBTransport, 'read_memory', return_value=b''):
            with pytest.raises(ConnectionError, match="Empty Buffer"):
                self.dxp.transport.exchange(b'tx')

    def test_exchange_insufficient_re_read(self, initialize_usb_dxp):
        """Ensures that we re-read if there's an error."""
        cmd = 0x42
        full_packet = self.create_raw_packet(cmd, 0x00, b'\x00' * 1000)
        with patch.object(USBTransport, 'read_memory') as mock_read:
            mock_read.side_effect = [
                full_packet[:512],
                b'\x1B' + b'\x00' * 10  # Second read is too short
            ]
            with pytest.raises(ConnectionError, match="received 11"):
                self.dxp.transport.exchange(b'tx')

    def test_close(self, initialize_usb_dxp):
        """Ensures we can close the handle properly"""
        self.dxp.transport.close()
        assert self.dxp.transport.handle is None

    def test_protocol_read_usb_memory(self):
        """ensures we can read the USB memory"""
        self.dxp.close()
        self.dxp.transport = MagicMock(spec=USBTransport)
        self.dxp.read_usb_memory(0x100, 10)
        self.dxp.transport.read_memory.assert_called_once()
