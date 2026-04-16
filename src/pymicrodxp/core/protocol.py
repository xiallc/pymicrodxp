""" SPDX-License-Identifier: Apache-2.0 """

import struct
from typing import Dict, Union

from ..core.logging import MergingAdapter
from .error import MicroDXPError
from .logging import logger
from .registry import COMMAND_REGISTRY
from .transport import USBTransport, SerialTransport
from .utils import calculate_checksum

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


class MicroDXPBase:
    """The base class for the microDXP object."""
    ESC = b'\x1B'
    STAT_CLK_PERIOD_S = 500e-9
    PRESET_CLK_PERIOD_S = 500e-9

    def __init__(self, uri: str, timeout: float = 2.0) -> None:
        self.board_info: Dict[str, Union[int, float, str]] = {}
        self.sn: str = "Unknown"
        self.log: MergingAdapter = MergingAdapter(logger, {"sn": self.sn})

        if uri.startswith("usb://"):
            raise NotImplementedError("USB transport is not supported.")
            self.transport = USBTransport(uri, timeout)
        elif uri.startswith("serial://"):
            self.transport = SerialTransport(uri, timeout)
            self._auto_baud()
        else:
            raise ValueError(f"Unsupported URI scheme. Use 'serial://' or 'usb://'. Got: {uri}")

        self.use_usb = self.transport.use_usb

    def _auto_baud(self):
        """Negotiates baud rate using 0x4A and a payload of PING."""
        baud_rates = [115200, 57600, 230400, 460800, 921600]
        ping_payload = b"PING"
        cmd_byte = 0x4A  # ECHO

        ndata = struct.pack('<H', len(ping_payload))
        ping_body = bytes([cmd_byte]) + ndata + ping_payload
        ping_packet = self.ESC + ping_body + bytes([calculate_checksum(ping_body)])

        original_timeout = self.transport.timeout
        self.transport.timeout = 0.2
        self.transport.handle.timeout = 0.2

        connected = False
        for baud in baud_rates:
            self.transport.set_baudrate(baud)
            try:
                resp_packet = self.transport.exchange(ping_packet)
                if resp_packet[1] == cmd_byte:
                    connected = True
                    break
            except (ConnectionError, ValueError, struct.error):
                continue

        self.transport.timeout = original_timeout
        self.transport.handle.timeout = original_timeout

        if not connected:
            raise ConnectionError(f"Failed to auto-baud connect to {self.transport.port}")

    def close(self) -> None:
        self.transport.close()

    def read_usb_memory(self, addr: int, num_bytes: int) -> bytes:
        """
        Public high-speed DMA memory read over USB.
        Used by command handlers for MCA and Traces.
        """
        return self.transport.read_memory(addr, num_bytes)

    def _transceive(self, cmd_byte: int, data: bytes = b'') -> bytes:
        """
        Sends and Receives commands according to the RS-232 3.40 command specification for the
        microDXP Revision H and J.

        The general command structure is
        ```
        [Esc][Command][Ndata (2 bytes)][data1]…[dataN][XOR CS]
        ```
        `[Esc]` is 0x1B and defines the command start byte.
        `[Command]` is one of the defined commands from the command specification.
        `[Ndata]` is a 2-byte little endian value defining the payload size.
        `[XOR CS]` is a bitwise XOR checksum of all command bytes excluding `[Esc]`.

        The response structure is identical to the command. With the first payload byte always
        being the command's return status. In the event of an error the payload only contains the
        error code.

        :param cmd_byte: The command byte that we'll execute the call with.
        :param data: The data to be sent with the command.
        :returns: A bytes array containing the response payload without the status code.
        """
        cmd_name = COMMAND_REGISTRY.get(cmd_byte, "Unknown").get('name', "Unknown")
        ndata = len(data)
        ndata_bytes = struct.pack('<H', ndata)
        payload = bytes([cmd_byte]) + ndata_bytes + data
        checksum = calculate_checksum(payload)
        packet = self.ESC + payload + bytes([checksum])

        transport_type = "USB" if self.use_usb else "Serial"
        self.log.debug(f"TX 0x{cmd_byte:02X} ({cmd_name})",
                       extra={"context": {"packet": packet.hex(' ').upper(),
                                          'transport': transport_type}})

        resp_packet = self.transport.exchange(packet)

        resp_cmd = resp_packet[1]
        if resp_cmd != cmd_byte:
            raise ValueError(
                f"Command mismatch: Sent {hex(cmd_byte)}, received {hex(resp_cmd)}")

        resp_ndata = struct.unpack('<H', resp_packet[2:4])[0]
        resp_data = resp_packet[4:4 + resp_ndata]
        resp_checksum = resp_packet[-1]

        expected_checksum = calculate_checksum(bytes([resp_cmd]) + resp_packet[2:4] + resp_data)
        if resp_checksum != expected_checksum:
            raise ValueError(
                f"Checksum mismatch: Expected {hex(expected_checksum)}, got {hex(resp_checksum)}")

        rx_packet = self.ESC + bytes([resp_cmd]) + resp_packet[2:4] + resp_data + bytes(
            [resp_checksum])
        self.log.debug(f"RX 0x{cmd_byte:02X} ({cmd_name})",
                       extra={"context": {"packet": rx_packet.hex(' ').upper(),
                                          "transport": transport_type}})

        if cmd_name == 'ECHO':
            return resp_data

        err_code = resp_data[0]
        if err_code != 0:
            raise MicroDXPError(cmd_byte, err_code)

        return resp_data[1:]
