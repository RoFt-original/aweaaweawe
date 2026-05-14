from __future__ import annotations

import pygame

from foxfunkin.core.jsonx import load_json


class Stage:
    def __init__(self, stage_id: str, asset_manager, resolver):
        self.id = stage_id or "mainStage"
        self.assets = asset_manager
        self.resolver = resolver
        self.name = self.id
        self.props = []
        self.directory = ""
        self.characters: dict[str, dict] = {}
        self.camera_zoom = 1.0
        self.load()

    def load(self):
        path = self.resolver.resolve_any([
            f"preload/data/stages/{self.id}.json",
            f"data/stages/{self.id}.json",
            f"stages/{self.id}.json",
        ])
        data = load_json(path, default={}) if path else {}
        if isinstance(data, dict):
            self.name = str(data.get("name", self.id))
            self.directory = str(data.get("directory", "") or "")
            self.camera_zoom = float(data.get("cameraZoom", 1.0) or 1.0)
            self.characters = data.get("characters", {}) if isinstance(data.get("characters", {}), dict) else {}
            props = data.get("props", [])
            if isinstance(props, list):
                self.props = sorted(props, key=lambda p: int(p.get("zIndex", 0) or 0) if isinstance(p, dict) else 0)

    def character_position(self, name: str, fallback: tuple[float, float]) -> tuple[float, float]:
        data = self.characters.get(name, {})
        pos = data.get("position") if isinstance(data, dict) else None
        if isinstance(pos, list) and len(pos) >= 2:
            return float(pos[0]), float(pos[1])
        return fallback

    def character_z(self, name: str, fallback: int) -> int:
        data = self.characters.get(name, {})
        if isinstance(data, dict):
            try:
                return int(data.get("zIndex", fallback))
            except Exception:
                return fallback
        return fallback

    def resolve_stage_asset(self, asset: str) -> str:
        asset = str(asset).strip()
        if not asset:
            return asset
        if ":" in asset or not self.directory:
            return asset
        return f"{self.directory}:{asset}"

    def set_prop(self, name: str, **values) -> bool:
        for prop in self.props:
            if isinstance(prop, dict) and prop.get("name") == name:
                prop.update(values)
                return True
        return False

    def draw(self, screen: pygame.Surface, song_pos: float = 0.0):
        w, h = screen.get_size()
        # Fallback stage: intentionally original, no FNF assets embedded.
        screen.fill((18, 18, 26))
        top = pygame.Rect(0, 0, w, int(h * 0.58))
        bottom = pygame.Rect(0, int(h * 0.58), w, int(h * 0.42))
        pygame.draw.rect(screen, (34, 32, 48), top)
        pygame.draw.rect(screen, (48, 42, 54), bottom)
        pygame.draw.circle(screen, (80, 74, 105), (int(w * 0.5), int(h * 0.25)), int(w * 0.12), 0)
        pygame.draw.rect(screen, (72, 58, 72), (0, int(h * 0.58), w, 12))
        for i in range(0, w, 120):
            pygame.draw.line(screen, (64, 56, 68), (i, int(h * 0.58)), (i - 90, h), 2)

        # Optional prop drawing for simple custom stages.
        for prop in self.props:
            if not isinstance(prop, dict):
                continue
            asset = prop.get("assetPath") or prop.get("asset") or ""
            if not asset:
                continue
            pos = prop.get("position", None)
            if isinstance(pos, list) and len(pos) >= 2:
                x = int(float(pos[0]) + w * 0.5)
                y = int(float(pos[1]) + h * 0.15)
            else:
                x = int(prop.get("x", w // 2))
                y = int(prop.get("y", h // 2))
            scale_raw = prop.get("scale", 1.0)
            if isinstance(scale_raw, list):
                sx = float(scale_raw[0] if scale_raw else 1.0)
                sy = float(scale_raw[1] if len(scale_raw) > 1 else sx)
            else:
                sx = sy = float(scale_raw or 1.0)
            img = self.assets.asset_image(self.resolve_stage_asset(str(asset)), label=str(asset))
            alpha = int(float(prop.get("alpha", 1.0) or 1.0) * 255)
            visible = bool(prop.get("visible", True))
            if not visible:
                continue
            if sx != 1.0 or sy != 1.0:
                iw, ih = img.get_size()
                img = pygame.transform.smoothscale(img, (max(1, int(iw * sx)), max(1, int(ih * sy))))
            if alpha < 255:
                img.set_alpha(alpha)
            scroll = prop.get("scroll", [1, 1])
            if isinstance(scroll, list) and len(scroll) >= 2:
                x += int((float(scroll[0]) - 1.0) * 40)
                y += int((float(scroll[1]) - 1.0) * 25)
            screen.blit(img, img.get_rect(center=(x, y)))
