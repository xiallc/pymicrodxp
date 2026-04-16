""" SPDX-License-Identifier: Apache-2.0 """

from ..commands.status import StatusCommands as sc
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


class StatusShellMixin:
    """Hardware health and identification commands."""

    @requires_connection
    def do_temp(self, arg):
        """0x41: Read the onboard temperature."""
        temp = self.dxp.status.read_temperature()
        print(f"Board Temperature: {temp} \u00B0C")

    @requires_connection
    def do_par_names(self, arg):
        """0x42: Read DSP parameter names. See `par_names -h` for more information."""
        parser = ShellArgumentParser(prog='par_names', target_func=sc.read_dsp_parameter_names)
        parser.add_argument('readout_option', type=int, nargs='?', default=0, choices=[0, 1])

        args = parser.parse_args(arg.split())
        res = self.dxp.status.read_dsp_parameter_names(args.readout_option)

        print(f"Number of Parameters: {res['num_parameters']}")
        print(f"Total Name String Length: {res['string_len']} bytes")

        if 'names' in res:
            print("Parameter List:")
            for i, name in enumerate(res['names']):
                print(f"  {i:03d}: {name}")

    @requires_connection
    def do_serial(self, arg):
        """0x48: Read the device serial number."""
        sn = self.dxp.status.read_serial_number()
        print(f"Serial Number: {sn}")

    @requires_connection
    def do_info(self, arg):
        """0x49: Read information about the board's configuration."""
        info = self.dxp.status.get_board_information()
        for k, v in info.items():
            print(f"  {k}: {v}")

    @requires_connection
    def do_status(self, arg):
        """0x4B: Read board run and error status."""
        status = self.dxp.status.get_status()
        for k, v in status.items():
            print(f"  {k}: {v}")

    @requires_connection
    def do_reset_fpga(self, arg):
        """0x4E: Reset the FPGA"""
        print("Resetting FPGA...")
        self.dxp.status.reset_fpga()
        print("FPGA reset command sent.")

    @requires_connection
    def do_reset_dsp(self, arg):
        """0x4F: Reset the DSP and FPGA"""
        print("Initiating full processor reset (DSP & FPGA)...")
        self.dxp.status.reset_dsp()
        print("Reset command accepted. Device will reboot.")
