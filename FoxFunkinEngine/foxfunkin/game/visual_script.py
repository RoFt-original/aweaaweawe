from __future__ import annotations

from pathlib import Path
from typing import Any

from foxfunkin.core.jsonx import load_json


class VisualGraphExecutor:
    def __init__(self, resolver):
        self.resolver = resolver
        self.active: list[dict[str, Any]] = []

    def load_graph(self, graph_ref: str | Path) -> dict[str, Any] | None:
        p = self.resolver.resolve(graph_ref)
        if not p:
            p = self.resolver.resolve(f"graphs/{graph_ref}")
        if not p:
            return None
        data = load_json(p, default=None)
        return data if isinstance(data, dict) else None

    def run(self, graph_ref: str | Path, context, entry_type: str = "Start", payload: dict[str, Any] | None = None) -> None:
        graph = self.load_graph(graph_ref)
        if not graph:
            context.toast.push(f"Graph not found: {graph_ref}")
            return

        nodes = {str(n.get("id")): n for n in graph.get("nodes", []) if isinstance(n, dict)}
        links = graph.get("links", [])
        next_map: dict[tuple[str, str], str] = {}
        for link in links:
            if isinstance(link, dict):
                port = str(link.get("fromPort", link.get("port", "next")))
                next_map[(str(link.get("from")), port)] = str(link.get("to"))

        start_id = None
        for nid, node in nodes.items():
            if node.get("type") == entry_type:
                start_id = nid
                break
        if not start_id and entry_type != "Start":
            for nid, node in nodes.items():
                if node.get("type") == "Start":
                    start_id = nid
                    break
        if not start_id and nodes:
            start_id = next(iter(nodes))

        safety = 0
        current = start_id
        while current and current in nodes and safety < 128:
            safety += 1
            node = nodes[current]
            port = self.execute_node(node, context, payload or {})
            current = next_map.get((current, port)) or next_map.get((current, "next"))

    def execute_node(self, node: dict[str, Any], context, payload: dict[str, Any] | None = None) -> str:
        typ = node.get("type", "")
        props = node.get("props", {})
        payload = payload or {}
        if typ in ("Start", "OnBeat", "OnStep", "OnNoteHit"):
            pass
        elif typ == "ShowText":
            context.spawn_text(str(props.get("text", "")), float(props.get("duration", 2.0)))
        elif typ == "CameraZoom":
            context.camera.target_zoom = float(props.get("zoom", 1.05))
        elif typ == "ScreenShake":
            context.camera.shake(float(props.get("strength", 8)), float(props.get("duration", 0.25)))
        elif typ == "SetScrollSpeed":
            context.scroll_speed = float(props.get("speed", context.scroll_speed))
        elif typ == "HealthChange":
            context.score_state.health = max(0.0, min(2.0, context.score_state.health + float(props.get("delta", 0))))
        elif typ == "PlayAnimation":
            target = str(props.get("target", "bf"))
            anim = str(props.get("anim", "idle"))
            context.play_character_animation(target, anim, force=bool(props.get("force", True)))
        elif typ == "SetVariable":
            name = str(props.get("name", "flag"))
            value = props.get("value", True)
            context.script_variables[name] = self._resolve_value(value, context, payload)
        elif typ == "Branch":
            name = str(props.get("name", "flag"))
            left = context.script_variables.get(name, payload.get(name))
            right = self._resolve_value(props.get("value", True), context, payload)
            op = str(props.get("op", "=="))
            return "true" if self._compare(left, right, op) else "false"
        elif typ == "PlaySound":
            path = str(props.get("path", ""))
            volume = props.get("volume", None)
            if path and getattr(context, "audio", None):
                candidates = context.app.resolver.asset_candidates(path, "sound")
                p = context.app.resolver.resolve(path) or context.app.resolver.resolve_any(candidates)
                context.audio.play_sound(p, float(volume) if volume is not None else None)
        elif typ == "StageProp":
            name = str(props.get("name", ""))
            values = {}
            for key in ("visible", "alpha", "x", "y", "scale"):
                if key in props:
                    values[key] = props[key]
            if name and hasattr(context.stage, "set_prop"):
                context.stage.set_prop(name, **values)
        elif typ == "Wait":
            # Wait is a design-time node; runtime chart timing controls when graphs fire.
            pass
        return "next"

    def _resolve_value(self, value: Any, context, payload: dict[str, Any]) -> Any:
        if isinstance(value, str) and value.startswith("$"):
            name = value[1:]
            return payload.get(name, context.script_variables.get(name))
        return value

    def _compare(self, left: Any, right: Any, op: str) -> bool:
        try:
            lf = float(left)
            rf = float(right)
            if op == ">":
                return lf > rf
            if op == ">=":
                return lf >= rf
            if op == "<":
                return lf < rf
            if op == "<=":
                return lf <= rf
        except Exception:
            pass
        if op in ("!=", "not"):
            return left != right
        return left == right
