""" SPDX-License-Identifier: Apache-2.0 """
import sys
import os

# Get the absolute path of this example's root (custom_extension/)
example_root = os.path.abspath(os.path.dirname(__file__))

# Add this folder to the system path so 'from extension import ...'
# works perfectly regardless of where pytest was started.
if example_root not in sys.path:
    sys.path.insert(0, example_root)