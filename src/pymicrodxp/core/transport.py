""" SPDX-License-Identifier: Apache-2.0 """

import time
import struct
import urllib.parse
import serial

try:
    import usb.core
    import usb.util
except ImportError:
    usb = None

from .logging import logger

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


class Transport:
    """Abstract base class for hardware transports."""
    ESC = b'\x1B'

    def __init__(self, uri: str, timeout: float):
        self.uri = uri
        self.timeout = timeout
        self.use_usb = False

        parsed = urllib.parse.urlparse(uri)
        self.scheme = parsed.scheme
        self.netloc = parsed.netloc
        self.path = parsed.path

    @staticmethod
    def create(uri: str, timeout: float) -> "Transport":
        """
        Factory method to instantiate the correct transport based on URI scheme.
        :param uri: Hardware URI (serial:// or usb://)
        :param timeout: Communication timeout in seconds
        :returns: An instance of SerialTransport or USBTransport
        """
        if uri.startswith("usb://"):
            return USBTransport(uri, timeout)
        elif uri.startswith("serial://"):
            return SerialTransport(uri, timeout)
        else:
            raise ValueError(f"Unsupported URI scheme. Use 'serial://' or 'usb://'. Got: {uri}")

    def exchange(self, packet: bytes) -> bytes:
        """Sends a packet and returns the fully extracted response packet."""
        raise NotImplementedError

    def read_memory(self, addr: int, num_bytes: int) -> bytes:
        raise ValueError("Direct memory access requires a USB connection.")

    def close(self):
        raise NotImplementedError


class SerialTransport(Transport):
    """RS-232 Serial transport implementation."""

    def __init__(self, uri: str, timeout: float):
        super().__init__(uri, timeout)
        self.port = self.netloc + self.path
        self.handle = serial.Serial(port=self.port, baudrate=115200, timeout=self.timeout)
        logger.info(f"Initialized Serial transport on {self.port}")

    def set_baudrate(self, baudrate: int):
        self.handle.baudrate = baudrate

    def exchange(self, packet: bytes) -> bytes:
        self.handle.reset_input_buffer()
        self.handle.write(packet)
        self.handle.flush()

        sync = self.handle.read_until(self.ESC)
        if not sync or sync[-1:] != self.ESC:
            raise ConnectionError("timeout: no start packet marker")

        resp_cmd_bytes = self.handle.read(1)
        if not resp_cmd_bytes:
            raise ConnectionError("timeout: no command byte received")

        resp_ndata_bytes = self.handle.read(2)
        if len(resp_ndata_bytes) < 2:
            raise ConnectionError("Incomplete Ndata length received.")
        resp_ndata = struct.unpack('<H', resp_ndata_bytes)[0]

        resp_data = self.handle.read(resp_ndata)
        if len(resp_data) < resp_ndata:
            raise ConnectionError(f"Expected {resp_ndata} bytes, received {len(resp_data)}")

        resp_checksum_bytes = self.handle.read(1)
        if not resp_checksum_bytes:
            raise ConnectionError("timeout: no checksum byte received")

        return self.ESC + resp_cmd_bytes + resp_ndata_bytes + resp_data + resp_checksum_bytes

    def close(self):
        if self.handle:
            self.handle.close()
            self.handle = None


class USBTransport(Transport):
    """Cypress EZ-USB transport implementation with DMA support."""
    XIA_VID = 0x10E9
    XIA_PID = 0x0B01
    XIA_UART_ADDRESS = 0x01000000
    USB_SETUP_FLAG_WRITE = 0
    USB_SETUP_FLAG_READ = 1
    USB_SMALL_READ_PAD = 512

    EP_SETUP_OUT = 0x01
    EP_DATA_OUT = 0x06
    EP_DATA_IN = 0x82

    def __init__(self, uri: str, timeout: float):
        super().__init__(uri, timeout)
        self.use_usb = True

        if usb is None:
            raise ImportError("USB support requires the 'pyusb' package.")

        bus, address = None, None
        if self.netloc and self.path:
            try:
                bus = int(self.netloc)
                address = int(self.path.strip('/'))
            except ValueError:
                logger.warning(f"Could not parse bus/address from {uri}.")

        if bus is not None and address is not None:
            def match_device(d):
                return (d.idVendor == self.XIA_VID and d.idProduct == self.XIA_PID and
                        d.bus == bus and d.address == address)

            self.handle = usb.core.find(custom_match=match_device)
        else:
            self.handle = usb.core.find(idVendor=self.XIA_VID, idProduct=self.XIA_PID)

        if self.handle is None:
            raise ConnectionError(f"Could not find microDXP USB device at {uri}")

        self.handle.set_configuration()

        if self.handle.is_kernel_driver_active(0):
            try:
                self.handle.detach_kernel_driver(0)
                logger.debug("Detached active kernel driver.")
            except usb.core.USBError as e:
                logger.warning(f"Could not detach kernel driver: {e}")

        usb.util.claim_interface(self.handle, 0)
        try:
            self.handle.read(self.EP_DATA_IN, self.USB_SMALL_READ_PAD, timeout=10)
        except usb.core.USBError:
            pass

        logger.info(f"Initialized USB transport on {uri}")

    def _send_usb_setup_packet(self, addr: int, n_bytes: int, rw_flag: int):
        pkt = bytearray(9)
        pkt[0] = addr & 0xFF
        pkt[1] = (addr >> 8) & 0xFF
        pkt[2] = n_bytes & 0xFF
        pkt[3] = (n_bytes >> 8) & 0xFF
        pkt[4] = (n_bytes >> 16) & 0xFF
        pkt[5] = (n_bytes >> 24) & 0xFF
        pkt[6] = rw_flag
        pkt[7] = (addr >> 16) & 0xFF
        pkt[8] = (addr >> 24) & 0xFF

        self.handle.write(self.EP_SETUP_OUT, pkt, timeout=int(self.timeout * 1000))

    def _write_usb_memory(self, addr: int, data: bytes):
        self._send_usb_setup_packet(addr, len(data), self.USB_SETUP_FLAG_WRITE)
        self.handle.write(self.EP_DATA_OUT, data, timeout=int(self.timeout * 1000))

    def read_memory(self, addr: int, num_bytes: int) -> bytes:
        """
        Reads data from hardware memory with 512-byte alignment to prevent
        Overflow (Errno 75) errors.
        """
        # Calculate how many bytes to actually request to keep buffers aligned.
        # Hardware transmits in 512-byte packets; requesting an unaligned
        # amount triggers a Babble/Overflow error in libusb.
        pad = self.USB_SMALL_READ_PAD
        req_bytes = ((num_bytes + pad - 1) // pad) * pad

        self._send_usb_setup_packet(addr, req_bytes, self.USB_SETUP_FLAG_READ)

        try:
            raw_data = self.handle.read(self.EP_DATA_IN, req_bytes,
                                        timeout=int(self.timeout * 1000))
        except usb.core.USBError as e:
            # Note: errno 110 is the standard timeout code
            if e.errno == 110 or "timeout" in str(e).lower():
                logger.warning(
                    f"Timeout on IN endpoint {hex(self.EP_DATA_IN)}. Falling back to 0x88...")
                self.EP_DATA_IN = 0x88
                raw_data = self.handle.read(self.EP_DATA_IN, req_bytes,
                                            timeout=int(self.timeout * 1000))
            else:
                raise

        return bytes(raw_data[:num_bytes])

    def exchange(self, packet: bytes) -> bytes:
        self._write_usb_memory(self.XIA_UART_ADDRESS, packet)
        time.sleep(0.01)

        # 1. Read the initial block
        resp_bytes = self.read_memory(self.XIA_UART_ADDRESS, self.USB_SMALL_READ_PAD)
        if len(resp_bytes) == 0:
            raise ConnectionError("USB timeout: Received 0 bytes (Empty Buffer)")

        if resp_bytes[0:1] != self.ESC:
            err_hex = resp_bytes[:10].hex(' ').upper()
            raise ConnectionError(f"USB framing error: Expected ESC, got: {err_hex}")

        # 2. Inspect the packet header to find the true payload size
        resp_ndata = struct.unpack('<H', resp_bytes[2:4])[0]
        total_len = 1 + 1 + 2 + resp_ndata + 1  # ESC + CMD + NDATA + PAYLOAD + CHK

        # 3. If response is larger than the initial read, re-read the full packet
        if len(resp_bytes) < total_len:
            resp_bytes = self.read_memory(self.XIA_UART_ADDRESS, total_len)

            if len(resp_bytes) < total_len:
                raise ConnectionError(
                    f"USB framing error: Expected {total_len} bytes, received {len(resp_bytes)}")

        return resp_bytes[:total_len]

    def close(self):
        if self.handle:
            usb.util.dispose_resources(self.handle)
            self.handle = None
