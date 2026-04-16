""" SPDX-License-Identifier: Apache-2.0 """

import shlex

from ..commands.peripheral import PeripheralCommands as pc
from .cli_utils import requires_connection, ShellArgumentParser

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


class PeripheralShellMixin:
    """Commands for controlling peripheral devices via various protocols."""

    @requires_connection
    def do_i2c(self, arg):
        """I2C Transaction. See `i2c -h` for more information."""
        parser = ShellArgumentParser(prog='i2c', target_funcs=[pc.write_i2c, pc.read_i2c])
        parser.add_argument('mode', choices=['read', 'write'])
        parser.add_argument('address', type=lambda x: int(x, 0))
        parser.add_argument('command_bytes', type=lambda x: bytes.fromhex(x))
        parser.add_argument('-d', '--data', type=lambda x: bytes.fromhex(x))
        parser.add_argument('-r', '--read_len', type=int)

        args = parser.parse_args(shlex.split(arg))
        if args.mode == 'read':
            if args.read_len is None:
                parser.error("The 'read_len' option is required.")
            res = self.dxp.peripheral.read_i2c(args.address, args.command_bytes, args.read_len)
            print(f"I2C Read from 0x{args.address:02X}: {res.hex(' ').upper()}")
        else:
            if not args.data:
                parser.error("The 'data' argument is required.")
            self.dxp.peripheral.write_i2c(args.address, args.command_bytes, args.data)
            print(f"I2C Write to 0x{args.address:02X} successful.")
