# pymicrodxp

pymicrodxp is a Python-based RS-232 hardware driver and interactive command-line utility for
the XIA microDXP Rev H and J hardware. It provides both a robust API for developers and a
fully-featured interactive shell for hardware testing, diagnostics, and trace visualization.

## Features

* Interactive Hardware Shell: A stateful command-line interface for rapid hardware debugging.
* Diagnostic Trace Capture: Easily capture, log, and visualize 8,000-point diagnostic traces (ADC,
  Filters, Baselines).
* Built-in Visualization: Interactive matplotlib plotting for hardware traces.
* Session Logging: All shell inputs and hardware outputs are automatically piped to an ISO
  8601-timestamped log file with automatic log rotation.
* Cross-Platform: Works on Windows, macOS, and Linux. Includes a tkinter-based file picker for
  seamless data loading.

## Prerequisites

* Python: 3.9 or newer.
* OS-Specific Hardware Permissions (Linux Only): By default, Linux distributions restrict access to
  serial ports. To allow your user to communicate with the microDXP (e.g., via `/dev/ttyUSB0`), you
  must add your user account to the dialout group. Refer to your distribution's documentation on
  using usermod to add a user to the dialout group.
  Note: You must log out and log back in (or restart your computer) for this permission change to
  take effect.

## Installation

If you are using pymicrodxp to interface with the hardware and capture data, set up your environment
as follows:

    # Install core driver
    pip install pymicrodxp

    # Install with interactive shell and plotting
    pip install pymicrodxp[shell]

This will install the library and automatically register the `microdxp` terminal command on your
system.

## Interactive Shell

The easiest way to interact with the board is using the built-in shell. The shell keeps the serial 
port open between commands for extremely fast readouts.

Launch the shell and automatically connect:

    microdxp -u serial://COM3          (Windows Serial)
    microdxp -u serial:///dev/ttyUSB0  (Linux Serial)

**Linux Users**: If you receive a "Permission Denied" error when connecting to hardware:

1. Add your user to the dialout group: `sudo usermod -a -G dialout $USER`
2. Log out and log back in for changes to take effect.

### Shell commands

Once inside the `(microdxp)` shell, you can type `help` to see a full list of commands, or use
`<command> -h` for specific details. The commands are broken down into the following
categories:

* **Session & Connections:** `connect <uri>`, `disconnect`, `view [filename]`, `exit`
* **Status:** `temp`, `serial`, `status`, `info`, `par_names`, `reset_dsp`, `reset_fpga`
* **Diagnostics:** `test [--plot]`, `trace [--plot]`, `histogram [--plot]`, `echo`, `transceive`
* **Run Control:** `start`, `stop`, `mca [--plot]`, `stats`, `preset`, `snapshot`
* **Spectrometer Control:** `tau`, `threshold`, `mca_width`, `mca_bins`, `polarity`, `parset`,
  `genset`, `filter_param`, `dac`, `base_gain`, `swgain`, `gain_trim`, `blfilter_avg_length`
* **Peripherals:** `i2c <read|write> <address> <command_bytes> [-d DATA] [-r READ_LEN]`