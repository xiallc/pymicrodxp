""" SPDX-License-Identifier: Apache-2.0 """
import pytest

from pymicrodxp.core.transport import Transport
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


class TestTransport(TestBase):
    """Tests related to the base transport class"""


    def test_transport_base_unimplemented(self):
        """Ensures that if we provide a URI base that we don't know we error out."""
        base = Transport("none://", 1.0)
        with pytest.raises(NotImplementedError): base.exchange(b'')
        with pytest.raises(NotImplementedError): base.close()
        with pytest.raises(ValueError, match="requires a USB connection"):
            base.read_memory(0, 0)
