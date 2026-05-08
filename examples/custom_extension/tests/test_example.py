""" SPDX-License-Identifier: Apache-2.0 """

import pytest
import struct
from unittest.mock import MagicMock
from extension.commands import CustomCommands


@pytest.fixture
def custom_ext():
    """Provides an isolated CustomCommands instance with a mocked driver."""
    mock_driver = MagicMock()
    return CustomCommands(mock_driver)


class TestCustomConversions:

    def test_explicit_documentation_example(self, custom_ext):
        """
        Test an exact real-world hardware example:
        HV = -800V -> DAC Value = 41942 (0xA3D6)
        """
        # 1. Test Float to Bytes
        dac_bytes = custom_ext._voltage_to_dac_bytes(-800.0)
        assert dac_bytes == b'\xA3\xD6'

        # 2. Test Bytes back to Float
        # Due to 16-bit truncation, 0xA3D6 evaluates to ~ -799.99V
        voltage = custom_ext._dac_bytes_to_voltage(b'\xA3\xD6')
        assert voltage == pytest.approx(-800.0, abs=0.01)

    def test_dac_bytes_to_voltage(self, custom_ext):
        """Test that DAC bytes correctly convert back to physical voltages."""

        # Test 1: Zero-scale (0x0000) should be 0.0 V
        zero_data = struct.pack('>H', 0x0000)
        assert custom_ext._dac_bytes_to_voltage(zero_data) == pytest.approx(0.0)

        # Test 2: Full-scale (0xFFFF) should be Maximum Negative Voltage (~ -1250V)
        # Max Voltage = -610.35 * 65535 * 2.048 / 65535 = -1249.9968 V
        full_data = struct.pack('>H', 0xFFFF)
        assert custom_ext._dac_bytes_to_voltage(full_data) == pytest.approx(-1249.9968)

    def test_voltage_to_dac_bytes(self, custom_ext):
        """Test that physical voltages correctly convert to Big-Endian DAC bytes."""

        # Test 1: 0.0 V should be 0x0000
        assert custom_ext._voltage_to_dac_bytes(0.0) == b'\x00\x00'

        # Test 2: Max Voltage (-1249.9968 V) should be 0xFFFF
        assert custom_ext._voltage_to_dac_bytes(-1249.9968) == b'\xFF\xFF'

    def test_voltage_clamping(self, custom_ext):
        """Ensure that requesting out-of-bounds voltages safely clamps to the DAC limits."""

        # Test 1: Positive voltages (out of bounds since HV_SCALE is negative) -> Clamp to 0x0000
        assert custom_ext._voltage_to_dac_bytes(100.0) == b'\x00\x00'

        # Test 2: Extremely negative voltages -> Clamp to 0xFFFF
        assert custom_ext._voltage_to_dac_bytes(-5000.0) == b'\xFF\xFF'