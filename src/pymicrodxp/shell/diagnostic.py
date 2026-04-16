""" SPDX-License-Identifier: Apache-2.0 """
from datetime import datetime
import json
import shlex

from ..commands.diagnostic import DiagnosticCommands as dc
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


class DiagnosticShellMixin:
    """Diagnostic readout and echo commands."""

    @requires_connection
    def do_histogram(self, arg):
        """Capture diagnostic histograms. See `histogram -h` for more info."""
        parser = ShellArgumentParser(prog='histogram', target_func=dc.read_diagnostic_histogram)
        parser.add_argument('data_type', type=int, nargs='?', choices=range(0, 6), default=0)
        parser.add_argument('--plot', action='store_true', help="Open plot window after capture.")

        args = parser.parse_args(arg.split())
        print(f"Reading diagnostic histogram (Type: {args.data_type})...")
        hist = self.dxp.diagnostic.read_diagnostic_histogram(args.data_type)

        filename = f"hist_{self.dxp.sn}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump({"timestamp": datetime.now().isoformat(), "histogram": hist}, f)

        print(f"Saved to {filename}")
        if args.plot:
            self.run_view_data(filename)

    @requires_connection
    def do_trace(self, arg):
        """Capture a diagnostic trace. See `trace -h` for more info."""
        parser = ShellArgumentParser(prog='trace', target_func=dc.read_diagnostic_trace)
        parser.add_argument('sampling_interval', type=int, nargs='?', default=0)
        parser.add_argument('trigger_position', type=int, nargs='?', choices=[0, 128, 255],
                            default=128)
        parser.add_argument('trigger_type', type=int, nargs='?',
                            choices=[0, 1, 2, 4, 8, 16, 32, 64, 128], default=0)
        parser.add_argument('trace_type', type=int, nargs='?', choices=range(0, 9), default=0)
        parser.add_argument('--plot', action='store_true', help="Open plot window after capture.")

        args = parser.parse_args(arg.split())
        print(f"Reading trace...")
        trace = self.dxp.diagnostic.read_diagnostic_trace(args.sampling_interval,
                                                          args.trigger_position,
                                                          args.trigger_type,
                                                          args.trace_type)

        filename = f"trace_{self.dxp.sn}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "diagnostic_trace": trace,
                    "sn": self.dxp.sn,
                }, f)

        print(f"Saved to {filename}")
        if args.plot:
            self.run_view_data(filename)

    @requires_connection
    def do_echo(self, arg):
        """
        Send an echo payload to test communications.
        Usage: echo <string>
        """
        payload = arg.encode('ascii') if arg else b'\x01\x02\x03'
        resp = self.dxp.diagnostic.echo(payload)
        print(f"Sent: {payload} | Received: {resp}")

    @requires_connection
    def do_transceive(self, arg):
        """
        Executes a direct call to transceive to allow arbitrary command execution.

        Warning: The transceive function may change without notice. This is for low-level testing
                 and not intended for general use.

        See `transceive -h` for more information.
        """
        parser = ShellArgumentParser(prog='transceive')
        parser.add_argument('command', type=lambda x: int(x, 0), nargs='?', default=0x4A,
                            help="The command to execute in hex format. Ex. 0x40")
        parser.add_argument('data', type=lambda x: bytes.fromhex(x), nargs='?', default=b'',
                            help="A space separated list of bytes to put into the data payload.")

        args = parser.parse_args(shlex.split(arg))
        print(
            f"Executing command: {hex(args.command)} with payload: {args.data.hex(' ').upper()}")
        result = self.dxp.diagnostic.transceive(args.command, args.data)
        print(f"Result: {result.hex(' ').upper()}")
