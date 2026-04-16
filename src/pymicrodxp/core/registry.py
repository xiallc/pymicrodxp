""" SPDX-License-Identifier: Apache-2.0 """

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

COMMAND_REGISTRY = {
    0x00: {
        "name": "START_RUN",
        "status_messages": {
            0: "Success",
        },
        'tx': {
            'ndata': [1],
            'args': {
                'clear_mca': {
                    'format': 'B',
                    'vals': {
                        0: {"description": 'resume run'},
                        1: {"description": 'new run'}
                    }
                }
            }
        },
        'rx': {
            'ndata': [3],
            'args': {
                'status': {
                    'format': 'B'
                },
                'run_number': {
                    'format': '<H'
                }
            }
        }
    },
    0x01: {
        "name": "END_RUN",
        "status_messages": {1: "Error ending run"}
    },
    0x02: {
        "name": "READ_MCA",
        "is_large": True
    },
    0x06: {
        "name": "READ_RUN_STATISTICS",
    },
    0x07: {
        "name": "SET_GET_RUN_PRESET",
        "selector": "mode",
        "base": {
            "status_messages": {"0": "Success"}
        },
        "operations": {
            "SET": {
                "tx": [
                    {"name": "mode", "format": "B", "value": 0},
                    {"name": "preset_type", "format": "B", "vals": {
                        "0": {"description": "Indefinite"},
                        "1": {"description": "Fixed Realtime", "user_units": "seconds"},
                        "2": {"description": "Fixed Livetime", "user_units": "seconds"},
                        "3": {"description": "Output Counts", "user_units": "counts"},
                        "4": {"description": "Input Counts", "user_units": "counts"}
                    }
                     },
                    {"name": "length", "format": "3H", "optional": True,
                     "range": {"min": "0", "max": "2.81e14"}}
                ]
            },
            "GET": {
                "tx": [
                    {"name": "mode", "format": "B", "value": 1}
                ],
                "rx": [
                    {"name": "preset_type", "format": "B"},
                    {"name": "length", "format": "3H"}
                ]
            }
        }
    },
    0x08: {
        "name": "TAKE_MCA_SNAPSHOT",
        "status_messages": {
            1: "MCALEN > 4096",
            2: "Snapshot timeout"
        }
    },
    0x09: {
        "name": "READ_SNAPSHOT_MCA",
        "status_messages": {1: "MCALEN > 4096 bins"}
    },
    0x0A: {
        "name": "READ_SNAPSHOT_RUN_STATISTICS",
        "status_messages": {1: "MCALEN > 4096 bins"}
    },
    0x10: {
        "name": "READ_DIAGNOSTIC_HISTOGRAM"
    },
    0x11: {
        "name": "READ_DIAGNOSTIC_TRACE",
        "is_large": True
    },
    0x40: {
        "name": "I2C_READ_WRITE",
    },
    0x41: {
        "name": "READ_TEMPERATURE",
    },
    0x42: {
        "name": "READ_DSP_PAR_NAMES",
    },
    0x43: {
        "name": "RW_DSP_PAR",
    },
    0x44: {
        "name": "RW_DSP_PROGRAM_MEM",
        "advanced": True
    },
    0x45: {
        "name": "RW_DSP_DATA_MEM",
        "advanced": True
    },
    0x48: {
        "name": "READ_SN",
    },
    0x49: {
        "name": "GET_BOARD_INFO",
    },
    0x4A: {
        "name": "ECHO",
    },
    0x4B: {
        "name": "GET_STATUS",
        "operations": {
            "READ": {
                "tx": [],
                "rx": [
                    {"name": "pic_status", "format": "B"},
                    {"name": "dsp_boot_status", "format": "B"},
                    {"name": "run_state", "format": "B", "vals": {
                        "0": {"description": "idle"},
                        "1": {"description": "running"}
                    }
                     },
                    {"name": "dsp_busy", "format": "B"},
                    {"name": "dsp_runerror", "format": "B"}
                ]
            }
        }
    },
    0x4C: {
        "name": "INPUT_ENABLE",
    },
    0x4D: {
        "name": "FLASH_WRITE_PROTECT_CTRL",
        "advanced": True
    },
    0x4E: {
        "name": "RESET_FPGA",
        "advanced": True
    },
    0x4F: {
        "name": "RESET_DSP",
        "advanced": True
    },
    0x82: {
        "name": "PARAMETER_SET",
        "range": range(24)
    },
    0x83: {
        "name": "GENERAL_SET",
        "range": range(5),
    },
    0x84: {
        "name": "MCA_BIN_WIDTH",
    },
    0x85: {
        "name": "NUMBER_OF_MCA_BINS",
        "status_messages": {1: "Invalid setting"}
    },
    0x86: {
        "name": "THRESHOLD",
    },
    0x87: {
        "name": "DETECTOR_POLARITY",
        "status_messages": {1: "Invalid setting"}
    },
    0x89: {
        "name": "RC_TIME_CONSTANT",
    },
    0x8A: {
        "name": "PREAMP_RESET_TIME",
    },
    0x8B: {
        "name": "FILTER_PAR_VALUE",
    },
    0x8C: {
        "name": "READ_PARSET_VALUES",
    },
    0x8D: {
        "name": "SAVE_PARSET",
    },
    0x8E: {
        "name": "READ_CURRENT_GENSET_VALUES",
    },
    0x8F: {
        "name": "SAVE_CURRENT_GENSET",
    },
    0x90: {
        "name": "READ_SLOWLEN_VALUES",
    },
    0x91: {
        "name": "GAIN_TRIM",
    },
    0x92: {
        "name": "BLFILTER",
    },
    0x93: {
        "name": "RUNTASKS",
        "advanced": True
    },
    0x94: {
        "name": "FIPCONTROL",
        "advanced": True
    },
    0x96: {
        "name": "SCA_PULSE_PERIODS",
    },
    0x97: {
        "name": "MULTISCA_REGION_LIMITS",
    },
    0x98: {
        "name": "AUTOSTART",
        "pic_version": ">1.3"
    },
    0x99: {
        "name": "OFFSET_DAC",
    },
    0x9B: {
        "name": "SWITCHED_GAIN",
    },
    0x9C: {
        "name": "BASE_GAIN",
    },
    0x9D: {
        "name": "ADC_OFFSET",
    },
    0x9E: {
        "name": "RESET_RC_SWITCH_POSITION",
    },
    0x9F: {
        "name": "APPLY_SETTINGS",
    },
    0xA0: {
        "name": "ADC_MAX",
    },
}
