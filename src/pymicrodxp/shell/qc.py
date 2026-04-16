""" SPDX-License-Identifier: Apache-2.0 """

import json
from datetime import datetime

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


class QualityControlShellMixin:
    """Commands for hardware validation and performance snapshots."""

    @requires_connection
    def do_test(self, arg):
        """Run full diagnostic test suite. See `test -h` for more information."""
        parser = ShellArgumentParser(prog='test',
                                     description="Capture serial, temperature, status, and "
                                                 "diagnostic data in one snapshot.")
        parser.add_argument('--plot', action='store_true', help="Plot results after capture")

        args = parser.parse_args(arg.split())
        print("\n--- microDXP Quality Control Snapshot ---")

        temp = self.dxp.status.read_temperature()
        status = self.dxp.status.get_status()
        info = self.dxp.status.get_board_information()

        print(f"Serial: {self.dxp.sn} | Temp: {temp} \u00B0C")

        print("\nVerifying 0x1B recovery and raw data handling...")
        test_payload = b"DATA" + bytes([0x1B]) + b"MORE"
        try:
            echo_resp = self.dxp.diagnostic.echo(test_payload)
            if echo_resp == test_payload:
                print("  -> PASSED: Embedded 0x1B handled correctly via length-prefixing.")
            else:
                print(f"  -> FAILED: Data mismatch. Length prefixing may be compromised.")
        except Exception as e:
            print(f"  -> ERROR: Synchronization lost: {e}")

        print("Capturing Diagnostic Trace...")
        trace = self.dxp.diagnostic.read_diagnostic_trace(0, 128, 0, 0)

        print("Capturing Diagnostic Histogram...")
        hist = self.dxp.diagnostic.read_diagnostic_histogram(0)

        output_data = {
            "timestamp": datetime.now().isoformat(),
            "serial_number": self.dxp.sn,
            "temperature_c": temp,
            "status": status,
            "board_information": info,
            "diagnostic_histogram": hist,
            "diagnostic_trace": trace
        }

        filename = f"qc_{self.dxp.sn}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(output_data, f, indent=4)

        print(f"QC Snapshot saved to: {filename}")
        if args.plot:
            self.run_view_data(filename)
