# microDXP Custom Extension Template

This directory contains a template for building custom, proprietary hardware extensions on top of
the open-source `pymicrodxp` driver.

By using this template, you can securely build and version-control your own proprietary hardware
logic (like custom High Voltage I2C control) in a private repository without needing to fork or
modify the core `pymicrodxp` driver.

## Included Files

* `example_commands.py`: Defines your custom hardware API logic. It demonstrates how to safely use
  the core driver's peripheral I2C methods to send and receive data, including precision-safe
  floating-point math.
* `example_shell.py`: Defines your custom interactive CLI commands. It demonstrates how to
  seamlessly inject your custom commands into the `microdxp>` interactive shell using strict
  Composition to prevent namespace collisions.
* `test_example.py`: A `pytest` test suite that rigorously tests the math and boundary clamping of
  your hardware conversions using a mocked driver.
* `main.py`: The dual-purpose entry point script. It demonstrates how to inherit from the core
  `MicroDXPShell` and dynamically register your custom hardware extensions at runtime for both
  interactive and headless execution.

## Getting Started

1. Copy this template to your own private repository:
   Create a new, private Git repository for your company and copy the contents of this folder into
   it.

2. Install the open-source core driver and testing tools:
   Ensure you have the latest version of the `pymicrodxp` driver installed in your Python
   environment, along with pytest for running the math validations.
   ``` 
   pip install pymicrodxp[shell] pytest
   ```  
3. Validate your math:
   Run the included test suite to verify that the template's voltage-to-DAC conversion math is
   working perfectly on your system.
   ```
   pytest test_example.py -v
   ```
4. Implement your custom logic:
   Rename the example files to match your project. Open the commands file and implement your
   specific register addresses, command bytes, and data conversion math (e.g., converting Volts to
   DAC ticks).

5. Run your customized driver:
   You can run your integration in one of two modes using the `main.py` script.

   Interactive Mode:
   Launches the full interactive shell. Once loaded, type `connect <uri>` (e.g.,
   `connect serial://COM3` or `connect usb://`) to connect to your hardware and auto-load your
   extensions.
   ```
   python main.py
   ```
   Headless Mode:
   Executes the programmatic API sequence defined in `main.py` without launching the shell. All
   diagnostic traces and custom log outputs will be saved to `headless_test.log`.
   ```
   python main.py --headless -u serial://COM3
   ```