from __future__ import annotations

from pathlib import Path
import itertools
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox

from foxfunkin.core.jsonx import load_json, save_json
from foxfunkin.core.paths import project_root


NODE_DEFAULTS = {
    "Start": {},
    "OnBeat": {},
    "OnStep": {},
    "OnNoteHit": {},
    "ShowText": {"text": "Hello", "duration": 2.0},
    "CameraZoom": {"zoom": 1.05},
    "ScreenShake": {"strength": 6, "duration": 0.25},
    "SetScrollSpeed": {"speed": 1.6},
    "HealthChange": {"delta": 0.1},
    "PlayAnimation": {"target": "bf", "anim": "hey", "force": True},
    "SetVariable": {"name": "flag", "value": True},
    "Branch": {"name": "flag", "op": "==", "value": True},
    "PlaySound": {"path": "shared:confirmMenu", "volume": 0.85},
    "StageProp": {"name": "stageBack", "visible": True, "alpha": 1.0},
    "Wait": {"seconds": 1.0},
}


class VisualProgrammer(tk.Toplevel):
    def __init__(self, master=None, path=None):
        super().__init__(master)
        self.title("FoxFunkin Visual Programmer")
        self.geometry("980x680")
        self.root_path = project_root()
        self.path: Path | None = Path(path) if path else None
        self.nodes: list[dict] = [{"id": "start", "type": "Start", "x": 50, "y": 80, "props": {}}]
        self.links: list[dict] = []
        self.counter = itertools.count(1)
        self.selected_id: str | None = None
        self.drag = None
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
        ttk.Label(top, text="Add node").pack(side="left", padx=(18, 4))
        self.node_type = tk.StringVar(value="ShowText")
        ttk.Combobox(top, textvariable=self.node_type, values=list(NODE_DEFAULTS), width=18).pack(side="left")
        ttk.Button(top, text="Add", command=self.add_node).pack(side="left", padx=3)
        ttk.Button(top, text="Link selected → last", command=self.link_selected_to_last).pack(side="left", padx=12)
        ttk.Button(top, text="Edit Props", command=self.edit_props).pack(side="left", padx=3)
        ttk.Button(top, text="Delete", command=self.delete_selected).pack(side="left", padx=3)

        self.canvas = tk.Canvas(self, bg="#15151f", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.click)
        self.canvas.bind("<B1-Motion>", self.motion)
        self.canvas.bind("<ButtonRelease-1>", self.release)

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=8, pady=6)
        self.status = ttk.Label(bottom, text="Drag nodes. Link selected → last creates a chain.")
        self.status.pack(side="left")

    def open_file(self):
        path = filedialog.askopenfilename(initialdir=self.root_path, filetypes=[("Fox visual graph", "*.fnvgraph.json"), ("JSON", "*.json")])
        if path:
            self.load(Path(path))

    def load(self, path: Path):
        data = load_json(path, default={})
        if not isinstance(data, dict):
            messagebox.showerror("Error", "Invalid graph")
            return
        self.nodes = list(data.get("nodes", []))
        self.links = list(data.get("links", []))
        self.path = path
        self.title(f"FoxFunkin Visual Programmer - {path.name}")
        self.redraw()

    def data(self):
        return {"version": "1.0.0", "nodes": self.nodes, "links": self.links}

    def save_file(self):
        if not self.path:
            return self.save_as()
        save_json(self.path, self.data())
        self.status.configure(text=f"Saved {self.path}")

    def save_as(self):
        path = filedialog.asksaveasfilename(initialdir=self.root_path, defaultextension=".fnvgraph.json", filetypes=[("Fox visual graph", "*.fnvgraph.json"), ("JSON", "*.json")])
        if path:
            self.path = Path(path)
            self.save_file()

    def add_node(self):
        typ = self.node_type.get()
        nid = f"{typ.lower()}_{next(self.counter)}"
        self.nodes.append({"id": nid, "type": typ, "x": 120 + len(self.nodes) * 35, "y": 120 + len(self.nodes) * 22, "props": dict(NODE_DEFAULTS.get(typ, {}))})
        self.selected_id = nid
        self.redraw()

    def node_rect(self, node):
        return (node.get("x", 0), node.get("y", 0), node.get("x", 0) + 150, node.get("y", 0) + 58)

    def hit_node(self, x, y):
        for node in reversed(self.nodes):
            x0, y0, x1, y1 = self.node_rect(node)
            if x0 <= x <= x1 and y0 <= y <= y1:
                return node
        return None

    def click(self, event):
        node = self.hit_node(event.x, event.y)
        if node:
            self.selected_id = node["id"]
            self.drag = (node, event.x - node.get("x", 0), event.y - node.get("y", 0))
        else:
            self.selected_id = None
            self.drag = None
        self.redraw()

    def motion(self, event):
        if self.drag:
            node, dx, dy = self.drag
            node["x"] = event.x - dx
            node["y"] = event.y - dy
            self.redraw()

    def release(self, event):
        self.drag = None

    def link_selected_to_last(self):
        if not self.selected_id or not self.nodes:
            return
        last = self.nodes[-1]["id"]
        if self.selected_id == last and len(self.nodes) >= 2:
            last = self.nodes[-2]["id"]
        self.links.append({"from": self.selected_id, "to": last})
        self.redraw()

    def edit_props(self):
        node = self.selected_node()
        if not node:
            return
        current = node.get("props", {})
        text = simpledialog.askstring("Props JSON-ish", "Edit props as key=value lines", initialvalue="\n".join(f"{k}={v}" for k, v in current.items()))
        if text is None:
            return
        props = {}
        for line in text.splitlines():
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip()
            if v.lower() in ("true", "false"):
                value = v.lower() == "true"
            else:
                try:
                    value = float(v) if "." in v else int(v)
                except ValueError:
                    value = v
            props[k] = value
        node["props"] = props
        self.redraw()

    def selected_node(self):
        for node in self.nodes:
            if node.get("id") == self.selected_id:
                return node
        return None

    def delete_selected(self):
        if not self.selected_id:
            return
        self.nodes = [n for n in self.nodes if n.get("id") != self.selected_id]
        self.links = [l for l in self.links if l.get("from") != self.selected_id and l.get("to") != self.selected_id]
        self.selected_id = None
        self.redraw()

    def redraw(self):
        c = self.canvas
        c.delete("all")
        lookup = {n.get("id"): n for n in self.nodes}
        for link in self.links:
            a = lookup.get(link.get("from"))
            b = lookup.get(link.get("to"))
            if not a or not b:
                continue
            ax0, ay0, ax1, ay1 = self.node_rect(a)
            bx0, by0, bx1, by1 = self.node_rect(b)
            c.create_line(ax1, (ay0 + ay1) / 2, bx0, (by0 + by1) / 2, fill="#ffd45c", width=2, arrow="last")
        for node in self.nodes:
            x0, y0, x1, y1 = self.node_rect(node)
            selected = node.get("id") == self.selected_id
            c.create_rectangle(x0, y0, x1, y1, fill="#2d2d42" if not selected else "#49496b", outline="#ffffff" if selected else "#777799", width=2, tags=node.get("id"))
            c.create_text(x0 + 10, y0 + 12, text=node.get("type"), anchor="w", fill="#ffffff", font=("Arial", 11, "bold"))
            c.create_text(x0 + 10, y0 + 35, text=node.get("id"), anchor="w", fill="#c8c8d8", font=("Arial", 9))
        self.status.configure(text=f"{len(self.nodes)} nodes, {len(self.links)} links • selected {self.selected_id or '-'}")


def main():
    app = tk.Tk()
    app.withdraw()
    win = VisualProgrammer(app)
    win.protocol("WM_DELETE_WINDOW", app.destroy)
    app.mainloop()


if __name__ == "__main__":
    main()
