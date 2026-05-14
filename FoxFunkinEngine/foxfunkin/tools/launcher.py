from __future__ import annotations

import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from foxfunkin.core.paths import project_root
from .asset_validator import validate_assets
from .mod_wizard import WizardGUI
from .chart_editor import ChartEditor
from .visual_programmer import VisualProgrammer


class ToolsLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FoxFunkin Tools")
        self.geometry("760x520")
        self.root_path = project_root()
        self.build()

    def build(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=12, pady=12)

        home = ttk.Frame(nb)
        nb.add(home, text="Home")
        ttk.Label(home, text="FoxFunkin Tools", font=("Arial", 22, "bold")).pack(anchor="w", padx=18, pady=(18, 8))
        ttk.Label(home, text=f"Project: {self.root_path}").pack(anchor="w", padx=18, pady=4)
        ttk.Button(home, text="Open Mod Wizard", command=self.open_wizard).pack(anchor="w", padx=18, pady=8)
        ttk.Button(home, text="Open Chart Editor", command=self.open_chart).pack(anchor="w", padx=18, pady=8)
        ttk.Button(home, text="Open Visual Programmer", command=self.open_visual).pack(anchor="w", padx=18, pady=8)
        ttk.Button(home, text="Run Engine", command=self.run_engine).pack(anchor="w", padx=18, pady=8)

        assets = ttk.Frame(nb)
        nb.add(assets, text="Asset Check")
        ttk.Button(assets, text="Refresh asset report", command=lambda: self.refresh_assets(report)).pack(anchor="w", padx=12, pady=8)
        report = tk.Text(assets, wrap="word", height=20)
        report.pack(fill="both", expand=True, padx=12, pady=8)
        self.refresh_assets(report)

        help_tab = ttk.Frame(nb)
        nb.add(help_tab, text="Mini Guide")
        text = tk.Text(help_tab, wrap="word")
        text.pack(fill="both", expand=True, padx=12, pady=12)
        text.insert("1.0", """Mini guide:

1. Put external assets into /data if you want the original asset layout.
2. Do not commit /data to GitHub.
3. Use Mod Wizard to create a playable mini-mod.
4. Chart Editor edits *-chart.json.
5. Visual Programmer saves *.fnvgraph.json and chart events can run them:
   { "t": 2000, "e": "RunGraph", "v": "graphs/intro.fnvgraph.json" }

The engine searches enabled mods first, then /data. That means mods can override anything by path.
""")
        text.configure(state="disabled")

    def refresh_assets(self, widget):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", "\n".join(validate_assets(self.root_path, return_lines=True)))
        widget.configure(state="disabled")

    def open_wizard(self):
        WizardGUI()

    def open_chart(self):
        ChartEditor(self)

    def open_visual(self):
        VisualProgrammer(self)

    def run_engine(self):
        try:
            subprocess.Popen([sys.executable, str(self.root_path / "run_engine.py")], cwd=str(self.root_path))
        except Exception as exc:
            messagebox.showerror("Error", str(exc))


def main():
    ToolsLauncher().mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
