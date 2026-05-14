from __future__ import annotations


class EventDispatcher:
    def __init__(self, context):
        self.context = context

    def dispatch(self, event: dict) -> None:
        e = str(event.get("e", event.get("event", "")))
        v = event.get("v", event.get("value", None))
        ctx = self.context

        if e == "FocusCamera":
            try:
                ctx.camera.set_focus(int(v))
            except Exception:
                pass
        elif e == "PlayAnimation":
            if isinstance(v, dict):
                ctx.play_character_animation(str(v.get("target", "bf")), str(v.get("anim", "idle")), bool(v.get("force", True)))
        elif e == "CameraZoom":
            try:
                ctx.camera.target_zoom = float(v if not isinstance(v, dict) else v.get("zoom", 1.05))
            except Exception:
                pass
        elif e == "ScreenShake":
            if isinstance(v, dict):
                ctx.camera.shake(float(v.get("strength", 8)), float(v.get("duration", 0.25)))
            else:
                ctx.camera.shake(8, 0.25)
        elif e == "SetScrollSpeed":
            try:
                ctx.scroll_speed = float(v if not isinstance(v, dict) else v.get("speed", ctx.scroll_speed))
            except Exception:
                pass
        elif e == "SpawnText":
            if isinstance(v, dict):
                ctx.spawn_text(str(v.get("text", "")), float(v.get("duration", 2.0)))
            else:
                ctx.spawn_text(str(v), 2.0)
        elif e == "HealthChange":
            try:
                delta = float(v if not isinstance(v, dict) else v.get("delta", 0))
                ctx.score_state.health = max(0.0, min(2.0, ctx.score_state.health + delta))
            except Exception:
                pass
        elif e == "RunGraph":
            graph_ref = str(v if not isinstance(v, dict) else v.get("path", ""))
            if graph_ref:
                ctx.graph_executor.run(graph_ref, ctx)
        elif e == "PlaySound":
            path = str(v if not isinstance(v, dict) else v.get("path", ""))
            volume = None if not isinstance(v, dict) else v.get("volume")
            if path:
                p = ctx.app.resolver.resolve(path) or ctx.app.resolver.resolve_any(ctx.app.resolver.asset_candidates(path, "sound"))
                ctx.audio.play_sound(p, float(volume) if volume is not None else None)
        elif e == "StageProp":
            if isinstance(v, dict):
                name = str(v.get("name", ""))
                values = {k: v[k] for k in ("visible", "alpha", "x", "y", "scale") if k in v}
                if name:
                    ctx.stage.set_prop(name, **values)
        else:
            if e:
                ctx.toast.push(f"Unhandled event: {e}")
