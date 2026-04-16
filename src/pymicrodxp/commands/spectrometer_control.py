""" SPDX-License-Identifier: Apache-2.0 """

import math
import struct
from typing import Dict, Any, Union, Optional

from ..core.utils import sec_to_ticks, ticks_to_sec
from ..core.logging import trace_command

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


class SpectrometerControlCommands:
    """Spectrometer Control commands"""

    BLFILTER_BASE = 32768

    def __init__(self, driver):
        self._driver = driver
        self.log = driver.log

    @trace_command(0x82, 'read')
    def read_parameter_set(self) -> int:
        """
        0x82: Get parameter set.
        :return: The current parameter set number from hardware.
        """
        data = self._driver._transceive(0x82, b'\x01')
        self._driver.parset_id = int(data[0])
        return self._driver.parset_id

    @trace_command(0x82, 'write')
    def write_parameter_set(self, num: int) -> int:
        """
        0x82: Set the current peaking time (parameter set).
        :param num: Parameter set number (0-23).
        :returns: The confirmed parameter set number from hardware.
        """
        if num not in range(0, 24):
            raise ValueError(f"invalid parameter set id ({num})")
        payload = struct.pack('<BB', 0, num)
        data = self._driver._transceive(0x82, payload)
        self._driver.parset_id = int(data[0])
        return self._driver.parset_id

    @trace_command(0x83, 'read')
    def read_general_set(self) -> int:
        """
        0x83: Get the current general configuration set.
        :returns: The confirmed general set number from hardware.
        """
        data = self._driver._transceive(0x83, b'\x01')
        self._driver.genset_id = int(data[0])
        return self._driver.genset_id

    @trace_command(0x83, 'write')
    def write_general_set(self, num: int) -> int:
        """
        0x83: Set the current general configuration set.
        :param num: General set number (0-4).
        :returns: The confirmed general set number from hardware.
        """
        if num not in range(0, 5):
            raise ValueError(f'invalid general set id ({num})')
        payload = struct.pack('<BB', 0, num)
        data = self._driver._transceive(0x83, payload)
        self._driver.genset_id = int(data[0])
        return self._driver.genset_id

    @trace_command(0x84, 'read')
    def read_mca_width(self) -> Dict[str, int]:
        """
        0x84: Get MCA bin granularity
        :returns: Dictionary of mode and granularity.
        """
        data = self._driver._transceive(0x84, b'\x01')
        return {"granularity": data[0], "custom_scale": data[1]}

    @trace_command(0x84, 'write')
    def write_mca_width(self, granularity: int, custom_scale: int = 1) -> Dict[str, int]:
        """
        0x84: Set MCA bin granularity
        :param granularity: Set granularity to one of 5 options:
                            0: Very fine (e.g. 5 eV/bin);
                            1: Fine (e.g. 10 eV/bin);
                            2: Medium (e.g. 20 eV/bin);
                            3: Coarse (e.g. 40 eV/bin);
                            4: Custom.
        :param custom_scale: Set custom scale in terms of the minimum bin width. For example, a
                             setting of 7 would give 35 eV/bin.
        :returns: Dictionary of mode and granularity.
        """
        if not (0 <= granularity <= 4):
            raise ValueError(f"invalid granularity {granularity}")
        if granularity == 4 and (custom_scale is None or not (0 <= custom_scale <= 255)):
            raise ValueError(f'invalid custom scale: {custom_scale}')
        payload = struct.pack('<BBB', 0, granularity, custom_scale)
        data = self._driver._transceive(0x84, payload)
        return {"granularity": data[0], "custom_scale": data[1]}

    def _decode_mca_bins(self, data: bytes) -> Dict[str, int]:
        bins, off = struct.unpack('<HH', data[0:4])
        return {"num_bins": int(bins), "offset": int(off)}

    @trace_command(0x85, 'read')
    def read_mca_bins(self) -> Dict[str, int]:
        """
        0x85: Get number of MCA bins and offset.
        :returns: Dictionary of number of bins and offset.
        """
        data = self._driver._transceive(0x85, b'\x01')
        return self._decode_mca_bins(data)

    @trace_command(0x85, 'write')
    def write_mca_bins(self, num_bins: int = 4096, offset: int = 0) -> Dict[str, int]:
        """
        0x85: Set number of MCA bins and offset.
        :param num_bins: Number of bins the MCA uses. Maximum is 8192. Must be less than 4096
                         to take snapshots. Default: 4096.
        :param offset: The first bin of the MCA spectrum as a positive integer less than num_bins.
                       Defaults to 0.
        :returns: Dictionary of number of bins and offset.
        """
        if not (1 <= num_bins <= 8192):
            raise ValueError("invalid number of MCA bins")
        if not (0 <= offset < num_bins):
            raise ValueError("invalid MCA offset, must be less than MCA bins")
        payload = struct.pack('<BHH', 0, num_bins, offset)
        data = self._driver._transceive(0x85, payload)
        return self._decode_mca_bins(data)

    def _decode_thresholds(self, data: bytes) -> Dict[str, int]:
        fast, inter, slow = struct.unpack('<HHH', data[0:6])
        return {
            "fast": int(fast),
            "intermediate": int(inter),
            "slow": int(slow)
        }

    @trace_command(0x86, 'read')
    def read_threshold(self) -> Dict[
        str, int]:
        """
        Command 0x86: Set or Get filter thresholds.
        :returns: Dictionary containing current threshold values for the fast, intermediate, and
                  slow filters.
        """
        data = self._driver._transceive(0x86, b'\x01')
        return self._decode_thresholds(data)

    @trace_command(0x86, 'write')
    def write_threshold(self, filter_choice: int, value: int) -> Dict[str, int]:
        """
        Command 0x86: Set or Get filter thresholds.
        :param filter_choice: 0: Fast, 1: Intermediate, 2: Slow/Energy.
        :param value: Threshold value (0-4095).
        :returns: Dictionary containing current threshold values for the fast, intermediate, and
                  slow filters.
        """
        if filter_choice not in [0, 1, 2]:
            raise ValueError(f"invalid filter choice: {filter_choice}")
        if not (0 <= value <= 0xFFF):
            raise ValueError(f'invalid threshold value: {value}')
        payload = struct.pack('<BBH', 0, filter_choice, value)
        data = self._driver._transceive(0x86, payload)
        return self._decode_thresholds(data)

    @trace_command(0x87)
    def read_polarity(self) -> int:
        """
        0x87: Get detector polarity.
        :returns: The current detector polarity.
        """
        data = self._driver._transceive(0x87, b'\x01')
        return int(data[0])

    @trace_command(0x87, 'write')
    def write_polarity(self, polarity: int) -> int:
        """
        0x87: Set or Get detector polarity.
        :param polarity: 0 = negative-going steps, 1 = positive-going steps
        :returns: The current detector polarity.
        """
        if polarity not in (0, 1):
            raise ValueError("invalid polarity value")
        payload = struct.pack('<BB', 0, polarity)
        data = self._driver._transceive(0x87, payload)
        return int(data[0])

    def _decode_tau(self, data) -> float:
        ticks = struct.unpack('<H', data[0:2])[0]
        return ticks_to_sec(ticks, self._driver.board_info['adc_clk_period_s'])

    @trace_command(0x89, 'read')
    def read_tau(self) -> float:
        """
        0x89: Get preamplifier RC decay time (Tau).
        Note: Applicable to RC feedback preamplifiers only.
        :returns: The current Tau value in seconds.
        """
        data = self._driver._transceive(0x89, b'\x01')
        return self._decode_tau(data)

    @trace_command(0x89, 'write')
    def write_tau(self, tau: float) -> float:
        """
        0x89: Set preamplifier RC decay time (Tau).
        Note: Applicable to RC feedback preamplifiers only.
        :param tau: Decay time in seconds.
        :returns: The current Tau value in seconds.
        """
        ticks = sec_to_ticks(tau, self._driver.board_info['adc_clk_period_s'])

        if not (0 <= ticks <= 0xFFFF):
            raise ValueError("invalid tau value")

        payload = struct.pack('<BH', 0, ticks)
        data = self._driver._transceive(0x89, payload)
        return self._decode_tau(data)

    @trace_command(0x8A, 'read')
    def read_reset_time(self) -> float:
        """
        0x8A: Get the preamplifier reset time.
        :returns: The current reset time in microseconds.
        """
        data = self._driver._transceive(0x8A, b'\x01')
        return int(data[0])

    @trace_command(0x8A, 'write')
    def write_reset_time(self, time_us: int) -> int:
        """
        0x8A: Set the preamplifier reset time.
        :param time_us: Reset time in microseconds (0-255).
        :returns: The current reset time in microseconds.
        """
        if not (0 <= time_us <= 0xFF):
            raise ValueError(f"invalid reset time: {time_us}")
        payload = struct.pack('<BB', 0, time_us)
        data = self._driver._transceive(0x8A, payload)
        return int(data[0])

    def _decode_filter_parameter(self, data) -> Dict[str, int]:
        p_num, val = struct.unpack('<BH', data[0:3])
        return {"param_num": int(p_num), "value": int(val)}

    @trace_command(0x8B, 'read')
    def read_filter_parameter(self, param_num: int) -> Dict[str, int]:
        """
        0x8B: Get filter parameter value.
        :param param_num: Filter parameter number ranging from 0 to 9, with the following meanings:
                          0: SLOWLEN used to calculate INTLEN = SLOWLEN/2^(BFACTOR+1)
                          1: SLOWGAP
                          2: PEAKINT
                          3: PEAKSAM
                          4: FASTLEN
                          5: FASTGAP
                          6: MINWIDTH
                          7: MAXWIDTH
                          8: BFACTOR used to calculate INTLEN = SLOWLEN/2^(BFACTOR+1)
                          9: PEAKMODE where 0 is finding, and 1 is sampling.
        :returns: Dictionary containing the parameter number and value.
        """
        if param_num not in range(10):
            raise ValueError("invalid filter parameter choice")

        payload = struct.pack('<BB', 1, param_num)
        data = self._driver._transceive(0x8B, payload)
        return self._decode_filter_parameter(data)

    @trace_command(0x8B, 'write')
    def write_filter_parameter(self, param_num: int, value: int) -> Dict[str, int]:
        """
        0x8B: Set filter parameter values.
        :param param_num: Filter parameter number ranging from 0 to 9, with the following meanings:
                          0: SLOWLEN used to calculate INTLEN = SLOWLEN/2^(BFACTOR+1);
                          1: SLOWGAP;
                          2: PEAKINT;
                          3: PEAKSAM;
                          4: FASTLEN;
                          5: FASTGAP;
                          6: MINWIDTH;
                          7: MAXWIDTH;
                          8: BFACTOR used to calculate INTLEN = SLOWLEN/2^(BFACTOR+1);
                          9: PEAKMODE where 0 is finding, and 1 is sampling.
        :param value: Filter parameter value.
        :returns: Dictionary containing the parameter number and value.
        """
        if param_num not in range(10):
            raise ValueError("invalid filter parameter choice")
        if not (0 <= value <= 0xFFFF):
            raise ValueError(f"invalid filter parameter value {value}")
        payload = struct.pack('<BBH', 0, param_num, value)
        data = self._driver._transceive(0x8B, payload)
        return self._decode_filter_parameter(data)

    @trace_command(0x8C, 'read')
    def read_parset_values(self, option: int = 1, fippi: int = 0, parset: Optional[int] = None) -> \
            Dict[str, Union[int, float]]:
        """
        0x8C: Read all values for a parameter set.

        Read values in a parameter set (PARSET). The parameter set starts with the parameter
        NUMPARSET and contains the NUMPARSET parameters immediately following NUMPARSET in DSP
        parameter memory. The names of the parameters can be obtained by reading the full list
        of DSP parameter names (command 0x42) and identifying the block starting with NUMPARSET.

        :param option: 0: only returns NUMPARSET,
                       1: return NUMPARSET and all par values from current set (default)
                       2: return all parameters from selected PARSET
        :param fippi: The fippi number that we'll get the parset for. Defaults to 0.
        :param parset: The parameter set to read (0-23). Gets ignored if option is 0 or 1.
                       Defaults to None.
        :returns: Dictionary containing the parameter name and value. If option is 0, the dictionary
                  only contains NUMPARSET. Otherwise, it contains the full
                  list of parameters.
        """
        if option not in range(0, 3):
            raise ValueError(f'invalid option: {option}')
        if not (0 <= fippi <= self._driver.board_info['nfippi']):
            raise ValueError(f'invalid fippi: {fippi}')
        if (parset is None and option == 2) or (parset is not None and parset not in range(0, 24)):
            raise ValueError(f'invalid parset: {parset}')

        payload = struct.pack('<B', option)
        if parset is not None and option == 2:
            payload += struct.pack('<BB', fippi, parset)

        data = self._driver._transceive(0x8C, payload)

        num_in_set = int(data[0])
        if option == 0:
            return {"NUMPARSET": num_in_set}

        parversion = struct.unpack('<H', data[1:3])[0]

        values = struct.unpack(f'<{num_in_set}H', data[3:])

        idx_start = self._driver._pars_by_name['PARVERSION'] + 1
        idx_stop = idx_start + num_in_set
        names = [self._driver._pars_by_idx[i] for i in range(idx_start, idx_stop) if
                 i in self._driver._pars_by_idx]

        result = {"parset_id": self._driver.parset_id, "numparset": num_in_set,
                  "version": parversion}
        result.update(dict(zip(names, values)))

        return result

    @trace_command(0x8D, 'save')
    def save_parameter_set(self, parset_num: int) -> int:
        """
        Command 0x8D: Save the requested parameter set.
        :param parset_num: Parameter set number (0-23).
        :returns: Confirmed parameter set number from hardware.
        """
        if not (0 <= parset_num <= 23):
            raise ValueError("invalid parameter set number")
        payload = struct.pack('<BBB', parset_num, 0x55, 0xAA)
        data = self._driver._transceive(0x8D, payload)
        return int(data[0])

    @trace_command(0x8E, 'read')
    def read_genset_values(self, option: int = 1) -> Dict[str, Union[int, float]]:
        """
        0x8E: Read all values for the current general configuration set.
        :param option: 0: returns only NUMGENSET, 1: returns all parameters.
        :returns: Dictionary with the genset_id, metadata, and mapped parameters.
        """
        payload = struct.pack('<B', option)
        data = self._driver._transceive(0x8E, payload)
        num_in_set = int(data[0])

        if option == 0:
            return {"NUMGENSET": num_in_set}

        gen_version = struct.unpack('<H', data[1:3])[0]
        values = struct.unpack(f'<{num_in_set}H', data[3:])

        idx_start = self._driver._pars_by_name['GENVERSION'] + 1
        idx_stop = idx_start + num_in_set
        names = [self._driver._pars_by_idx[i] for i in range(idx_start, idx_stop) if
                 i in self._driver._pars_by_idx]

        result = {
            "genset_id": self._driver.genset_id,
            "numgenset": num_in_set,
            "version": gen_version
        }
        result.update(dict(zip(names, values)))

        return result

    @trace_command(0x8F, 'save')
    def save_general_set(self, genset_num: int) -> int:
        """
        0x8F: Save the current general set.
        :param genset_num: General set number (0-4).
        :returns: Confirmed general set number from hardware.
        """
        if genset_num not in range(0, 5):
            raise ValueError(f"invalid general set id: {genset_num}")
        payload = struct.pack('<BBB', genset_num, 0x55, 0xAA)
        data = self._driver._transceive(0x8F, payload)
        return int(data[0])

    @trace_command(0x90, 'read')
    def read_slowlen_values(self) -> Dict[str, Any]:
        """
        0x90: Read SLOWLEN values from all 24 parameter sets
        :returns: Dictionary containing the data read back from the hardware.
        """
        data = self._driver._transceive(0x90)
        values = list(struct.unpack('<24H', data[3:51]))
        return {
            "clkset": int(data[0]),
            "nfippi": int(data[1]),
            "decimation": int(data[2]),
            "values": values
        }

    def _decode_gain_trim(self, tweak: int) -> float:
        return tweak / 0x8000

    @trace_command(0x91, 'read')
    def read_gain_trim(self) -> float:
        """
        0x91: Get GAINTWEAK value for current peaking time.
        :returns: The value of GAINTWEAK for the current peaking time.
        """
        data = self._driver._transceive(0x91, b'\x01')
        return self._decode_gain_trim(struct.unpack('<H', data[0:2])[0])

    @trace_command(0x91, 'write')
    def write_gain_trim(self, trim: float) -> float:
        """
        0x91: Set GAINTWEAK value for current peaking time.
        :returns: The value of GAINTWEAK for the current peaking time.
        """
        if not (0.5 <= trim <= 2):
            raise ValueError(f'invalid gain tweak value: {trim}')
        tweak = round(trim * 0x8000, 0)
        payload = struct.pack('<BH', 0, tweak)
        data = self._driver._transceive(0x91, payload)
        return self._decode_gain_trim(struct.unpack('<H', data[0:2])[0])

    def _calc_bl_length(self, data: bytes) -> int:
        return self.BLFILTER_BASE // int(struct.unpack('<H', data[0:2])[0])

    @trace_command(0x92, 'read')
    def read_bl_avg_length(self) -> int:
        """
        0x92: Reads the number of samples averaged together to calculate the BLFILTER.
        :returns: The value of BLFILTER for the current baseline.
        """
        data = self._driver._transceive(0x92, b'\x01')
        return self._calc_bl_length(data)

    @trace_command(0x92, 'write')
    def write_bl_avg_length(self, ave_length: int) -> int:
        """
        0x92: Write the number of samples averaged together to calculate the BLFILTER.
        :param ave_length: The number of samples used to calculate the BLFILTER.
                           Ranges from 1 to 1024 in powers of 2.
        :returns: The value of BLFILTER for the current baseline.
        """
        if ave_length not in {2 ** i for i in range(11)}:
            raise ValueError(f"invalid baseline averaging length: {ave_length}")
        value = struct.pack("<H", self.BLFILTER_BASE // ave_length)
        data = self._driver._transceive(0x92, value)
        return self._calc_bl_length(data)

    @trace_command(0x99, 'read')
    def read_dac_value(self) -> int:
        """
        0x99: Set or Get SlopeDAC (reset) or OffsetDAC (RC) value.
        :returns: The current SlopeDAC/OFFSETDAC value.
        """
        data = self._driver._transceive(0x99, b'\x01')
        return int(struct.unpack('<H', data[0:2])[0])

    @trace_command(0x99, 'write')
    def write_dac_value(self, value: int) -> int:
        """
        0x99: Set or Get SlopeDAC (reset) or OffsetDAC (RC) value.
        :param value: The 16-bit value.
        :returns: The current SlopeDAC/OFFSETDAC value.
        """
        if not (0 <= value <= 0xFFFF):
            raise ValueError(f"invalid SlopeDAC/OFFSETDAC value {value}")
        payload = struct.pack('<BH', 0, value)
        data = self._driver._transceive(0x99, payload)
        return int(struct.unpack('<H', data[0:2])[0])

    @trace_command(0x9B, 'read')
    def read_switched_gain(self) -> int:
        """0x9B: Set or Get 4-bit SWGAIN setting.
        :returns: The 4-bit switched-gain value.
        """
        data = self._driver._transceive(0x9B, b'\x01')
        return int(data[0] & 0x0F)

    @trace_command(0x9B, 'write')
    def write_switched_gain(self, value: int) -> int:
        """0x9B: Set or Get 4-bit SWGAIN setting.
        :param value: The 4-bit switched-gain value to set
        :returns: The 4-bit switched-gain value.
        """
        if not (0 <= value <= 0xF):
            raise ValueError(f'invalid 4-bit SWGAIN value {value}')
        payload = struct.pack('<BB', 0, value & 0x0F)
        data = self._driver._transceive(0x9B, payload)
        return int(data[0] & 0x0F)

    def _calc_digital_base_gain(self, mantissa: int, exponent: int) -> float:
        return (mantissa / 0x8000) * 2 ** exponent

    @trace_command(0x9C, 'read')
    def read_digital_base_gain(self) -> float:
        """
        0x9C: Get Digital Base Gain.
        :returns: The current value of the Digital Base Gain.
        """
        data = self._driver._transceive(0x9C, b'\x01')
        m, e = struct.unpack('<Hb', data[0:3])
        return self._calc_digital_base_gain(m, e)

    @trace_command(0x9C, 'write')
    def write_digital_base_gain(self, gain: float) -> float:
        """
        0x9C: Set Digital Base Gain.
        :param gain: The value the Digital Base Gain will take. Ranges from 0.25 V to 4 V.
        :returns: The current value of the Digital Base Gain.
        """
        GAIN_MIN = 0.25
        GAIN_MAX = 65535 / 32768 * 2

        if not (GAIN_MIN <= gain <= GAIN_MAX):
            raise ValueError(f"invalid Digital Base Gain value {gain}")

        _, exponent = math.frexp(gain)
        exp = max(-2, min(1, exponent - 1))
        base = round(gain / (2 ** exp) * 32768)
        base = max(32768, min(65535, base))

        payload = struct.pack('<BHb', 0, base, exp)
        data = self._driver._transceive(0x9C, payload)
        m, e = struct.unpack('<Hb', data[0:3])

        return self._calc_digital_base_gain(m, e)
