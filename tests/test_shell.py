""" SPDX-License-Identifier: Apache-2.0 """

import pytest
from unittest.mock import MagicMock, patch, create_autospec

from pymicrodxp.driver import MicroDXP
from pymicrodxp.cli import MicroDXPShell
from pymicrodxp.shell.cli_utils import ShellArgparseExit
from pymicrodxp.core.error import MicroDXPError

from pymicrodxp.commands.status import StatusCommands
from pymicrodxp.commands.diagnostic import DiagnosticCommands
from pymicrodxp.commands.run_control import RunControlCommands
from pymicrodxp.commands.spectrometer_control import SpectrometerControlCommands
from pymicrodxp.commands.peripheral import PeripheralCommands

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


class TestShell:
    @pytest.fixture(autouse=True)
    def setup_shell(self):
        """Initializes the shell and mocks out the hardware driver."""
        self.shell = MicroDXPShell()

        # Strictly mock the base driver
        self.shell.dxp = create_autospec(MicroDXP, instance=True)
        self.shell.dxp.sn = "TEST_SN"

        # FIX: Explicitly attach strictly mocked command namespaces
        self.shell.dxp.status = create_autospec(StatusCommands, instance=True)
        self.shell.dxp.diagnostic = create_autospec(DiagnosticCommands, instance=True)
        self.shell.dxp.run_control = create_autospec(RunControlCommands, instance=True)
        self.shell.dxp.spectrometer = create_autospec(SpectrometerControlCommands, instance=True)
        self.shell.dxp.peripheral = create_autospec(PeripheralCommands, instance=True)

        # Helper to bypass interactive plotting during tests
        self.shell._ensure_plot_process = MagicMock(return_value=True)
        self.shell.run_view_data = MagicMock()

        # Provide safe mock returns to prevent KeyErrors or json.dumps() crashes in print statements
        self.shell.dxp.status.read_dsp_parameter_names.return_value = {'num_parameters': 0,
                                                                       'string_len': 0, 'names': []}
        self.shell.dxp.status.get_board_information.return_value = {}
        self.shell.dxp.status.get_status.return_value = {}

        self.shell.dxp.spectrometer.read_mca_width.return_value = {'granularity': 0,
                                                                   'custom_scale': 0}
        self.shell.dxp.spectrometer.write_mca_width.return_value = {'granularity': 0,
                                                                    'custom_scale': 0}
        self.shell.dxp.spectrometer.read_mca_bins.return_value = {'num_bins': 4096, 'offset': 0}
        self.shell.dxp.spectrometer.write_mca_bins.return_value = {'num_bins': 4096, 'offset': 0}
        self.shell.dxp.spectrometer.read_threshold.return_value = {'fast': 0, 'intermediate': 0,
                                                                   'slow': 0}
        self.shell.dxp.spectrometer.write_threshold.return_value = {'fast': 0, 'intermediate': 0,
                                                                    'slow': 0}
        self.shell.dxp.spectrometer.read_filter_parameter.return_value = {"param_num": 0,
                                                                          "value": 0}
        self.shell.dxp.spectrometer.write_filter_parameter.return_value = {"param_num": 0,
                                                                           "value": 0}
        self.shell.dxp.spectrometer.read_slowlen_values.return_value = {'clkset': 0,
                                                                        'decimation': 0,
                                                                        'values': []}
        self.shell.dxp.spectrometer.read_parset_values.return_value = {}
        self.shell.dxp.spectrometer.read_genset_values.return_value = {}

        self.shell.dxp.run_control.read_run_statistics.return_value = {}
        self.shell.dxp.run_control.read_run_preset.return_value = {'preset_type': 0, 'length': 0}

    # ==========================================
    #               HAPPY PATHS
    # ==========================================

    # --- STATUS COMMANDS ---

    def test_do_temp(self):
        self.shell.do_temp("")
        self.shell.dxp.status.read_temperature.assert_called_once()

    def test_do_par_names(self):
        self.shell.do_par_names("1")
        self.shell.dxp.status.read_dsp_parameter_names.assert_called_once_with(1)

    def test_do_serial(self):
        self.shell.do_serial("")
        self.shell.dxp.status.read_serial_number.assert_called_once()

    def test_do_info(self):
        self.shell.do_info("")
        self.shell.dxp.status.get_board_information.assert_called_once()

    def test_do_status(self):
        self.shell.do_status("")
        self.shell.dxp.status.get_status.assert_called_once()

    def test_do_reset_fpga(self):
        self.shell.do_reset_fpga("")
        self.shell.dxp.status.reset_fpga.assert_called_once()

    def test_do_reset_dsp(self):
        self.shell.do_reset_dsp("")
        self.shell.dxp.status.reset_dsp.assert_called_once()

    # --- DIAGNOSTIC COMMANDS ---

    @patch('builtins.open')
    def test_do_histogram(self, mock_open):
        self.shell.do_histogram("3")
        self.shell.dxp.diagnostic.read_diagnostic_histogram.assert_called_once_with(3)

    @patch('builtins.open')
    def test_do_trace(self, mock_open):
        self.shell.do_trace("100 255 1 2")
        self.shell.dxp.diagnostic.read_diagnostic_trace.assert_called_once_with(100, 255, 1, 2)

    def test_do_echo(self):
        self.shell.do_echo("HELLO")
        self.shell.dxp.diagnostic.echo.assert_called_once_with(b"HELLO")

    def test_do_transceive(self):
        self.shell.do_transceive("0x4A \"01 02\"")
        self.shell.dxp.diagnostic.transceive.assert_called_once_with(74, b'\x01\x02')

    # --- PERIPHERAL COMMANDS ---

    def test_do_i2c_read(self):
        # Passed 01 as the command_byte
        self.shell.do_i2c("read 0x20 01 -r 2")
        self.shell.dxp.peripheral.read_i2c.assert_called_once_with(32, b'\x01', 2)

    def test_do_i2c_write(self):
        # Passed 01 as the command_byte
        self.shell.do_i2c("write 0x20 01 -d \"02 03\"")
        self.shell.dxp.peripheral.write_i2c.assert_called_once_with(32, b'\x01', b'\x02\x03')

    # --- RUN CONTROL COMMANDS ---

    def test_do_start(self):
        self.shell.do_start("--clear_mca")
        self.shell.dxp.run_control.start_run.assert_called_once_with(True)

    def test_do_stop(self):
        self.shell.do_stop("")
        self.shell.dxp.run_control.end_run.assert_called_once()

    @patch('builtins.open')
    def test_do_mca(self, mock_open):
        self.shell.do_mca("0 1024 2 --snapshot")
        self.shell.dxp.run_control.read_mca.assert_called_once_with(0, 1024, 2, True)

    def test_do_stats(self):
        self.shell.do_stats("0 --snapshot")
        self.shell.dxp.run_control.read_run_statistics.assert_called_once_with(mode=0,
                                                                               snapshot=True)

    def test_do_preset_write(self):
        self.shell.do_preset("1 60.5")
        self.shell.dxp.run_control.write_run_preset.assert_called_once_with(1, 60.5)

    def test_do_preset_read(self):
        self.shell.do_preset("")
        self.shell.dxp.run_control.read_run_preset.assert_called_once()

    def test_do_snapshot(self):
        self.shell.do_snapshot("--clear")
        self.shell.dxp.run_control.take_snapshot.assert_called_once_with(clear=True)

    # --- SPECTROMETER CONTROL COMMANDS ---

    def test_do_parset_write(self):
        self.shell.do_parset("5")
        self.shell.dxp.spectrometer.write_parameter_set.assert_called_once_with(5)

    def test_do_parset_read(self):
        self.shell.do_parset("")
        self.shell.dxp.spectrometer.read_parameter_set.assert_called_once()

    def test_do_genset(self):
        self.shell.do_genset("1")
        self.shell.dxp.spectrometer.write_general_set.assert_called_once_with(1)

    def test_do_mca_width(self):
        self.shell.do_mca_width("0 5")
        self.shell.dxp.spectrometer.write_mca_width.assert_called_once_with(0, 5)

    def test_do_mca_bins(self):
        self.shell.do_mca_bins("2048 0")
        self.shell.dxp.spectrometer.write_mca_bins.assert_called_once_with(2048, 0)

    def test_do_threshold(self):
        self.shell.do_threshold("2 1000")
        self.shell.dxp.spectrometer.write_threshold.assert_called_once_with(2, 1000)

    def test_do_polarity(self):
        self.shell.do_polarity("1")
        self.shell.dxp.spectrometer.write_polarity.assert_called_once_with(1)

    def test_do_tau(self):
        self.shell.do_tau("0.5")
        self.shell.dxp.spectrometer.write_tau.assert_called_once_with(0.5)

    def test_do_reset_time(self):
        self.shell.do_reset_time("100")
        self.shell.dxp.spectrometer.write_reset_time.assert_called_once_with(100)

    def test_do_filter_param(self):
        self.shell.do_filter_param("2 15")
        self.shell.dxp.spectrometer.write_filter_parameter.assert_called_once_with(2, 15)

    def test_do_read_parset(self):
        self.shell.do_read_parset("2 0 10")
        self.shell.dxp.spectrometer.read_parset_values.assert_called_once_with(2, 0, 10)

    def test_do_save_parset(self):
        self.shell.do_save_parset("15")
        self.shell.dxp.spectrometer.save_parameter_set.assert_called_once_with(15)

    def test_do_read_genset(self):
        self.shell.do_read_genset("")
        self.shell.dxp.spectrometer.read_genset_values.assert_called_once()

    def test_do_save_genset(self):
        self.shell.do_save_genset("2")
        self.shell.dxp.spectrometer.save_general_set.assert_called_once_with(2)

    def test_do_slowlen(self):
        self.shell.do_slowlen("")
        self.shell.dxp.spectrometer.read_slowlen_values.assert_called_once()

    def test_do_gain_trim(self):
        self.shell.do_gain_trim("1.5")
        self.shell.dxp.spectrometer.write_gain_trim.assert_called_once_with(1.5)

    def test_do_bl_avg_length(self):
        self.shell.do_bl_avg_length("1024")
        self.shell.dxp.spectrometer.write_bl_avg_length.assert_called_once_with(1024)

    def test_do_dac(self):
        self.shell.do_dac("200")
        self.shell.dxp.spectrometer.write_dac_value.assert_called_once_with(200)

    def test_do_swgain(self):
        self.shell.do_swgain("15")
        self.shell.dxp.spectrometer.write_switched_gain.assert_called_once_with(15)

    def test_do_base_gain(self):
        self.shell.do_base_gain("1.5")
        self.shell.dxp.spectrometer.write_digital_base_gain.assert_called_once_with(1.5)

    def test_do_parset_read(self):
        self.shell.do_parset("")
        # Use _with() to ensure absolutely NO arguments are passed
        self.shell.dxp.spectrometer.read_parameter_set.assert_called_once_with()

    def test_do_genset_read(self):
        self.shell.do_genset("")
        self.shell.dxp.spectrometer.read_general_set.assert_called_once_with()

    def test_do_mca_width_read(self):
        self.shell.do_mca_width("")
        self.shell.dxp.spectrometer.read_mca_width.assert_called_once_with()

    def test_do_mca_bins_read(self):
        self.shell.do_mca_bins("")
        self.shell.dxp.spectrometer.read_mca_bins.assert_called_once_with()

    def test_do_threshold_read(self):
        self.shell.do_threshold("")
        self.shell.dxp.spectrometer.read_threshold.assert_called_once_with()

    def test_do_polarity_read(self):
        self.shell.do_polarity("")
        self.shell.dxp.spectrometer.read_polarity.assert_called_once_with()

    def test_do_tau_read(self):
        self.shell.do_tau("")
        self.shell.dxp.spectrometer.read_tau.assert_called_once_with()

    def test_do_reset_time_read(self):
        self.shell.do_reset_time("")
        self.shell.dxp.spectrometer.read_reset_time.assert_called_once_with()

    def test_do_bl_avg_length_read(self):
        self.shell.do_bl_avg_length("")
        self.shell.dxp.spectrometer.read_bl_avg_length.assert_called_once_with()

    def test_do_dac_read(self):
        self.shell.do_dac("")
        self.shell.dxp.spectrometer.read_dac_value.assert_called_once_with()

    def test_do_base_gain_read(self):
        self.shell.do_base_gain("")
        self.shell.dxp.spectrometer.read_digital_base_gain.assert_called_once_with()

    # ==========================================
    #               ERROR PATHS
    # ==========================================

    @pytest.mark.parametrize("method, bad_args", [
        ("do_mca", "abc 1024 2"),  # Bad integer
        ("do_trace", "100 255 1 9"),  # trace_type 9 out of choices range(0, 9)
        ("do_parset", "99"),  # parset 99 out of choices range(24)
        ("do_threshold", "5 1000"),  # filter_choice 5 out of choices [0, 1, 2]
        ("do_i2c", "invalid_mode 0x20"),  # Invalid mode choice
        ("do_base_gain", "not_a_float"),  # Bad float
        ("do_start", "--invalid_flag"),  # Unrecognized argument
    ])
    def test_cli_parsing_errors(self, method, bad_args):
        """Verify that invalid arguments raise the custom ShellArgparseExit to safely abort."""
        with pytest.raises(ShellArgparseExit):
            getattr(self.shell, method)(bad_args)

    @patch('builtins.print')
    def test_hardware_error_handling(self, mock_print):
        """Verify that the decorator catches MicroDXPErrors and prints a formatted trace."""
        self.shell.dxp.run_control.end_run.side_effect = MicroDXPError(0x01, 1)
        self.shell.do_stop("")
        called_args = mock_print.call_args[0][0]
        assert "[Hardware Error]" in called_args
        assert "Error ending run" in called_args

    @patch('builtins.print')
    def test_api_value_error_handling(self, mock_print):
        """Verify that the decorator catches core API ValueErrors and prints a formatted trace."""
        self.shell.dxp.spectrometer.write_tau.side_effect = ValueError("invalid tau value")
        self.shell.do_tau("9999.9")
        called_args = mock_print.call_args[0][0]
        assert "Error [" in called_args
        assert "invalid tau value" in called_args

    @patch('builtins.print')
    def test_requires_connection_guard(self, mock_print):
        """Verify commands abort if the hardware is completely disconnected."""
        self.shell.dxp = None
        self.shell.do_status("")
        mock_print.assert_called_with("Error: Not connected. Use 'connect <uri>' first.")
