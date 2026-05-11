""" SPDX-License-Identifier: Apache-2.0 """
import pytest

from unittest.mock import MagicMock
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


class TestDriver(TestBase):

    def test_driver_namespace_protection(self):
        """Ensure that we cannot overwrite extensions in the core namespace."""
        with pytest.raises(ValueError, match="reserved for core"):
            self.dxp.register_extension("status", MagicMock)

        with pytest.raises(AttributeError, match="Cannot overwrite core namespace"):
            self.dxp.status = "overwritten"

    def test_driver_init_and_registration(self):
        """Ensure that we can register new extensions."""
        self.dxp.register_extension("test_ext", MagicMock)
        assert hasattr(self.dxp, "test_ext")
