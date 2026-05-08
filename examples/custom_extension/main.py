""" SPDX-License-Identifier: Apache-2.0 """

import argparse
import logging

from pymicrodxp.driver import MicroDXP
from pymicrodxp.cli import MicroDXPShell

# Import your proprietary hardware logic and CLI commands
from extension import CustomCommands, CustomShellCommands


def run_headless_example(uri: str):
    """
    Demonstrates programmatic, headless control of the hardware using the custom API.
    All outputs (including custom extension logs) are safely routed through the core driver's logger.
    """
    if not uri:
        print("Error: Headless mode requires a URI (-u).")
        return

    print(f"\nConnecting to {uri} in headless mode...")

    try:
        # 1. Initialize the driver. DEBUG will produce HUGE logs for data runs. This is only for
        #    debugging. Omit this to generate no log, or drop it to INFO for more reasonable logs.
        driver = MicroDXP(uri, log_level=logging.DEBUG, log_file="headless_test.log")

        # 2. Register the programmatic extension
        driver.register_extension("custom", CustomCommands)
        print("\n--- Running Headless API Sequence ---")

        # 3. The custom extension inherits the driver's context-aware logger!
        driver.custom.log.info("Starting automated HV sequence.")

        # 4. Execute the custom hardware logic
        driver.custom.write_hv(-800.0)
        voltage = driver.custom.read_hv()

        print(f"\nSequence Complete. Final Readout: {voltage:.2f} V")
        print("Check 'headless_test.log' to see the combined core and custom hardware traces.")

    except Exception as e:
        print(f"\n[Connection Error] {e}")
    finally:
        if 'driver' in locals() and driver:
            driver.close()


def run_interactive_shell(uri: str = None):
    """
    Demonstrates interactive control by injecting the custom hardware commands
    directly into the microdxp> CLI prompt.
    """
    shell = MicroDXPShell(initial_uri=uri)

    # 1. Register CLI commands immediately so they ALWAYS appear in the `help` menu!
    shell.register_commands(CustomShellCommands(shell))

    print("\nWelcome to the Custom Extension Shell!")
    print("Type `connect <uri>` to begin. Extensions will load automatically.")

    # 2. Save a reference to the core connect command
    original_connect = shell.do_connect

    def auto_load_connect(arg):
        # Let the core shell do the heavy lifting
        original_connect(arg)

        # 3. If the connection was successful, automatically load the API extension
        if shell.dxp:
            shell.dxp.register_extension("custom", CustomCommands)
            print("Custom extensions automatically loaded! Type `help` to see new commands.")

    # 4. RESTORE THE DOCSTRING!
    # This guarantees 'connect' stays in the Documented Commands list
    auto_load_connect.__doc__ = original_connect.__doc__

    # 5. Override the shell's connect command with our hooked version
    shell.do_connect = auto_load_connect

    # 6. Start the interactive loop
    shell.cmdloop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Custom Hardware Control Example")
    parser.add_argument('--headless', action='store_true',
                        help="Run the programmatic API sequence instead of the interactive shell.")
    parser.add_argument('-u', '--uri', type=str, default="serial://COM3",
                        help="The hardware URI to connect to (Used in headless mode).")

    args = parser.parse_args()

    if args.headless:
        run_headless_example(args.uri)
    else:
        run_interactive_shell(args.uri)
