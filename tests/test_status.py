""" SPDX-License-Identifier: Apache-2.0 """

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


class TestStatusCommands(TestBase):

    def test_read_temperature(self):
        """Success: 0x41 Read Temperature"""
        self.setup_response(b'\x19\x80')
        assert self.dxp.status.read_temperature() == 25.5
        self.dxp._transceive.assert_called_with(0x41)

    def test_read_serial_number(self):
        """Success: 0x48 Read Serial Number"""
        self.setup_response(b"UDX9EJC252524294")
        sn = self.dxp.status.read_serial_number()
        assert sn == "UDX9EJC252524294"
        self.dxp._transceive.assert_called_with(0x48)

    def test_get_board_information(self):
        """Success: 0x49 Get Board Information"""
        fake_info = bytes.fromhex("24 04 16 11 0A 1E 28 01 01 03 00 40 01 02 01 04 00 00 12 11")
        self.setup_response(fake_info)
        info = self.dxp.status.get_board_information()

        for k, v in self.dxp.board_info.items():
            assert info[k] == v

        self.dxp._transceive.assert_called_with(0x49)

    def test_get_status(self):
        """Success: 0x4B Status"""
        self.setup_response(b'\x01\x02\x03\x04\x05')
        res = self.dxp.status.get_status()

        assert res['pic_status'] == 1
        assert res['dsp_boot_status'] == 2
        assert res['run_state'] == 3
        assert res['dsp_busy'] == 4
        assert res['dsp_runerror'] == 5

        self.dxp._transceive.assert_called_with(0x4B)

    def test_read_dsp_parameter_names(self):
        """Success: 0x42 Read DSP parameter names"""
        names_payload = b"PEAKTIME\x00GAPTIME\x00".ljust(16, b'\x00')
        mock_response = b'\x02\x00\x10\x00' + names_payload
        self.setup_response(mock_response)
        res = self.dxp.status.read_dsp_parameter_names(0)
        assert res['num_parameters'] == 2
        assert res['string_len'] == 16
        assert res['names'] == ["PEAKTIME", "GAPTIME"]
        self.dxp._transceive.assert_called_with(0x42, b'\x00')

    def test_reset_fpga(self):
        """Success: 0x4E Reset FPGA"""
        self.setup_response(b'')
        self.dxp.status.reset_fpga()
        self.dxp._transceive.assert_called_with(0x4E, b'\xaa\x55\xaa\x55')

    def test_reset_dsp(self):
        """Success: 0x4F Reset DSP"""
        self.setup_response(b'')
        self.dxp.status.reset_dsp()
        self.dxp._transceive.assert_called_with(0x4F, b'\xaa\x55\xaa\x55')

    def test_hardware_error_propagation(self):
        """Failure: MicroDXPError raised on hardware fault."""
        self.setup_error(0x41, 0x01)
        with pytest.raises(MicroDXPError) as exc:
            self.dxp.status.read_temperature()
        assert exc.value.status == 0x01

    @pytest.mark.parametrize("opt", [-1, 2])
    def test_read_dsp_parameter_names_validation(self, opt):
        """Failure: ValueError if readout_option is out of range."""
        with pytest.raises(ValueError, match="invalid readout option"):
            self.dxp.status.read_dsp_parameter_names(opt)