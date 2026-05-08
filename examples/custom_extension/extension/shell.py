""" SPDX-License-Identifier: Apache-2.0 """

from pymicrodxp.shell.cli_utils import requires_connection, ShellArgumentParser
from example_commands import CustomCommands

class CustomShellCommands:
    """Example interactive shell commands for custom hardware."""

    def __init__(self, shell):
        self.shell = shell

    @property
    def dxp(self):
        """Dynamically fetch the active driver instance from the main shell."""
        return self.shell.dxp

    @requires_connection
    def do_read_hv(self, arg):
        """Read the Custom High Voltage module. See `read_hv -h` for more info."""
        parser = ShellArgumentParser(prog='read_hv', target_func=CustomCommands.read_hv)
        parser.parse_args(arg.split())

        # Executing the command from the dynamically attached namespace
        voltage = self.dxp.custom.read_hv()
        print(f"Current High Voltage: {voltage:.2f} V")

    @requires_connection
    def do_write_hv(self, arg):
        """Write a new High Voltage setpoint. See `write_hv -h` for more info."""
        parser = ShellArgumentParser(prog='write_hv', target_func=CustomCommands.write_hv)
        parser.add_argument('voltage', type=float, help="The target voltage in Volts.")
        args = parser.parse_args(arg.split())

        voltage = self.dxp.custom.write_hv(args.voltage)
        print(f"Successfully set High Voltage to {voltage:.2f} V")