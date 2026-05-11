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


class TestRunControl(TestBase):

    def test_start_run_new(self):
        """Success: 0x00 Start a new run."""
        self.setup_response(b'\x05\x00')
        assert self.dxp.run_control.start_run(clear_mca=True) == 5
        self.dxp._transceive.assert_called_with(0x00, b'\x01')

    def test_start_run_resume(self):
        """Success: 0x00 Resume a run."""
        self.setup_response(b'\x05\x00')
        assert self.dxp.run_control.start_run(clear_mca=False) == 5
        self.dxp._transceive.assert_called_with(0x00, b'\x00')

    def test_end_run(self):
        """Success: 0x01 End Run"""
        self.setup_response(b'\x00')
        assert self.dxp.run_control.end_run() is None
        self.dxp._transceive.assert_called_with(0x01)

    def test_read_mca_3bytes(self):
        """Success: 0x02 Read MCA"""
        fake_data = b'\x01\x00\x00\xDE\xAD\xBE'
        self.setup_response(fake_data)
        mca = self.dxp.run_control.read_mca(0, 2, 3)
        assert mca == [1, 12496350]

    def test_read_mca_snapshot(self):
        """Success: 0x09 Read Snapshot MCA"""
        fake_data = b'\x01\x00\x00\xDE\xAD\xBE'
        self.setup_response(fake_data)
        mca = self.dxp.run_control.read_mca(0, 2, 3, snapshot=True)
        self.dxp._transceive.assert_called_with(0x09, b'\x00\x00\x02\x00\x03')
        assert mca == [1, 12496350]

    def test_read_multisca(self):
        """Failure: NotImplementedError for MultiSCA"""
        with pytest.raises(NotImplementedError):
            self.dxp.run_control.read_multisca()

    def test_read_run_stats(self):
        """Success: 0x06 Read Run Statistics"""
        lt_ticks = int(1.0 / 500e-9).to_bytes(6, 'little')
        rt_ticks = int(2.0 / 500e-9).to_bytes(6, 'little')
        payload = (lt_ticks + rt_ticks +
                   b'\xEF\xBE\xAD\xDE\x0D\xF0\xAD\xBA\x1A\xCC\xCA\xF0\xAD\xDE\xE1\xFE')

        self.setup_response(payload)
        result = self.dxp.run_control.read_run_statistics(mode=1)

        assert result["livetime"] == pytest.approx(1.0)
        assert result["realtime"] == pytest.approx(2.0)
        assert result['input_events'] == 3735928559
        assert result['output_events'] == 3131961357
        assert result['underflows'] == 4039822362
        assert result['overflows'] == 4276215469

    def test_read_run_stats_snapshot(self):
        """Success: 0x0A Read Snapshot Run Statistics"""
        lt_ticks = int(1.0 / 500e-9).to_bytes(6, 'little')
        rt_ticks = int(2.0 / 500e-9).to_bytes(6, 'little')
        payload = lt_ticks + rt_ticks + b'\x00' * 16

        self.setup_response(payload)
        result = self.dxp.run_control.read_run_statistics(snapshot=True)

        assert result["livetime"] == pytest.approx(1.0)
        self.dxp._transceive.assert_called_with(0x0A)

    def test_set_run_preset(self):
        """Success: 0x07 Set Run Preset"""
        self.setup_response(b'\x01\xF4\xA5\x93\xD6\x00\x00')
        self.dxp.run_control.write_run_preset(1, 1800.00025)
        self.dxp._transceive.assert_called_with(0x07, b'\x00\x01\xF4\xA5\x93\xD6')

    def test_get_run_preset(self):
        """Success: 0x07 Get Run Preset"""
        self.setup_response(b'\x01\xF4\x81\x79\xEF\xD3\x15')
        data = self.dxp.run_control.read_run_preset()
        assert data['preset_type'] == 1
        assert data['length'] == pytest.approx(12000000.00025)
        self.dxp._transceive.assert_called_with(0x07, b'\x01')

    def test_take_snapshot(self):
        """Success: 0x08 Take MCA Snapshot"""
        self.setup_response(b'\x00')
        self.dxp.run_control.take_snapshot(clear=True)
        self.dxp._transceive.assert_called_with(0x08, b'\x01')

    def test_hardware_error_propagation(self):
        """Failure: MicroDXPError raised on hardware fault."""
        self.setup_error(0x00, 0x01)
        with pytest.raises(MicroDXPError) as exc:
            self.dxp.run_control.start_run()
        assert exc.value.status == 0x01

    @pytest.mark.parametrize("first, num, bpb, err_msg", [
        (-1, 1024, 2, "invalid first bin"),
        (0x10000, 1024, 2, "invalid first bin"),
        (0, -1, 2, "invalid number of MCA bins"),
        (0, 0, 2, "invalid number of MCA bins"),
        (0, 1024, 0, "invalid bytes per bin"),
        (0, 1024, -1, "invalid bytes per bin"),
    ])
    def test_read_mca_validation(self, first, num, bpb, err_msg):
        with pytest.raises(ValueError, match=err_msg):
            self.dxp.run_control.read_mca(first, num, bpb)

    @pytest.mark.parametrize("mode", [-1, 2])
    def test_read_run_statistics_validation(self, mode):
        with pytest.raises(ValueError, match="invalid mode"):
            self.dxp.run_control.read_run_statistics(mode=mode)

    @pytest.mark.parametrize("p_type, length, err_msg", [
        (-1, 60, "invalid preset type"),
        (5, 60, "invalid preset type"),
        (1, -10.0, "preset length cannot be negative"),
    ])
    def test_write_run_preset_validation(self, p_type, length, err_msg):
        with pytest.raises(ValueError, match=err_msg):
            self.dxp.run_control.write_run_preset(p_type, length)

    def test_write_run_preset_32bit_overflow(self):
        """Line 171: Branch where high word (bytes 32-48) is used."""
        # Value > 2^32 - 1
        val = 0x100000000
        self.setup_response(b'\x03' + b'\x00' * 6)
        self.dxp.run_control.write_run_preset(3, val)
        # Verify 9-byte packet (cmd + preset + 3 words)
        sent_data = self.dxp._transceive.call_args[0][1]
        assert len(sent_data) == 8  # 1 (mode) + 1 (type) + 6 (3 words)

    def test_set_run_mode_not_implemented(self):
        """Line 199: NotImplementedError coverage."""
        with pytest.raises(NotImplementedError):
            self.dxp.run_control.set_run_mode(1)
