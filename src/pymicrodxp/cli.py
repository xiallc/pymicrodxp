""" SPDX-License-Identifier: Apache-2.0 """

import argparse
import cmd
from datetime import datetime
import logging
import os
import sys
import time

try:
    import readline
except ImportError:
    # Fallback for Windows if pyreadline3 isn't installed
    readline = None

from .driver import MicroDXP

from .shell import (StatusShellMixin, DiagnosticShellMixin, VisualizationShellMixin,
                    QualityControlShellMixin, RunControlShellMixin, SpectrometerControlShellMixin,
                    PeripheralShellMixin)
from .shell.cli_utils import ShellLogger, ShellArgparseExit, format_error_traceback

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


class MicroDXPShell(cmd.Cmd, StatusShellMixin, DiagnosticShellMixin, VisualizationShellMixin,
                    QualityControlShellMixin, RunControlShellMixin, SpectrometerControlShellMixin,
                    PeripheralShellMixin):
    """Interactive command shell for pymicrodxp."""
    intro = "Welcome to the pymicrodxp shell. Type help or ? to list commands.\n"
    prompt = "microdxp:DISCONNECTED> "
    history_file = os.path.expanduser("~/.microdxp_history")

    def _update_prompt(self, run_state: int):
        """Updates the prompt based on the hardware run state."""
        state_str = "RUNNING" if run_state == 1 else "IDLE"
        self.prompt = f"microdxp:{state_str}> "

    def __init__(self, initial_uri=None):
        super().__init__()
        self.dxp = None
        self.initial_uri = initial_uri
        self.default_num_bins = 4096
        self._load_history()

    def _load_history(self):
        """Configures history and fixes Linux up-arrow issues."""
        if os.path.exists(self.history_file):
            readline.read_history_file(self.history_file)

    def emptyline(self):
        """Override default behavior to do nothing on an empty input line."""
        pass

    def onecmd(self, line):
        """Global catch for argparse help menus and usage exits."""
        try:
            return super().onecmd(line)
        except ShellArgparseExit:
            return False

    def precmd(self, line):
        """Log the user's input before executing it."""
        if readline:
            history_len = readline.get_current_history_length()
            if history_len > 0:
                if not line.strip():
                    readline.remove_history_item(history_len - 1)
                elif history_len > 1:
                    prev_item = readline.get_history_item(history_len - 1)
                    if line.strip() == prev_item:
                        readline.remove_history_item(history_len - 1)

        if isinstance(sys.stdout, ShellLogger):
            sys.stdout.log_input(self.prompt, line)
        return line

    def preloop(self):
        """Automatically connect if a port was provided at startup."""
        if self.initial_uri:
            print(f"Auto-connecting to {self.initial_uri}...")
            self.do_connect(self.initial_uri)

            if not self.dxp:
                print("\nAuto-connection failed. You can try again using: connect <port>")

    def postloop(self):
        if readline:
            readline.set_history_length(1000)
            readline.write_history_file(self.history_file)

    def do_help(self, arg):
        """Categorized help display."""
        if arg:
            cmd_func = getattr(self, f"do_{arg}", None)
            if cmd_func and hasattr(cmd_func, "_shell_parser"):
                print()
                cmd_func._shell_parser.print_help()
                return

        super().do_help(arg)

        if not arg and sys.platform.startswith('linux'):
            print("\n--- Linux Serial Access ---")
            print("  If you receive 'Permission Denied', add your user to the dialout group:")
            print(f"  sudo usermod -a -G dialout {os.getenv('USER')}")
            print("  Note: You must log out and back in for changes to take effect.")

    def do_connect(self, arg):
        """
        Connect to the microDXP.
        Usage: connect <uri>
        Example: connect serial://COM3
                 connect serial:///dev/ttyUSB0
                 connect usb://
                 connect usb://2/10
        """
        args = arg.split()
        if not args:
            print("Error: URI is required.")
            return

        uri = args[0]

        if self.dxp:
            print("Closing existing connection...")
            self.dxp.close()

        print(f"Connecting to {uri}...")
        try:
            self.dxp = MicroDXP(uri=uri, log_level=logging.DEBUG, log_file="microdxp_driver.log")
            self._update_prompt(0)
            print("Connected successfully!")
        except Exception as e:
            if "Permission denied" in str(e) and sys.platform.startswith('linux'):
                print("\n[PERMISSION ERROR] Cannot access serial port.")
                print("Run the following command to fix this:")
                print(f"  sudo usermod -a -G dialout {os.getenv('USER')}")
                print("Note: You must log out and back in for changes to take effect.\n")
            else:
                print(format_error_traceback("Failed to connect", e))
            self.dxp = None

    def do_disconnect(self, arg):
        """Disconnect from the microDXP."""
        if self.dxp:
            self.dxp.close()
            self.dxp = None
            print("Disconnected.")
        else:
            print("Not currently connected.")

    def do_quit(self, arg):
        """Exit the shell."""
        if hasattr(self, '_plot_queues'):
            print("Closing visualization windows...")
            for queue in self._plot_queues.values():
                queue.put(None)

            start_wait = time.time()
            while time.time() - start_wait < 2.0:
                if all(not p.is_alive() for p in self._plot_processes.values()):
                    break
                time.sleep(0.1)

        self.do_disconnect("")
        print("Goodbye!")
        return True

    def do_exit(self, arg):
        """Exit the shell."""
        return self.do_quit(arg)

    def do_EOF(self, arg):
        """Exit the shell using Ctrl+D (EOF)."""
        print()
        return self.do_quit(arg)


def main():
    """Main CLI entry point using subparsers."""
    parser = argparse.ArgumentParser(description="MicroDXP Command Line Utility")
    parser.add_argument("-u", "--uri",
                        help="Automatically connect to this URI")

    args = parser.parse_args()

    log_filename = "microdxp_session.log"

    sys.stdout = ShellLogger(log_filename)

    print(f"Session logging initialized: {log_filename}")

    try:
        shell = MicroDXPShell(initial_uri=args.uri)
        shell.cmdloop()
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        if isinstance(sys.stdout, ShellLogger):
            sys.stdout.log_file.close()
            sys.stdout = sys.stdout.terminal


if __name__ == "__main__":
    main()
