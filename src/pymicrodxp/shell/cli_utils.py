""" SPDX-License-Identifier: Apache-2.0 """

import sys
import argparse
import inspect
import re
import os
import traceback
from functools import wraps
from datetime import datetime
from logging.handlers import RotatingFileHandler

from ..core.error import MicroDXPError

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


def extract_desc_help(func):
    """Extracts the main description from a docstring line-by-line."""
    doc = inspect.getdoc(func)
    if not doc:
        return None

    lines = doc.splitlines()
    desc_lines = []
    for line in lines:
        # Stop capturing the description when we hit the first Sphinx tag (e.g., :param, :returns)
        if re.match(r'^\s*:[a-zA-Z_]+', line):
            break
        desc_lines.append(line.strip())

    return " ".join(desc_lines).strip()


def extract_param_help(func, param_name):
    """Extracts parameter help text from a docstring line-by-line."""
    doc = inspect.getdoc(func)
    if not doc:
        return None

    lines = doc.splitlines()
    capture = False
    help_lines = []

    # Regex to detect the start of ANY param/return tag: e.g. ":param clear_mca:"
    tag_pattern = re.compile(r'^\s*:([a-zA-Z_]+)(?:\s+([a-zA-Z_]+))?:')

    for line in lines:
        match = tag_pattern.match(line)
        if match:
            tag_type = match.group(1)
            tag_name = match.group(2)

            if tag_type == 'param' and tag_name == param_name:
                capture = True
                help_text = line[match.end():].strip()
                if help_text:
                    help_lines.append(help_text)
                continue
            else:
                capture = False

        if capture:
            help_lines.append(line.strip())

    if help_lines:
        return " ".join(help_lines).strip()
    return None


class ShellLogger:
    def __init__(self, filename, backup_count: int = 5):
        self.terminal = sys.stdout

        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            handler = RotatingFileHandler(filename, backupCount=backup_count, delay=True)
            handler.doRollover()
            handler.close()

        self.log_file = open(filename, 'a', encoding='utf-8')
        self.encoding = getattr(self.terminal, 'encoding', 'utf-8')
        self.errors = getattr(self.terminal, 'errors', 'strict')

    def isatty(self):
        return self.terminal.isatty()

    def fileno(self):
        return self.terminal.fileno()

    def write(self, message):
        self.terminal.write(message)
        self.log_file.write(message)
        self.log_file.flush()

    def flush(self):
        self.terminal.flush()
        self.log_file.flush()

    def log_input(self, prompt, line):
        timestamp = datetime.now().isoformat()
        self.log_file.write(f"\n[{timestamp}] {prompt}{line}\n")
        self.log_file.flush()

    def log_error(self, command: str, status: int):
        """Logs hardware command failures with the status code."""
        ts = datetime.now().isoformat()
        self.log_file.write(f"[{ts}] ERROR: Command {command} failed with status {status}\n")
        self.log_file.flush()

    def log_status(self, command: str, status: int):
        """Logs successful hardware command statuses."""
        ts = datetime.now().isoformat()
        self.log_file.write(f"[{ts}] SUCCESS: Command {command} status {status}\n")
        self.log_file.flush()


class ShellArgparseExit(BaseException):
    """Custom exception to catch argparse exits without killing the shell."""
    pass


def format_error_traceback(prefix: str, e: BaseException) -> str:
    """Helper to dynamically extract the file and line number of an exception."""
    tb_list = traceback.extract_tb(e.__traceback__)
    if tb_list:
        last_frame = tb_list[-1]
        fname = os.path.basename(last_frame.filename)
        return f"{prefix} [{fname}:{last_frame.lineno}] - {e}"
    return f"{prefix} - {e}"


def requires_connection(func):
    """Decorator to ensure the hardware is connected and handle API errors."""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.dxp:
            print("Error: Not connected. Use 'connect <uri>' first.")
            return
        try:
            return func(self, *args, **kwargs)
        except ValueError as e:
            print(format_error_traceback("Error", e))
        except MicroDXPError as e:
            print(format_error_traceback("[Hardware Error]", e))
        except Exception as e:
            print(format_error_traceback("[Error]", e))

    return wrapper


class ShellArgumentParser(argparse.ArgumentParser):
    """Custom parser that catches errors instead of exiting the program."""

    def __init__(self, *args, target_func=None, target_funcs=None, **kwargs):
        self.target_funcs = target_funcs or []
        if target_func:
            self.target_funcs.append(target_func)

        kwargs.setdefault('formatter_class', argparse.ArgumentDefaultsHelpFormatter)

        if self.target_funcs and 'description' not in kwargs:
            desc = extract_desc_help(self.target_funcs[0])
            if desc:
                kwargs['description'] = desc.replace('%', '%%')

        super().__init__(*args, **kwargs)

    def add_argument(self, *args, **kwargs):
        specific_func = kwargs.pop('target_func', None)
        funcs_to_search = [specific_func] if specific_func else self.target_funcs

        if funcs_to_search and 'help' not in kwargs:
            param_name = None
            for arg in args:
                if arg.startswith('--'):
                    param_name = arg[2:]
                    break
                elif not arg.startswith('-'):
                    param_name = arg
                    break

            if param_name:
                for func in funcs_to_search:
                    sig = inspect.signature(func)
                    if param_name in sig.parameters:
                        param = sig.parameters[param_name]

                        if 'help' not in kwargs:
                            help_text = extract_param_help(func, param_name)
                            if help_text:
                                kwargs['help'] = help_text.replace('%', '%%')

                        if 'type' not in kwargs and 'action' not in kwargs:
                            if param.annotation is bool:
                                kwargs[
                                    'action'] = 'store_false' if param.default is True else 'store_true'
                            elif param.annotation in (int, float, str):
                                kwargs['type'] = param.annotation

                        if 'default' not in kwargs and 'action' not in kwargs:
                            if param.default != inspect.Parameter.empty:
                                kwargs['default'] = param.default
                        break

        return super().add_argument(*args, **kwargs)

    def error(self, message):
        print(f"Usage Error: {message}")
        self.print_usage()
        raise ShellArgparseExit()

    def exit(self, status=0, message=None):
        """Override exit to prevent argparse from closing the shell."""
        if message:
            print(message)
        raise ShellArgparseExit()
