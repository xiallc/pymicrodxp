""" SPDX-License-Identifier: Apache-2.0 """

from datetime import datetime
import json

from ..commands.run_control import RunControlCommands as rcc
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


class RunControlShellMixin:
    """Commands for controlling data acquisition and reading MCA data."""

    @requires_connection
    def _is_hardware_faulty(self) -> bool:
        """
        Blocking pre-readout error check.
        Returns True if a fault exists to block execution.
        """
        status = self.dxp.status.get_status()
        if status.get('dsp_error', False) or status.get('dsp_runerror', False):
            print(f"\n[ABORTED] Hardware Error Detected: {status}")
            return True
        return False

    @requires_connection
    def do_start(self, arg):
        """0x00: Start a data run. See `start -h` for more details."""
        parser = ShellArgumentParser(prog='start', target_func=rcc.start_run)
        parser.add_argument('--clear_mca', action='store_true', default=True)
        args = parser.parse_args(arg.split())
        res = self.dxp.run_control.start_run(args.clear_mca)
        print(f"Run #{res} started.")
        self._update_prompt(1)

    @requires_connection
    def do_stop(self, arg):
        """0x01: Stop the current data run."""
        self.dxp.run_control.end_run()
        print("Run stopped.")
        self._update_prompt(0)

    @requires_connection
    def do_mca(self, arg):
        """0x02 | 0x09: Collects the current MCA histogram or snapshot. See `mca -h` for details."""
        parser = ShellArgumentParser(prog='mca', target_func=rcc.read_mca)
        parser.add_argument('first', type=int, nargs='?', default=0)
        parser.add_argument('num', type=int, nargs='?', default=4096)
        parser.add_argument('bpb', type=int, nargs='?', choices=[1, 2, 3], default=3)
        parser.add_argument('--snapshot', action='store_true')
        parser.add_argument('--plot', action='store_true', help='Plot after capture')
        args = parser.parse_args(arg.split())

        if self._is_hardware_faulty():
            return

        print(f"Reading live MCA ({args.num} bins)...")
        mca = self.dxp.run_control.read_mca(args.first, args.num, args.bpb, args.snapshot)
        print("Readout complete.")

        filename = f"mca_{self.dxp.sn}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump({
                "mca": mca,
                "serial_number": self.dxp.sn,
                "timestamp": datetime.now().isoformat()
            }, f, indent=4)

        print(f"Saved to {filename}")
        if args.plot:
            self.run_view_data(filename)

    @requires_connection
    def do_stats(self, arg):
        """0x06 | 0x0A: Reads run statistics from the hardware. See `stats -h` for details."""
        parser = ShellArgumentParser(prog='stats', target_func=rcc.read_run_statistics)
        parser.add_argument('mode', type=int, nargs='?', default=1, choices=[0, 1],
                            help="0: Standard stats, 1: Include over/underflows")
        parser.add_argument('--snapshot', action='store_true',
                            help="Read snapshot statistics instead of live statistics")
        args = parser.parse_args(arg.split())

        if self._is_hardware_faulty():
            return

        print(f"Reading {'snapshot ' if args.snapshot else ''}run statistics...")
        stats = self.dxp.run_control.read_run_statistics(mode=args.mode, snapshot=args.snapshot)

        print("\n--- Run Statistics ---")
        for k, v in stats.items():
            if 'time' in k:
                print(f"  {k.replace('_', ' ').title()}: {v:.6f} s")
            else:
                print(f"  {k.replace('_', ' ').title()}: {v}")
        print("----------------------\n")

    @requires_connection
    def do_preset(self, arg):
        """0x07: Handles preset run configuration. See `preset -h` for more details."""
        parser = ShellArgumentParser(prog='preset', target_func=rcc.write_run_preset)
        parser.add_argument('preset_type', type=int, nargs='?', choices=[0, 1, 2, 3, 4])
        parser.add_argument('length', type=float, nargs='?')

        args = parser.parse_args(arg.split())
        if args.preset_type is None:
            p = self.dxp.run_control.read_run_preset()
            print(f"Current Preset: Type {p['preset_type']}, Value: {p['length']:.6f}")
        else:
            result = self.dxp.run_control.write_run_preset(args.preset_type, args.length)
            print(f"Preset updated: Type {result['preset_type']}, Value: {result['length']}")

    @requires_connection
    def do_snapshot(self, arg):
        """0x08: Trigger a run snapshot in the hardware. See `snapshot -h` for details."""
        parser = ShellArgumentParser(prog='snapshot', target_func=rcc.take_snapshot)
        parser.add_argument('--clear', action='store_true')
        args = parser.parse_args(arg.split())
        self.dxp.run_control.take_snapshot(clear=args.clear)
