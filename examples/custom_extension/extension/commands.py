""" SPDX-License-Identifier: Apache-2.0 """

import struct
import time


class CustomCommands:
    """Example hardware extension for custom High Voltage I2C control."""

    # These constants are based on a standard AD5693 16-bit DAC with a -610.35V multiplier
    HV_SCALE_V = -610.35
    CTRL_V_RANGE_MAX = 2.048
    AD5693_PRECISION = 0xFFFF  # 65535

    def __init__(self, driver):
        self._driver = driver
        self.log = driver.log

    def _voltage_to_dac_bytes(self, voltage: float) -> bytes:
        """
        Converts a voltage value to DAC bytes.
        Math: DAC = (Voltage * 65535) / (-610.35 * 2.048)
        """
        raw_val = (voltage * self.AD5693_PRECISION) / (self.HV_SCALE_V * self.CTRL_V_RANGE_MAX)

        # 1. Round to 6 decimal places to eliminate floating-point representation noise
        # 2. Use int() to strictly truncate the decimal, matching the hardware documentation
        dac_val = int(round(raw_val, 6))
        dac_val = max(0, min(self.AD5693_PRECISION, dac_val))  # Clamp to 16-bit

        # Explicitly packing as Big-Endian (>H) to match standard I2C byte order
        return struct.pack('>H', dac_val)

    def _dac_bytes_to_voltage(self, data: bytes) -> float:
        """
        Converts DAC bytes back to a voltage value.
        Math: Voltage = -610.35 * DAC * 2.048 / 65535
        """
        dac_val = struct.unpack('>H', data)[0]
        return (dac_val * self.HV_SCALE_V * self.CTRL_V_RANGE_MAX) / self.AD5693_PRECISION

    def write_hv(self, voltage: float) -> float:
        """
        Writes a new High Voltage setpoint via I2C.
        :param voltage: The target voltage in Volts.
        :returns: The voltage that was set.
        """
        payload = self._voltage_to_dac_bytes(voltage)

        # Using the core peripheral API (Address: 0x98, Cmd: 0x10)
        self._driver.peripheral.write_i2c(address=0x98, command_bytes=b'\x10', data=payload)

        self.log.info(f"Custom HV set to {voltage:.2f} V")
        return voltage

    def read_hv(self) -> float:
        """
        Reads the current High Voltage via I2C.
        Performs a dummy read to wake the ADC, waits 1ms, and reads the actual value.
        :returns: The current High Voltage in Volts.
        """
        # 1. Dummy read to wake up the onboard ADC (Address: 0x29, Cmd: 0x00, Len: 2)
        self._driver.peripheral.read_i2c(address=0x29, command_bytes=b'\x00', read_len=2)

        # 2. Wait for the ADC to wake up and sample
        time.sleep(0.01)

        # 3. Perform the actual read
        data = self._driver.peripheral.read_i2c(address=0x29, command_bytes=b'\x00', read_len=2)

        voltage = self._dac_bytes_to_voltage(data)
        self.log.info(f"Custom HV read as {voltage:.2f} V")

        return voltage