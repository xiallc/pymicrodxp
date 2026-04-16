""" SPDX-License-Identifier: Apache-2.0 """

import logging
from logging.handlers import RotatingFileHandler
import json
import functools
from datetime import datetime
import os

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

logger = logging.getLogger("pymicrodxp")
logger.propagate = False


class MergingAdapter(logging.LoggerAdapter):
    """
    Custom adapter that merges the constructor 'extra' (SN)
    with the 'extra' passed during the log call (context).
    """

    def process(self, msg, kwargs):
        if "extra" not in kwargs:
            kwargs["extra"] = self.extra
        else:
            kwargs["extra"].update(self.extra)
        return msg, kwargs


class JSONFormatter(logging.Formatter):
    """ISO8601 JSON logs with Serial Number and Context."""

    def format(self, record):
        log_record = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "sn": getattr(record, "sn", "UNKNOWN"),
            "msg": record.getMessage(),
        }

        context = getattr(record, "context", None)
        if isinstance(context, dict):
            log_record.update(context)

        return json.dumps(
            log_record,
            default=lambda o: o.hex(' ').upper() if isinstance(o, (bytes, bytearray)) else str(o)
        )


def configure_logging(level=logging.INFO, log_file=None):
    """
    Configures the logger with a rotating file handler.
    """
    logger.setLevel(level)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    if log_file:
        handler = RotatingFileHandler(log_file, maxBytes=0, backupCount=5)

        if os.path.exists(log_file) and os.path.getsize(log_file) > 0:
            handler.doRollover()

        handler.setFormatter(JSONFormatter())
        handler.setLevel(level)
        logger.addHandler(handler)


def trace_command(cmd_byte, operation=''):
    """
    Decorator to log calls with explicit command and operation tracking.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            cmd_info = COMMAND_REGISTRY.get(cmd_byte, {})
            cmd_name = cmd_info.get("name", f"0x{cmd_byte:02X}")
            self.log.info(f"CALL: {cmd_name} [{operation}]",
                          extra={"context": {
                              "operation": operation,
                              "args": args,
                              "kwargs": kwargs
                          }})
            try:
                result = func(self, *args, **kwargs)
                self.log.info(f"SUCCESS: {cmd_name} [{operation}]")
                return result
            except Exception as e:
                self.log.error(f"FAILURE: {cmd_name} [{operation}]",
                               extra={"context": {
                                   "operation": operation,
                                   "err": str(e)
                               }})
                raise

        return wrapper

    return decorator
