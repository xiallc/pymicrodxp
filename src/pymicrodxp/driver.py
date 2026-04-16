""" SPDX-License-Identifier: Apache-2.0 """

import logging
from typing import Optional, Dict, Union

from .core.logging import configure_logging, logger, MergingAdapter
from .core.protocol import MicroDXPBase

from .commands import (StatusCommands, DiagnosticCommands, RunControlCommands,
                       SpectrometerControlCommands, PeripheralCommands)

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


class MicroDXP(MicroDXPBase):
    CORE_NAMESPACES = {'status', 'diagnostics', 'run_control', 'spectrometer', 'peripheral'}

    def __init__(self, uri: str, timeout: float = 2.0,
                 log_level=logging.INFO, log_file: Optional[str] = None) -> None:
        super().__init__(uri, timeout)

        self.status = StatusCommands(self)
        self.diagnostic = DiagnosticCommands(self)
        self.run_control = RunControlCommands(self)
        self.spectrometer = SpectrometerControlCommands(self)
        self.peripheral = PeripheralCommands(self)

        configure_logging(level=log_level, log_file=log_file)
        self.sn: str = self.status.read_serial_number()

        self.log: MergingAdapter = MergingAdapter(logger, {"sn": self.sn})

        self.board_info: Dict[
            str, Union[int, float, str, None]] = self.status.get_board_information()
        self.parset_id: int = self.spectrometer.read_parameter_set()
        self.genset_id: int = self.spectrometer.read_general_set()

        par_names = self.status.read_dsp_parameter_names(0)['names']
        self._pars_by_name: Dict[str, int] = {}
        self._pars_by_idx: Dict[int, str] = {}

        for idx, name in enumerate(par_names):
            self._pars_by_idx[idx] = name
            self._pars_by_name[name] = idx

    def register_extension(self, name: str, extension_class):
        """
        Attaches a customer extension to the driver with namespace protection.
        """
        if name in self.CORE_NAMESPACES:
            raise ValueError(f"Namespace '{name}' is reserved for core functionality.")

        setattr(self, name, extension_class(self))
        self.log.info(f"Registered extension namespace: {name}")

    def __setattr__(self, key, value):
        """Prevent accidental overwriting of core namespaces."""
        if hasattr(self, key) and key in self.CORE_NAMESPACES:
            raise AttributeError(f"Cannot overwrite core namespace '{key}'.")
        super().__setattr__(key, value)
