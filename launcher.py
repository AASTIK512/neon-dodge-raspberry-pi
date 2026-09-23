#!/usr/bin/env python3
"""Neon Launchpad: launch and manage multiple Windows executables at once."""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import tkinter as tk
from dataclasses import asdict, dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

APP_DIR = Path.home() / ".neon-launchpad"
CONFIG_PATH = APP_DIR / "launchers.json"

BG = "#090d1f"
PANEL = "#111831"
PANEL_2 = "#17213f"
BORDER = "#26365f"
TEXT = "#eef4ff"
MUTED = "#8998bd"
CYAN = "#35e1ff"
PINK = "#ff4f9a"
GREEN = "#60e6a8"
YELLOW = "#ffdc68"
RED = "#ff6674"


@dataclass
class LaunchItem:
    name: str = "New program"
    executable: str = ""
    arguments: str = ""
    working_dir: str = ""
    enabled: bool = True


class NeonLaunchpad(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Neon Launchpad")
        self.geometry("1060x720")
        self.minsize(850, 560)
        self.configure(bg=BG)
        self.processes: dict[int, subprocess.Popen] = {}
        self.items: list[LaunchItem] = self.load_items()
        self.rows: list[dict[str, object]] = []
        self.build_style()
        self.build_ui()
        self.refresh_rows()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(800, self.refresh_process_status)

    def build_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TButton", background=PANEL_2, foreground=TEXT, bordercolor=BORDER,
                        lightcolor=PANEL_2, darkcolor=PANEL_2, padding=(12, 8), font=("Segoe UI", 10))
        style.map("TButton", background=[("active", "#24345f")], foreground=[("disabled", MUTED)])
        style.configure("Accent.TButton", background=CYAN, foreground="#06121f", bordercolor=CYAN,
                        padding=(16, 10), font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton", background=[("active", "#86edff")])
        style.configure("Danger.TButton", background="#3d1d32", foreground="#ffb7d2", bordercolor="#70405b")
        style.map("Danger.TButton", background=[("active", "#5a2949")])
        style.configure("TEntry", fieldbackground="#0c132a", foreground=TEXT, insertcolor=CYAN,
                        bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER, padding=8)
        style.configure("TCheckbutton", background=PANEL, foreground=TEXT, font=("Segoe UI", 10))
        style.map("TCheckbutton", background=[("active", PANEL)])
        style.configure("TScrollbar", background=PANEL_2, troughcolor=BG, bordercolor=BG, arrowcolor=MUTED)

    def build_ui(self) -> None:
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=28, pady=(24, 8))
        tk.Label(header, text="NEON", fg=CYAN, bg=BG, font=("Segoe UI", 25, "bold")).pack(side="left")
        tk.Label(header, text="LAUNCHPAD", fg=TEXT, bg=BG, font=("Segoe UI", 25, "bold")).pack(side="left", padx=(7, 0))
        tk.Label(header, text="MULTI-PROGRAM STARTER", fg=MUTED, bg=BG, font=("Segoe UI", 9, "bold")).pack(side="right", pady=10)

        toolbar = tk.Frame(self, bg=BG)
        toolbar.pack(fill="x", padx=28, pady=(4, 18))
        ttk.Button(toolbar, text="＋  Add program", command=self.add_item).pack(side="left")
        ttk.Button(toolbar, text="▣  Launch enabled", style="Accent.TButton", command=self.launch_enabled).pack(side="left", padx=10)
        ttk.Button(toolbar, text="■  Stop all", style="Danger.TButton", command=self.stop_all).pack(side="left")
        self.status_label = tk.Label(toolbar, text="Ready", fg=GREEN, bg=BG, font=("Segoe UI", 10, "bold"))
        self.status_label.pack(side="right", pady=10)

        card = tk.Frame(self, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True, padx=28, pady=(0, 14))
        tk.Label(card, text="LAUNCH GROUP", fg=TEXT, bg=PANEL, font=("Segoe UI", 12, "bold"), anchor="w").pack(fill="x", padx=18, pady=(16, 2))
        tk.Label(card, text="Add as many programs as you need. Enabled rows launch together, in order.", fg=MUTED, bg=PANEL, font=("Segoe UI", 9), anchor="w").pack(fill="x", padx=18, pady=(0, 13))

        self.canvas = tk.Canvas(card, bg=PANEL, highlightthickness=0)
        scrollbar = ttk.Scrollbar(card, orient="vertical", command=self.canvas.yview)
        self.rows_frame = tk.Frame(self.canvas, bg=PANEL)
        self.rows_frame.bind("<Configure>", lambda _: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.rows_frame, anchor="nw")
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfigure(self.canvas_window, width=event.width))
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=(0, 12))
        scrollbar.pack(side="right", fill="y", padx=(0, 12), pady=(0, 12))

        footer = tk.Frame(self, bg=BG)
        footer.pack(fill="x", padx=28, pady=(0, 20))
        tk.Label(footer, text="Tip: use Browse to select .exe files. Arguments are optional.", fg=MUTED, bg=BG, font=("Segoe UI", 9)).pack(side="left")
        ttk.Button(footer, text="Save profile", command=self.save_profile).pack(side="right")

    def load_items(self) -> list[LaunchItem]:
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            return [LaunchItem(**item) for item in data]
        except (OSError, ValueError, TypeError):
            return [LaunchItem(name="My first program")]

    def save_profile(self) -> None:
        self.sync_items()
        try:
            APP_DIR.mkdir(parents=True, exist_ok=True)
            CONFIG_PATH.write_text(json.dumps([asdict(item) for item in self.items], indent=2), encoding="utf-8")
            self.set_status("Profile saved", GREEN)
        except OSError as exc:
            messagebox.showerror("Could not save", str(exc))

    def sync_items(self) -> None:
        for index, row in enumerate(self.rows):
            self.items[index] = LaunchItem(
                name=str(row["name"].get()), executable=str(row["exe"].get()),
                arguments=str(row["args"].get()), working_dir=str(row["cwd"].get()),
                enabled=bool(row["enabled"].get()),
            )

    def refresh_rows(self) -> None:
        self.sync_items() if self.rows else None
        for child in self.rows_frame.winfo_children():
            child.destroy()
        self.rows = []
        if not self.items:
            self.items.append(LaunchItem())
        for index, item in enumerate(self.items):
            self.make_row(index, item)

    def make_row(self, index: int, item: LaunchItem) -> None:
        row = tk.Frame(self.rows_frame, bg=PANEL_2, highlightbackground=BORDER, highlightthickness=1)
        row.pack(fill="x", padx=6, pady=5)
        row.grid_columnconfigure(2, weight=1)
        enabled = tk.BooleanVar(value=item.enabled)
        name = ttk.Entry(row, width=21)
        name.insert(0, item.name)
        exe = ttk.Entry(row)
        exe.insert(0, item.executable)
        args = ttk.Entry(row, width=20)
        args.insert(0, item.arguments)
        cwd = ttk.Entry(row, width=20)
        cwd.insert(0, item.working_dir)
        ttk.Checkbutton(row, variable=enabled).grid(row=0, column=0, padx=(12, 6), pady=14)
        name.grid(row=0, column=1, padx=6, sticky="ew")
        exe.grid(row=0, column=2, padx=6, sticky="ew")
        ttk.Button(row, text="Browse", command=lambda entry=exe: self.browse_exe(entry)).grid(row=0, column=3, padx=6)
        args.grid(row=0, column=4, padx=6, sticky="ew")
        cwd.grid(row=0, column=5, padx=6, sticky="ew")
        ttk.Button(row, text="×", style="Danger.TButton", command=lambda: self.remove_item(index)).grid(row=0, column=6, padx=(6, 12))
        self.rows.append({"name": name, "exe": exe, "args": args, "cwd": cwd, "enabled": enabled, "frame": row})

    def browse_exe(self, entry: ttk.Entry) -> None:
        path = filedialog.askopenfilename(title="Choose a program", filetypes=[("Windows executable", "*.exe"), ("All files", "*.*")])
        if path:
            entry.delete(0, "end")
            entry.insert(0, path)

    def add_item(self) -> None:
        self.sync_items()
        self.items.append(LaunchItem(name=f"Program {len(self.items) + 1}"))
        self.refresh_rows()
        self.set_status("Program added", CYAN)

    def remove_item(self, index: int) -> None:
        if len(self.items) == 1:
            self.items[0] = LaunchItem()
        else:
            self.items.pop(index)
        self.refresh_rows()
        self.save_profile()

    def launch_enabled(self) -> None:
        self.sync_items()
        launched = 0
        failures: list[str] = []
        for item in self.items:
            if not item.enabled or not item.executable.strip():
                continue
            executable = os.path.expandvars(os.path.expanduser(item.executable.strip().strip('"')))
            if not Path(executable).exists():
                failures.append(f"{item.name}: file not found")
                continue
            try:
                command = [executable] + (shlex.split(item.arguments, posix=os.name != "nt") if item.arguments else [])
                cwd = item.working_dir.strip() or str(Path(executable).parent)
                process = subprocess.Popen(command, cwd=cwd)
                self.processes[process.pid] = process
                launched += 1
            except (OSError, ValueError) as exc:
                failures.append(f"{item.name}: {exc}")
        self.save_profile()
        if failures:
            messagebox.showwarning("Some programs could not start", "\n".join(failures))
        self.set_status(f"Launched {launched} program{'s' if launched != 1 else ''}", GREEN if launched else YELLOW)

    def stop_all(self) -> None:
        stopped = 0
        for pid, process in list(self.processes.items()):
            if process.poll() is None:
                try:
                    process.terminate()
                    stopped += 1
                except OSError:
                    pass
            self.processes.pop(pid, None)
        self.set_status(f"Stopped {stopped} program{'s' if stopped != 1 else ''}", PINK)

    def refresh_process_status(self) -> None:
        finished = [pid for pid, process in self.processes.items() if process.poll() is not None]
        for pid in finished:
            self.processes.pop(pid, None)
        if self.processes:
            self.set_status(f"{len(self.processes)} program{'s' if len(self.processes) != 1 else ''} running", GREEN)
        self.after(800, self.refresh_process_status)

    def set_status(self, text: str, color: str) -> None:
        self.status_label.configure(text=text, fg=color)

    def on_close(self) -> None:
        self.sync_items()
        self.save_profile()
        self.stop_all()
        self.destroy()


if __name__ == "__main__":
    NeonLaunchpad().mainloop()
