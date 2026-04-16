""" SPDX-License-Identifier: Apache-2.0 """

import json

from .registry import COMMAND_REGISTRY

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


class MicroDXPError(Exception):
    def __init__(self, command_byte: int, status_code: int, extra_data: bytes = b''):
        self.command_byte = command_byte
        self.status = status_code
        self.extra_data = extra_data

        cmd_info = COMMAND_REGISTRY.get(command_byte, {})
        self.name = cmd_info.get("name", f"0x{command_byte:02X}")
        self.msg = cmd_info.get("status_messages", {}).get(status_code, "Unknown hardware error")

        payload = {
            "cmd": f"0x{command_byte:02X}",
            "name": self.name,
            "status": status_code,
            "msg": self.msg
        }
        if extra_data:
            payload["extra"] = extra_data.hex().upper()

        super().__init__(json.dumps(payload))
