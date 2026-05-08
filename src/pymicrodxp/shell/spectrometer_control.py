""" SPDX-License-Identifier: Apache-2.0 """

import json

from ..commands.spectrometer_control import SpectrometerControlCommands as scc
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


class SpectrometerControlShell:
    """Commands for spectrometer configuration."""

    def __init__(self, shell):
        self.shell = shell

    @property
    def dxp(self):
        return self.shell.dxp

    @requires_connection
    def do_parset(self, arg):
        """0x82: Set or query the current parameter set. See `parset -h` for more info."""
        parser = ShellArgumentParser(prog='parset')
        parser.add_argument('num', type=int, nargs='?', choices=range(24))

        args = parser.parse_args(arg.split())
        if args.num is not None:
            val = self.dxp.spectrometer.write_parameter_set(args.num)
        else:
            val = self.dxp.spectrometer.read_parameter_set()
        print(f"Parameter Set: {val}")

    @requires_connection
    def do_genset(self, arg):
        """0x83: Set or query the current general set. See `genset -h` for more info."""
        parser = ShellArgumentParser(prog='genset', target_func=scc.write_general_set)
        parser.add_argument('num', type=int, nargs='?', choices=range(5))

        args = parser.parse_args(arg.split())
        if args.num is not None:
            val = self.dxp.spectrometer.write_general_set(args.num)
        else:
            val = self.dxp.spectrometer.read_general_set()
        print(f"General Set: {val}")

    @requires_connection
    def do_mca_width(self, arg):
        """0x84: Set or query MCA bin granularity. See `mca_width -h` for more info."""
        parser = ShellArgumentParser(prog='mca_width')
        parser.add_argument('granularity', type=int, nargs='?')
        parser.add_argument('custom_scale', type=int, nargs='?', default=1)

        labels = {
            0: "0: Very Fine (e.g. 5 eV/bin)",
            1: "1: Fine (e.g. 10 eV/bin)",
            2: "2: Medium (e.g. 20 eV/bin)",
            3: "3: Coarse (e.g. 40 eV/bin)",
            4: "4: Custom"
        }

        args = parser.parse_args(arg.split())
        if args.granularity is None:
            res = self.dxp.spectrometer.read_mca_width()
            label = labels.get(res['granularity'], "Unknown")
            print(f"Current Granularity: {label}")
            print(
                f"Custom Scale: {res['custom_scale']} (Width in terms of Very Fine bin width)")
        else:
            res = self.dxp.spectrometer.write_mca_width(args.granularity,
                                                        args.custom_scale)
            label = labels.get(res['granularity'], "Unknown")
            print(f"Set Granularity: {label}")
            print(f"Custom Scale: {res['custom_scale']}")

    @requires_connection
    def do_mca_bins(self, arg):
        """0x85: Set or query MCA bin count/offset. See `mca_bins -h` for more info."""
        parser = ShellArgumentParser(prog='mca_bins', target_func=scc.write_mca_bins)
        parser.add_argument('num_bins', type=int, nargs='?')
        parser.add_argument('offset', type=int, nargs='?')

        args = parser.parse_args(arg.split())
        if args.num_bins is None:
            res = self.dxp.spectrometer.read_mca_bins()
            print(f"Current: {res['num_bins']} bins, Offset: {res['offset']}")
            self.default_num_bins = res['num_bins']
        else:
            current = self.dxp.spectrometer.read_mca_bins()
            offset = args.offset if args.offset is not None else current['offset']
            res = self.dxp.spectrometer.write_mca_bins(args.num_bins, offset)
            self.default_num_bins = res['num_bins']
            print(f"Set: {res['num_bins']} bins, Offset: {res['offset']}")

    @requires_connection
    def do_threshold(self, arg):
        """0x86: Read/Write filter thresholds. See `threshold -h` for more info."""
        parser = ShellArgumentParser(prog='threshold', target_func=scc.write_threshold)
        parser.add_argument('filter_choice', type=int, nargs='?', choices=[0, 1, 2])
        parser.add_argument('value', type=int, nargs='?')

        args = parser.parse_args(arg.split())
        if args.value is not None:
            res = self.dxp.spectrometer.write_threshold(args.filter_choice, args.value)
        elif args.filter_choice is not None:
            parser.error("A threshold value is required to set a threshold.")
        else:
            res = self.dxp.spectrometer.read_threshold()

        print(f"'Current Thresholds:")
        print(f"  Fast (0):         {res['fast']}")
        print(f"  Intermediate (1): {res['intermediate']}")
        print(f"  Slow/Energy (2):  {res['slow']}")

    @requires_connection
    def do_polarity(self, arg):
        """0x87: Read/Write signal polarity. See `polarity -h` for more info."""
        parser = ShellArgumentParser(prog='polarity', target_func=scc.write_polarity)
        parser.add_argument('polarity', type=int, nargs='?', choices=[0, 1])

        args = parser.parse_args(arg.split())
        if args.polarity is None:
            val = self.dxp.spectrometer.read_polarity()
            mode = "Positive" if val == 1 else "Negative"
            print(f"Current Polarity: {val} ({mode}-going steps)")
        else:
            val = self.dxp.spectrometer.write_polarity(args.polarity)
            mode = "Positive" if val == 1 else "Negative"
            print(f"Set Polarity to: {val} ({mode}-going steps)")

    @requires_connection
    def do_tau(self, arg):
        """0x89: Read/Write the RC time constant (Tau). See `tau -h` for more info."""
        parser = ShellArgumentParser(prog='tau', target_func=scc.write_tau)
        parser.add_argument('tau', type=float, nargs='?')
        args = parser.parse_args(arg.split())
        if args.tau is not None:
            val = self.dxp.spectrometer.write_tau(args.tau)
        else:
            val = self.dxp.spectrometer.read_tau()

        print(f"Tau: {val:.3e} s")

    @requires_connection
    def do_reset_time(self, arg):
        """0x8A: Read/Write the preamplifier reset time. See `reset-time -h` for more info."""
        parser = ShellArgumentParser(prog='reset_time', target_func=scc.write_reset_time)
        parser.add_argument('time_us', type=int, nargs='?')
        args = parser.parse_args(arg.split())
        if args.time_us is not None:
            val = self.dxp.spectrometer.write_reset_time(args.time_us)
        else:
            val = self.dxp.spectrometer.read_reset_time()
        print(f"Reset Time: {val} \u00B5s")

    @requires_connection
    def do_filter_param(self, arg):
        """0x8B: Read/Write filter parameters. See `filter_param -h` for more info."""
        parser = ShellArgumentParser(prog='filter_param', target_func=scc.write_filter_parameter)
        parser.add_argument('param_num', type=int)
        parser.add_argument('value', type=int, nargs='?')
        args = parser.parse_args(arg.split())
        if args.value is not None:
            res = self.dxp.spectrometer.write_filter_parameter(args.param_num, args.value)
        else:
            res = self.dxp.spectrometer.read_filter_parameter(args.param_num)
        print(
            f"Param {res['param_num']}: {res['value']}")

    @requires_connection
    def do_read_parset(self, arg):
        """0x8C: Read all values for a parameter set. See `read_parset -h` for more info."""
        parser = ShellArgumentParser(prog='read_parset', target_func=scc.read_parset_values)
        parser.add_argument('option', type=int, nargs='?', choices=range(3), default=1)
        parser.add_argument('fippi', type=int, nargs='?', default=0)
        parser.add_argument('parset', type=int, nargs='?', choices=range(24), default=0)
        args = parser.parse_args(arg.split())
        res = self.dxp.spectrometer.read_parset_values(args.option, args.fippi, args.parset)
        print(json.dumps(res))

    @requires_connection
    def do_save_parset(self, arg):
        """0x8D: Save the requested parameter set. See `save_parset -h` for more info."""
        parser = ShellArgumentParser(prog='save_parset', target_func=scc.save_parameter_set)
        parser.add_argument('parset_num', type=int)
        args = parser.parse_args(arg.split())
        res = self.dxp.spectrometer.save_parameter_set(args.parset_num)
        print(f"Successfully saved Parameter Set {res}.")

    @requires_connection
    def do_read_genset(self, arg):
        """0x8E: Read all values for the current general configuration set."""
        parser = ShellArgumentParser(prog='read_genset', target_func=scc.read_genset_values)
        parser.add_argument('option', type=int, nargs='?', choices=[0, 1], default=1)
        args = parser.parse_args(arg.split())
        res = self.dxp.spectrometer.read_genset_values(args.option)
        print(json.dumps(res))

    @requires_connection
    def do_save_genset(self, arg):
        """0x8F: Save the current general set. See `save_genset -h` for more info."""
        parser = ShellArgumentParser(prog='save_genset', target_func=scc.save_general_set)
        parser.add_argument('genset_num', type=int, choices=range(5))
        args = parser.parse_args(arg.split())
        res = self.dxp.spectrometer.save_general_set(args.genset_num)
        print(f"Successfully saved General Set {res}.")

    @requires_connection
    def do_slowlen(self, arg):
        """0x90: Read SLOWLEN values from all parameter sets."""
        res = self.dxp.spectrometer.read_slowlen_values()
        print(f"CLKSET: {res['clkset']} | Decimation: {res['decimation']}")
        for i, val in enumerate(res['values']):
            print(f"  PARSET {i:02d}: {val} ticks")

    @requires_connection
    def do_gain_trim(self, arg):
        """0x91: Read/Write GAINTWEAK. See `gain_trim -h` for more info."""
        parser = ShellArgumentParser(prog='gain_trim', target_func=scc.write_gain_trim)
        parser.add_argument('trim', type=float, nargs='?')
        args = parser.parse_args(arg.split())
        if args.trim is not None:
            val = self.dxp.spectrometer.write_gain_trim(args.trim)
        else:
            val = self.dxp.spectrometer.read_gain_trim()
        print(f"Gain Tweak: {val}")

    @requires_connection
    def do_bl_avg_length(self, arg):
        """0x92: Read/Write baseline averaging value. See `bl_avg_length -h` for more information."""
        parser = ShellArgumentParser(prog='blfilter_avg_length',
                                     target_func=scc.write_bl_avg_length)
        parser.add_argument('ave_length', type=int, nargs='?')
        args = parser.parse_args(arg.split())
        if args.ave_length is not None:
            val = self.dxp.spectrometer.write_bl_avg_length(args.ave_length)
        else:
            val = self.dxp.spectrometer.read_bl_avg_length()
        print(f"BL_AVE_LENGTH: {val}")

    @requires_connection
    def do_dac(self, arg):
        """0x99: Set or query Slope/Offset DAC. See `dac -h` for more info."""
        parser = ShellArgumentParser(prog='dac', target_func=scc.write_dac_value)
        parser.add_argument('value', type=int, nargs='?')
        args = parser.parse_args(arg.split())
        if args.value is not None:
            val = self.dxp.spectrometer.write_dac_value(args.value)
        else:
            val = self.dxp.spectrometer.read_dac_value()
        print(f"DAC Value: {val}")

    @requires_connection
    def do_swgain(self, arg):
        """0x9B: Read/Write Switched-Gain. See `swgain -h` for more info."""
        parser = ShellArgumentParser(prog='swgain', target_func=scc.write_switched_gain)
        parser.add_argument('value', type=int, nargs='?')
        args = parser.parse_args(arg.split())
        if args.value is not None:
            val = self.dxp.spectrometer.write_switched_gain(args.value)
        else:
            val = self.dxp.spectrometer.read_switched_gain()
        print(f"Switched Gain: {val}")

    @requires_connection
    def do_base_gain(self, arg):
        """0x9C: Read/Write Digital Base Gain. See `base-gain -h` for more info."""
        parser = ShellArgumentParser(prog='base_gain', target_func=scc.write_digital_base_gain)
        parser.add_argument('gain', type=float, nargs='?')
        args = parser.parse_args(arg.split())
        if args.gain is not None:
            res = self.dxp.spectrometer.write_digital_base_gain(args.gain)
        else:
            res = self.dxp.spectrometer.read_digital_base_gain()
        print(f"Base Gain: {res}")
