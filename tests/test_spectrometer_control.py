""" SPDX-License-Identifier: Apache-2.0 """

import struct
import pytest
from pymicrodxp.core.error import MicroDXPError
from .test_base import TestBase

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


class TestSpectrometerControl(TestBase):

    @pytest.mark.parametrize("num", [-1, 24])
    def test_write_parameter_set_validation(self, num):
        with pytest.raises(ValueError, match="invalid parameter set id"):
            self.dxp.spectrometer.write_parameter_set(num)

    @pytest.mark.parametrize("num", [-1, 5])
    def test_write_general_set_validation(self, num):
        with pytest.raises(ValueError, match="invalid general set id"):
            self.dxp.spectrometer.write_general_set(num)

    @pytest.mark.parametrize("gran, custom", [(5, None), (4, 256)])
    def test_write_mca_width_validation(self, gran, custom):
        with pytest.raises(ValueError):
            self.dxp.spectrometer.write_mca_width(granularity=gran, custom_scale=custom)

    @pytest.mark.parametrize("bins, offset, msg", [
        (8193, 0, "invalid number of MCA bins"),
        (4096, 4097, "invalid MCA offset")
    ])
    def test_write_mca_bins_validation(self, bins, offset, msg):
        with pytest.raises(ValueError, match=msg):
            self.dxp.spectrometer.write_mca_bins(bins, offset)

    @pytest.mark.parametrize("choice, value, msg", [
        (3, 0, "invalid filter choice"),
        (0, 4096, "invalid threshold value")
    ])
    def test_write_threshold_validation(self, choice, value, msg):
        with pytest.raises(ValueError, match=msg):
            self.dxp.spectrometer.write_threshold(choice, value)

    def test_write_polarity_validation(self):
        with pytest.raises(ValueError, match="invalid polarity value"):
            self.dxp.spectrometer.write_polarity(2)

    def test_write_tau_validation(self):
        with pytest.raises(ValueError, match="invalid tau value"):
            self.dxp.spectrometer.write_tau(10.0)

    def test_write_reset_time_validation(self):
        with pytest.raises(ValueError, match="invalid reset time"):
            self.dxp.spectrometer.write_reset_time(256)

    @pytest.mark.parametrize("num", [None, 10])
    def test_read_filter_parameter_validation(self, num):
        with pytest.raises(ValueError, match="invalid filter parameter choice"):
            self.dxp.spectrometer.read_filter_parameter(num)

    @pytest.mark.parametrize("num, value, msg", [
        (10, 0, "invalid filter parameter choice"),
        (0, 0x10000, "invalid filter parameter value")
    ])
    def test_write_filter_parameter_validation(self, num, value, msg):
        with pytest.raises(ValueError, match=msg):
            self.dxp.spectrometer.write_filter_parameter(num, value)

    @pytest.mark.parametrize("opt, fip, par, msg", [
        (3, 0, 0, "invalid option"),
        (2, 99, 0, "invalid fippi"),
        (2, 0, 24, "invalid parset")
    ])
    def test_read_parset_values_validation(self, opt, fip, par, msg):
        with pytest.raises(ValueError, match=msg):
            self.dxp.spectrometer.read_parset_values(option=opt, fippi=fip, parset=par)

    def test_save_parameter_set_validation(self):
        with pytest.raises(ValueError, match="invalid parameter set number"):
            self.dxp.spectrometer.save_parameter_set(24)

    def test_save_general_set_validation(self):
        with pytest.raises(ValueError, match="invalid general set id"):
            self.dxp.spectrometer.save_general_set(5)

    @pytest.mark.parametrize("trim", [0.4, 2.1])
    def test_write_gain_trim_validation(self, trim):
        with pytest.raises(ValueError, match="invalid gain tweak value"):
            self.dxp.spectrometer.write_gain_trim(trim)

    @pytest.mark.parametrize("value", [-1, 11, 1000])
    def test_write_bl_avg_length_validation(self, value):
        with pytest.raises(ValueError, match="invalid baseline averaging length"):
            self.dxp.spectrometer.write_bl_avg_length(value)

    def test_read_bl_avg_length(self):
        self.setup_response(struct.pack('<H', 32))
        res = self.dxp.spectrometer.read_bl_avg_length()
        assert res == 1024
        self.dxp._transceive.assert_called_with(0x92, b'\x01')

    @pytest.mark.parametrize("ave_length, expected_hw_val", [
        (1, 32768),
        (2, 16384),
        (16, 2048),
        (1024, 32)
    ])
    def test_write_bl_avg_length(self, ave_length, expected_hw_val):
        self.setup_response(struct.pack('<H', expected_hw_val))
        res = self.dxp.spectrometer.write_bl_avg_length(ave_length)
        assert res == ave_length
        expected_payload = struct.pack('<H', expected_hw_val)
        self.dxp._transceive.assert_called_with(0x92, expected_payload)

    @pytest.mark.parametrize("value", [-1, 0x30000])
    def test_write_dac_value_validation(self, value):
        with pytest.raises(ValueError, match="invalid SlopeDAC/OFFSETDAC value"):
            self.dxp.spectrometer.write_dac_value(value)

    @pytest.mark.parametrize("value", [-1, 0x10])
    def test_write_switched_gain_validation(self, value):
        with pytest.raises(ValueError, match="invalid 4-bit SWGAIN value"):
            self.dxp.spectrometer.write_switched_gain(value)

    @pytest.mark.parametrize("gain", [0.1, 4.0])
    def test_write_digital_base_gain_validation(self, gain):
        with pytest.raises(ValueError, match="invalid Digital Base Gain value"):
            self.dxp.spectrometer.write_digital_base_gain(gain)

    @pytest.mark.parametrize("num", [-1, 24])
    def test_write_parameter_set_validation(self, num):
        with pytest.raises(ValueError, match="invalid parameter set id"):
            self.dxp.spectrometer.write_parameter_set(num)

    @pytest.mark.parametrize("gran, custom", [
        (-1, None), (5, None), (4, -1), (4, 256)
    ])
    def test_write_mca_width_validation(self, gran, custom):
        with pytest.raises(ValueError):
            self.dxp.spectrometer.write_mca_width(granularity=gran, custom_scale=custom)

    @pytest.mark.parametrize("bins, offset, msg", [
        (-1, 0, "invalid number of MCA bins"),
        (0, 0, "invalid number of MCA bins"),
        (8193, 0, "invalid number of MCA bins"),
        (4096, -1, "invalid MCA offset"),
        (4096, 4096, "invalid MCA offset"),
    ])
    def test_write_mca_bins_validation(self, bins, offset, msg):
        with pytest.raises(ValueError, match=msg):
            self.dxp.spectrometer.write_mca_bins(bins, offset)

    def test_write_tau_validation(self):
        with pytest.raises(ValueError, match="invalid tau value"):
            self.dxp.spectrometer.write_tau(-1.0)

    @pytest.mark.parametrize("opt, fip, par, msg", [
        (-1, 0, 0, "invalid option"),
        (3, 0, 0, "invalid option"),
        (2, -1, 0, "invalid fippi"),
        (2, 99, 0, "invalid fippi"),
        (2, 0, -1, "invalid parset"),
        (2, 0, 24, "invalid parset")
    ])
    def test_read_parset_values_validation(self, opt, fip, par, msg):
        with pytest.raises(ValueError, match=msg):
            self.dxp.spectrometer.read_parset_values(option=opt, fippi=fip, parset=par)

    @pytest.mark.parametrize("num", [-1, 24])
    def test_save_parameter_set_validation(self, num):
        with pytest.raises(ValueError, match="invalid parameter set number"):
            self.dxp.spectrometer.save_parameter_set(num)

    # --- SUCCESS TESTS ---

    def test_get_parameter_set(self):
        self.setup_response(b'\x0c')
        assert self.dxp.spectrometer.read_parameter_set() == 12
        self.dxp._transceive.assert_called_with(0x82, b'\x01')

    def test_set_parameter_set(self):
        self.setup_response(b'\x0f')
        assert self.dxp.spectrometer.write_parameter_set(15) == 15
        self.dxp._transceive.assert_called_with(0x82, b'\x00\x0f')

    def test_get_general_set(self):
        self.setup_response(b'\x03')
        assert self.dxp.spectrometer.read_general_set() == 3
        self.dxp._transceive.assert_called_with(0x83, b'\x01')

    def test_set_general_set(self):
        self.setup_response(b'\x02')
        assert self.dxp.spectrometer.write_general_set(2) == 2
        self.dxp._transceive.assert_called_with(0x83, b'\x00\x02')

    def test_get_mca_width(self):
        self.setup_response(b'\x02\x00')
        res = self.dxp.spectrometer.read_mca_width()
        assert res["granularity"] == 2
        assert res["custom_scale"] == 0
        self.dxp._transceive.assert_called_with(0x84, b'\x01')

    def test_set_mca_width_custom(self):
        self.setup_response(b'\x04\x07')
        res = self.dxp.spectrometer.write_mca_width(4, 7)
        assert res["granularity"] == 4
        assert res["custom_scale"] == 7
        self.dxp._transceive.assert_called_with(0x84, b'\x00\x04\x07')

    def test_get_mca_bins(self):
        self.setup_response(b'\x00\x08\x00\x00')
        res = self.dxp.spectrometer.read_mca_bins()
        assert res['num_bins'] == 2048
        self.dxp._transceive.assert_called_with(0x85, b'\x01')

    def test_set_mca_bins(self):
        self.setup_response(b'\x00\x10\x00\x00')
        res = self.dxp.spectrometer.write_mca_bins(4096, 0)
        assert res['num_bins'] == 4096
        self.dxp._transceive.assert_called_with(0x85, b'\x00\x00\x10\x00\x00')

    def test_get_polarity(self):
        self.setup_response(b'\x01')
        assert self.dxp.spectrometer.read_polarity() == 1
        self.dxp._transceive.assert_called_with(0x87, b'\x01')

    def test_set_polarity(self):
        self.setup_response(b'\x01')
        assert self.dxp.spectrometer.write_polarity(1) == 1
        self.dxp._transceive.assert_called_with(0x87, b'\x00\x01')

    def test_get_threshold(self):
        self.setup_response(struct.pack('<HHH', 100, 200, 300))
        res = self.dxp.spectrometer.read_threshold()
        assert res['fast'] == 100
        assert res['intermediate'] == 200
        assert res['slow'] == 300
        self.dxp._transceive.assert_called_with(0x86, b'\x01')

    def test_set_threshold(self):
        self.setup_response(struct.pack('<HHH', 500, 200, 300))
        res = self.dxp.spectrometer.write_threshold(0, 500)
        assert res['fast'] == 500
        self.dxp._transceive.assert_called_with(0x86, b'\x00\x00\xf4\x01')

    def test_get_tau_seconds(self):
        self.setup_response(b'\xD0\x07')
        result = self.dxp.spectrometer.read_tau()
        assert result == pytest.approx(50e-6)
        self.dxp._transceive.assert_called_with(0x89, b'\x01')

    def test_set_tau_seconds(self):
        self.setup_response(b'\xD0\x07')
        result = self.dxp.spectrometer.write_tau(50e-6)
        assert result == pytest.approx(50e-6)
        self.dxp._transceive.assert_called_with(0x89, b'\x00\xD0\x07')

    def test_get_reset_time(self):
        self.setup_response(b'\x32')
        assert self.dxp.spectrometer.read_reset_time() == 50
        self.dxp._transceive.assert_called_with(0x8A, b'\x01')

    def test_set_reset_time(self):
        self.setup_response(b'\x64')
        assert self.dxp.spectrometer.write_reset_time(100) == 100
        self.dxp._transceive.assert_called_with(0x8A, b'\x00\x64')

    def test_read_filter_parameter(self):
        self.setup_response(struct.pack('<BH', 1, 10))
        res = self.dxp.spectrometer.read_filter_parameter(1)
        assert res['param_num'] == 1
        assert res['value'] == 10
        self.dxp._transceive.assert_called_with(0x8B, b'\x01\x01')

    def test_write_filter_parameter(self):
        self.setup_response(struct.pack('<BH', 1, 15))
        res = self.dxp.spectrometer.write_filter_parameter(1, 15)
        assert res['param_num'] == 1
        assert res['value'] == 15
        self.dxp._transceive.assert_called_with(0x8B, b'\x00\x01\x0F\x00')

    def test_get_base_gain(self):
        self.setup_response(struct.pack('<Hb', 32768, -2))
        res = self.dxp.spectrometer.read_digital_base_gain()
        assert res == 0.25
        self.dxp._transceive.assert_called_with(0x9C, b'\x01')

    def test_write_digital_base_gain(self):
        self.setup_response(struct.pack('<Hb', 32768, 0))
        res = self.dxp.spectrometer.write_digital_base_gain(1.0)
        assert res == 1.0
        self.dxp._transceive.assert_called_with(0x9C, b'\x00\x00\x80\x00')

    def test_set_swgain(self):
        self.setup_response(b'\x08')
        assert self.dxp.spectrometer.write_switched_gain(8) == 8
        self.dxp._transceive.assert_called_with(0x9B, b'\x00\x08')

    def test_read_switched_gain(self):
        self.setup_response(b'\x0F')
        assert self.dxp.spectrometer.read_switched_gain() == 15
        self.dxp._transceive.assert_called_with(0x9B, b'\x01')

    def test_slowlen(self):
        mock_data = b'\x01\x01\x02' + (struct.pack('<H', 100) * 24)
        self.setup_response(mock_data)
        res = self.dxp.spectrometer.read_slowlen_values()
        assert res['clkset'] == 1
        assert res['values'][0] == 100
        assert len(res['values']) == 24

    def test_save_parameter_set(self):
        self.setup_response(b'\x05')
        result = self.dxp.spectrometer.save_parameter_set(5)
        assert result == 5
        self.dxp._transceive.assert_called_with(0x8D, b'\x05\x55\xaa')

    def test_save_general_set(self):
        self.setup_response(b'\x02')
        result = self.dxp.spectrometer.save_general_set(2)
        assert result == 2
        self.dxp._transceive.assert_called_with(0x8F, b'\x02\x55\xaa')

    def test_read_parset_values(self):
        self.dxp.parset_id = 12

        self.dxp._pars_by_name = {
            "NUMPARSET": 0,
            "PARVERSION": 1,
            "SLOWLEN": 2,
            "BFACTOR": 3
        }
        self.dxp._pars_by_idx = {v: k for k, v in self.dxp._pars_by_name.items()}

        mock_data = b'\x02\x00\x01' + struct.pack('<HH', 1000, 5)
        self.setup_response(mock_data)

        res = self.dxp.spectrometer.read_parset_values(option=1)

        assert res["parset_id"] == 12
        assert res["numparset"] == 2
        assert res["version"] == 256
        assert res["SLOWLEN"] == 1000
        assert res["BFACTOR"] == 5

    def test_read_genset_values(self):
        self.dxp.genset_id = 2

        # Populate driver dicts exactly how MicroDXP.__init__ does it
        self.dxp._pars_by_name = {
            "NUMGENSET": 10,
            "GENVERSION": 11,
            "HDWRREV": 12,
            "DSPSPEED": 13
        }
        self.dxp._pars_by_idx = {v: k for k, v in self.dxp._pars_by_name.items()}

        mock_data = b'\x02\x00\x02' + struct.pack('<HH', 5, 40)
        self.setup_response(mock_data)

        res = self.dxp.spectrometer.read_genset_values()

        assert res["genset_id"] == 2
        assert res["numgenset"] == 2
        assert res["HDWRREV"] == 5
        assert res["DSPSPEED"] == 40

    def test_hardware_error_propagation(self):
        """Failure: MicroDXPError raised on hardware fault."""
        self.setup_error(0x82, 0x01)
        with pytest.raises(MicroDXPError) as exc:
            self.dxp.spectrometer.write_parameter_set(1)
        assert exc.value.status == 0x01
