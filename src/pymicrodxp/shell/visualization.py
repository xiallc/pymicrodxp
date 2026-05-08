""" SPDX-License-Identifier: Apache-2.0 """

import os
import json
import multiprocessing as mp
import queue as mp_queue
import time

try:
    import tkinter as tk
    from tkinter import filedialog
except ImportError:
    tk = None

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


def plotting_loop(data_queue: mp.Queue, title_prefix: str, ylabel: str, color: str, offset: int):
    """Internal process loop for interactive, non-blocking plotting."""
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt

    plt.ion()
    fig, ax = plt.subplots(num=title_prefix, figsize=(10, 5))
    plt.show(block=False)

    try:
        fig.canvas.manager.window.wm_geometry(f"+{offset}+{offset}")
        fig.canvas.manager.window.attributes("-topmost", 0)
    except Exception:
        pass

    while True:
        try:
            data_packet = data_queue.get(timeout=0.1)

            if data_packet is None:
                plt.close(fig)
                break

            try:
                while not data_queue.empty():
                    new_packet = data_queue.get_nowait()
                    if new_packet is None:
                        plt.close(fig)
                        return
                    data_packet = new_packet
            except mp_queue.Empty:
                pass

            data = data_packet['data']
            sn = data_packet.get('sn', 'Unknown')
            ts = data_packet.get('ts', 'Unknown')

            ax.clear()
            ax.plot(data, color=color, linewidth=1)
            ax.set_title(f"{title_prefix}\nSN: {sn} | {ts}")
            ax.set_xlabel("Index")
            ax.set_ylabel(ylabel)
            ax.grid(True, alpha=0.3)
            fig.canvas.draw_idle()

        except mp_queue.Empty:
            pass
        except Exception as e:
            print(f"\n[Visualization Error] {e}")
            break

        fig.canvas.flush_events()
        time.sleep(0.05)


class VisualizationShell:
    """Commands for data visualization and file browsing."""

    def __init__(self, shell, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shell = shell
        self._plot_queues = {}
        self._plot_processes = {}
        self._window_offset = 50

    @property
    def dxp(self):
        return self.shell.dxp

    def _ensure_plot_process(self, plot_type: str, title: str, ylabel: str, color: str):
        """Spawns or verifies a background plotting process."""
        if not hasattr(self, '_plot_processes'):
            self._plot_processes = {}
        if not hasattr(self, '_plot_queues'):
            self._plot_queues = {}
        if not hasattr(self, '_window_offset'):
            self._window_offset = 50

        if plot_type not in self._plot_processes or not self._plot_processes[plot_type].is_alive():
            if tk is None:
                print("\n[Error] Plotting dependencies (tkinter) are missing.")
                return False

            q = mp.Queue()
            proc = mp.Process(
                target=plotting_loop,
                args=(q, title, ylabel, color, self._window_offset),
                daemon=True
            )
            proc.start()
            self._plot_queues[plot_type] = q
            self._plot_processes[plot_type] = proc
            self._window_offset += 50
        return True

    def run_view_data(self, filename: str = None):
        """Loads a JSON file and plots traces/histograms in separate windows."""

        if not filename:
            if tk is None:
                print("\n[Error] Plotting dependencies are missing.")
                return
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            filename = filedialog.askopenfilename(
                initialdir=os.getcwd(),
                title="Select microDXP Data JSON",
                filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
            )
            if not filename:
                print("No file selected. Returning.")
                return

        try:
            with open(filename, 'r') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return

        trace = data.get("diagnostic_trace")
        hist = data.get("diagnostic_histogram") or data.get("histogram") or data.get('mca')

        if not trace and not hist:
            print(f"No data found in {filename}.")
            return

        sn = data.get("sn", "Unknown")
        ts = data.get("timestamp", "Unknown")

        if trace and self._ensure_plot_process("trace", "Trace", "ADC Value", "#1f77b4"):
            self._plot_queues["trace"].put({'data': trace, 'sn': sn, 'ts': ts})

        if hist and self._ensure_plot_process("hist", "Histogram", "Counts", "green"):
            self._plot_queues["hist"].put({'data': hist, 'sn': sn, 'ts': ts})

    def do_view(self, arg):
        """Visualize a saved JSON data file. Usage: view [filename]"""
        self.shell.run_view_data(arg.strip() if arg else None)

    def complete_view(self, text, line, begidx, endidx):
        """Autocomplete .json files in the current directory."""
        return [f for f in os.listdir('.') if f.startswith(text) and f.endswith('.json')]
