from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path
import wave

import pygame

from foxfunkin.core.jsonx import load_json, save_json
from foxfunkin.core.paths import project_root


LANES = ["O-L", "O-D", "O-U", "O-R", "P-L", "P-D", "P-U", "P-R", "EVENT"]


class ChartEditor(tk.Toplevel):
    def __init__(self, master=None, path: str | Path | None = None):
        super().__init__(master)
        self.title("FoxFunkin Chart Editor")
        self.geometry("980x720")
        self.root_path = project_root()
        self.path: Path | None = Path(path) if path else None
        self.chart = {"version": "2.0.0", "scrollSpeed": {"normal": 1.5}, "events": [], "notes": {"normal": []}}
        self.difficulty = tk.StringVar(value="normal")
        self.bpm = tk.DoubleVar(value=120.0)
        self.snap = tk.IntVar(value=250)
        self.zoom = tk.DoubleVar(value=0.18)  # px per ms
        self.offset_y = 0
        self.selected_note = None
        self.audio_path: Path | None = None
        self.wave_cache: list[float] = []
        self.build()
        if self.path and self.path.exists():
            self.load(self.path)
        self.redraw()

    def build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=6)
        ttk.Button(top, text="Open", command=self.open_file).pack(side="left", padx=3)
        ttk.Button(top, text="Save", command=self.save_file).pack(side="left", padx=3)
        ttk.Button(top, text="Save As", command=self.save_as).pack(side="left", padx=3)
        ttk.Button(top, text="Audio", command=self.open_audio).pack(side="left", padx=8)
        ttk.Button(top, text="Play/Stop", command=self.toggle_audio).pack(side="left", padx=3)
        ttk.Button(top, text="Metadata", command=self.edit_metadata).pack(side="left", padx=8)
        ttk.Label(top, text="Difficulty").pack(side="left", padx=(18, 4))
        ttk.Combobox(top, textvariable=self.difficulty, values=["easy", "normal", "hard"], width=10).pack(side="left")
        ttk.Label(top, text="Snap ms").pack(side="left", padx=(18, 4))
        ttk.Entry(top, textvariable=self.snap, width=7).pack(side="left")
        ttk.Label(top, text="Zoom").pack(side="left", padx=(18, 4))
        ttk.Scale(top, variable=self.zoom, from_=0.08, to=0.42, orient="horizontal", command=lambda _=None: self.redraw()).pack(side="left", fill="x", expand=True)

        main = ttk.Frame(self)
        main.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(main, bg="#15151f", highlightthickness=0)
        self.scroll = ttk.Scrollbar(main, orient="vertical", command=self.on_scrollbar)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scroll.pack(side="right", fill="y")
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<MouseWheel>", self.on_wheel)
        self.canvas.bind("<Configure>", lambda e: self.redraw())

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=8, pady=6)
        self.status = ttk.Label(bottom, text="Click to add/remove notes. Right click note = sustain. Event lane adds chart events.")
        self.status.pack(side="left")

    def notes(self):
        notes = self.chart.setdefault("notes", {}).setdefault(self.difficulty.get(), [])
        return notes

    def open_file(self):
        path = filedialog.askopenfilename(
            title="Open chart JSON",
            initialdir=self.root_path,
            filetypes=[("Chart JSON", "*.json"), ("All", "*.*")]
        )
        if path:
            self.load(Path(path))

    def open_audio(self):
        path = filedialog.askopenfilename(
            title="Open Inst audio",
            initialdir=self.root_path,
            filetypes=[("Audio", "*.ogg *.mp3 *.wav"), ("All", "*.*")]
        )
        if not path:
            return
        self.audio_path = Path(path)
        self.wave_cache = self.load_waveform(self.audio_path)
        self.redraw()

    def toggle_audio(self):
        if not self.audio_path:
            self.open_audio()
            if not self.audio_path:
                return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            else:
                pygame.mixer.music.load(str(self.audio_path))
                pygame.mixer.music.play()
        except pygame.error as exc:
            messagebox.showerror("Audio error", str(exc))

    def load_waveform(self, path: Path) -> list[float]:
        if path.suffix.lower() != ".wav":
            return []
        try:
            with wave.open(str(path), "rb") as wf:
                frames = wf.readframes(wf.getnframes())
                width = wf.getsampwidth()
                if width != 2:
                    return []
                samples = memoryview(frames).cast("h")
                step = max(1, len(samples) // 800)
                return [abs(int(samples[i])) / 32768.0 for i in range(0, len(samples), step)]
        except Exception:
            return []

    def edit_metadata(self):
        text = simpledialog.askstring(
            "Song metadata",
            "Edit quick metadata as key=value lines",
            initialvalue="songName=Test Song\nartist=unknown\nbpm=120\nstage=mainStage\nplayer=bf\nopponent=dad\ngirlfriend=gf",
        )
        if text is None:
            return
        self.chart.setdefault("_editorMetadata", {})
        for line in text.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                self.chart["_editorMetadata"][key.strip()] = value.strip()

    def load(self, path: Path):
        data = load_json(path, default=None)
        if not isinstance(data, dict):
            messagebox.showerror("Error", "Invalid chart JSON")
            return
        self.chart = data
        self.path = path
        if "notes" in data and isinstance(data["notes"], dict):
            if self.difficulty.get() not in data["notes"]:
                self.difficulty.set(next(iter(data["notes"]), "normal"))
        self.title(f"FoxFunkin Chart Editor - {path.name}")
        self.redraw()

    def save_file(self):
        if not self.path:
            return self.save_as()
        save_json(self.path, self.chart)
        self.status.configure(text=f"Saved {self.path}")

    def save_as(self):
        path = filedialog.asksaveasfilename(
            title="Save chart JSON",
            initialdir=self.root_path,
            defaultextension=".json",
            filetypes=[("Chart JSON", "*.json")]
        )
        if path:
            self.path = Path(path)
            self.save_file()

    def on_scrollbar(self, *args):
        if args[0] == "moveto":
            frac = float(args[1])
            self.offset_y = int(frac * 90000)
        elif args[0] == "scroll":
            self.offset_y += int(args[1]) * 1500
        self.offset_y = max(0, self.offset_y)
        self.redraw()

    def on_wheel(self, event):
        self.offset_y = max(0, self.offset_y - int(event.delta / 120) * 1000)
        self.redraw()

    def x_to_lane(self, x):
        width = max(1, self.canvas.winfo_width())
        margin = 80
        lane_w = (width - margin * 2) / len(LANES)
        lane = int((x - margin) // lane_w)
        return lane if 0 <= lane < len(LANES) else None

    def y_to_time(self, y):
        height = self.canvas.winfo_height()
        t = self.offset_y + (height - y) / max(0.01, self.zoom.get())
        snap = max(1, int(self.snap.get()))
        return round(t / snap) * snap

    def time_to_y(self, t):
        height = self.canvas.winfo_height()
        return height - (float(t) - self.offset_y) * self.zoom.get()

    def on_click(self, event):
        lane = self.x_to_lane(event.x)
        if lane is None:
            return
        if lane == 8:
            self.add_event_at(self.y_to_time(event.y))
            return
        t = self.y_to_time(event.y)
        notes = self.notes()
        # Toggle note near same lane/time.
        for n in list(notes):
            if int(n.get("d", 4)) == lane and abs(float(n.get("t", 0)) - t) <= max(1, self.snap.get() / 2):
                notes.remove(n)
                self.redraw()
                return
        notes.append({"t": t, "d": lane})
        notes.sort(key=lambda n: float(n.get("t", 0)))
        self.redraw()

    def on_right_click(self, event):
        lane = self.x_to_lane(event.x)
        if lane is None or lane >= 8:
            return
        t = self.y_to_time(event.y)
        for n in self.notes():
            if int(n.get("d", 4)) == lane and abs(float(n.get("t", 0)) - t) <= max(1, self.snap.get() / 2):
                current = float(n.get("l", 0) or 0)
                value = simpledialog.askfloat("Sustain length", "Length in milliseconds", initialvalue=current or float(self.snap.get()))
                if value is not None:
                    if value <= 0:
                        n.pop("l", None)
                    else:
                        n["l"] = round(float(value), 3)
                    self.redraw()
                return

    def add_event_at(self, t):
        event_type = simpledialog.askstring("Event", "Event name", initialvalue="RunGraph")
        if not event_type:
            return
        value = simpledialog.askstring("Event value", "Value/path/JSON-ish", initialvalue="graphs/intro.fnvgraph.json")
        event = {"t": t, "e": event_type, "v": value or ""}
        self.chart.setdefault("events", []).append(event)
        self.chart["events"].sort(key=lambda e: float(e.get("t", 0)))
        self.redraw()

    def redraw(self):
        c = self.canvas
        c.delete("all")
        w = max(1, c.winfo_width())
        h = max(1, c.winfo_height())
        margin = 80
        lane_w = (w - margin * 2) / len(LANES)

        # lanes
        for i in range(len(LANES) + 1):
            x = margin + i * lane_w
            c.create_line(x, 0, x, h, fill="#343448")
        for i, name in enumerate(LANES):
            x = margin + i * lane_w + lane_w / 2
            c.create_text(x, 18, text=name, fill="#ddddff", font=("Arial", 10, "bold"))

        # time grid
        snap = max(1, int(self.snap.get()))
        start = int(self.offset_y // snap) * snap
        end = self.offset_y + h / max(0.01, self.zoom.get())
        t = start
        while t <= end + snap:
            y = self.time_to_y(t)
            if 0 <= y <= h:
                major = (t % 1000 == 0)
                c.create_line(margin, y, w - margin, y, fill="#44445c" if major else "#242436")
                if major:
                    c.create_text(42, y, text=f"{t/1000:.1f}s", fill="#aaaabb")
            t += snap

        if self.wave_cache:
            mid = h // 2
            last = None
            for i, amp in enumerate(self.wave_cache):
                x = margin + (w - margin * 2) * i / max(1, len(self.wave_cache) - 1)
                y = mid - amp * 70
                if last:
                    c.create_line(last[0], last[1], x, y, fill="#315d83")
                    c.create_line(last[0], h - last[1], x, h - y, fill="#315d83")
                last = (x, y)

        # notes
        for n in self.notes():
            lane = int(n.get("d", 4))
            t = float(n.get("t", 0))
            y = self.time_to_y(t)
            if y < -30 or y > h + 30:
                continue
            x0 = margin + lane * lane_w + 6
            x1 = margin + (lane + 1) * lane_w - 6
            color = "#55ddff" if lane >= 4 else "#ff6a9a"
            c.create_rectangle(x0, y - 8, x1, y + 8, fill=color, outline="#ffffff")
            if float(n.get("l", 0) or 0) > 0:
                y2 = self.time_to_y(t + float(n["l"]))
                c.create_rectangle((x0 + x1)/2 - 5, y2, (x0 + x1)/2 + 5, y, fill=color, stipple="gray50")

        for ev in self.chart.get("events", []):
            try:
                t = float(ev.get("t", 0))
            except Exception:
                continue
            y = self.time_to_y(t)
            if y < -20 or y > h + 20:
                continue
            x0 = margin + 8 * lane_w + 6
            x1 = margin + 9 * lane_w - 6
            c.create_rectangle(x0, y - 9, x1, y + 9, fill="#ffd45c", outline="#ffffff")
            c.create_text((x0 + x1) / 2, y, text=str(ev.get("e", "event"))[:12], fill="#1b1b20", font=("Arial", 8, "bold"))

        self.status.configure(text=f"{len(self.notes())} notes • offset {self.offset_y/1000:.1f}s • file {self.path or '(new)'}")


def main():
    app = tk.Tk()
    app.withdraw()
    win = ChartEditor(app)
    win.protocol("WM_DELETE_WINDOW", app.destroy)
    app.mainloop()


if __name__ == "__main__":
    main()
