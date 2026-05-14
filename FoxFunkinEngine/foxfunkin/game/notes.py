from __future__ import annotations

import pygame

from foxfunkin.core.jsonx import load_json


LANE_NAMES = ("LEFT", "DOWN", "UP", "RIGHT")
DEFAULT_LANE_KEYS = ("D", "F", "J", "K")
LANE_COLORS = ((210, 70, 170), (70, 210, 245), (80, 235, 125), (245, 75, 85))


def make_arrow(size: int, lane: int, receptor: bool = False) -> pygame.Surface:
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    color = LANE_COLORS[lane % 4]
    outline = (245, 250, 255) if receptor else color
    fill_alpha = 95 if receptor else 242
    fill = (color[0], color[1], color[2], fill_alpha)

    c = size // 2
    pad = size // 6
    if lane == 0:
        pts = [(pad, c), (size - pad, pad), (size - pad, size - pad), (pad, c)]
    elif lane == 1:
        pts = [(c, size - pad), (pad, pad), (size - pad, pad), (c, size - pad)]
    elif lane == 2:
        pts = [(c, pad), (pad, size - pad), (size - pad, size - pad), (c, pad)]
    else:
        pts = [(size - pad, c), (pad, pad), (pad, size - pad), (size - pad, c)]

    pygame.draw.polygon(surf, (color[0], color[1], color[2], 76), pts)
    pygame.draw.polygon(surf, fill, pts)
    pygame.draw.polygon(surf, outline, pts, 6 if receptor else 3)
    if not receptor:
        inner = [(int((x + c) / 2), int((y + c) / 2)) for x, y in pts[:-1]]
        pygame.draw.polygon(surf, (255, 255, 255, 92), inner, 2)
    else:
        pygame.draw.circle(surf, outline, (c, c), max(3, size // 12), 2)
    return surf


class NoteRenderer:
    def __init__(self, asset_manager, resolver=None, style_id: str = "funkin", size: int = 64):
        self.assets = asset_manager
        self.resolver = resolver
        self.style_id = style_id or "funkin"
        self.size = size
        self.note_surfaces = [make_arrow(size, i, False) for i in range(4)]
        self.receptor_surfaces = [make_arrow(size, i, True) for i in range(4)]
        self.load_style()

    def load_style(self) -> None:
        if not self.resolver:
            return
        path = self.resolver.resolve_any([
            f"preload/data/notestyles/{self.style_id}.json",
            f"data/notestyles/{self.style_id}.json",
            f"notestyles/{self.style_id}.json",
        ])
        data = load_json(path, default={}) if path else {}
        if not isinstance(data, dict):
            return
        assets = data.get("assets", {})
        note_data = assets.get("note", {}) if isinstance(assets, dict) else {}
        strum_data = assets.get("noteStrumline", {}) if isinstance(assets, dict) else {}
        notes = self._surfaces_from_style(note_data, ["left", "down", "up", "right"], receptor=False)
        receptors = self._surfaces_from_style(strum_data, ["leftStatic", "downStatic", "upStatic", "rightStatic"], receptor=True)
        if all(notes):
            self.note_surfaces = notes
        if all(receptors):
            self.receptor_surfaces = receptors

    def _surfaces_from_style(self, spec: dict, keys: list[str], receptor: bool) -> list[pygame.Surface]:
        out: list[pygame.Surface] = []
        if not isinstance(spec, dict):
            return out
        asset_path = str(spec.get("assetPath", "") or "")
        frames = self.assets.atlas_for_asset_id(asset_path) if asset_path else {}
        scale = float(spec.get("scale", 1.0) or 1.0)
        data = spec.get("data", {}) if isinstance(spec.get("data", {}), dict) else {}
        for lane, key in enumerate(keys):
            item = data.get(key, {})
            prefix = str(item.get("prefix", "") if isinstance(item, dict) else "")
            frame = self._frame_by_prefix(frames, prefix)
            if not frame:
                out.append(make_arrow(self.size, lane, receptor))
                continue
            surf = frame.copy()
            if scale != 1.0:
                w, h = surf.get_size()
                surf = pygame.transform.smoothscale(surf, (max(1, int(w * scale)), max(1, int(h * scale))))
            if surf.get_width() > self.size * 2 or surf.get_height() > self.size * 2:
                ratio = min((self.size * 1.35) / surf.get_width(), (self.size * 1.35) / surf.get_height())
                surf = pygame.transform.smoothscale(surf, (max(1, int(surf.get_width() * ratio)), max(1, int(surf.get_height() * ratio))))
            out.append(surf)
        return out

    def _frame_by_prefix(self, frames: dict[str, pygame.Surface], prefix: str) -> pygame.Surface | None:
        if not frames:
            return None
        if prefix:
            for name, frame in frames.items():
                if name.startswith(prefix):
                    return frame
        return next(iter(frames.values()), None)

    def draw_receptors(
        self,
        screen: pygame.Surface,
        xs: list[int],
        y: int,
        font=None,
        labels: tuple[str, ...] | None = None,
        active: set[int] | None = None,
        flashes: dict[int, float] | None = None,
        show_labels: bool = True,
        alpha: int = 255,
    ) -> None:
        labels = labels or DEFAULT_LANE_KEYS
        active = active or set()
        flashes = flashes or {}
        for lane, x in enumerate(xs):
            color = LANE_COLORS[lane]
            flash = max(0.0, min(1.0, float(flashes.get(lane, 0.0))))
            pressed = lane in active or flash > 0.0
            scale = 1.0 + (0.16 if pressed else 0.0) + flash * 0.10
            glow_alpha = int((70 if pressed else 22) + flash * 120)
            glow = pygame.Surface((self.size * 3, self.size * 3), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*color, glow_alpha), (self.size * 3 // 2, self.size * 3 // 2), int(self.size * (0.72 + flash * 0.35)))
            screen.blit(glow, glow.get_rect(center=(x, y)))

            img = self.receptor_surfaces[lane].copy()
            img.set_alpha(alpha)
            if scale != 1.0:
                iw, ih = img.get_size()
                img = pygame.transform.smoothscale(img, (max(1, int(iw * scale)), max(1, int(ih * scale))))
            screen.blit(img, img.get_rect(center=(x, y)))

            if show_labels and font:
                text = labels[lane] if lane < len(labels) else DEFAULT_LANE_KEYS[lane]
                color_text = (255, 250, 170) if pressed else (225, 225, 235)
                label = font.render(text, True, color_text)
                shadow = font.render(text, True, (0, 0, 0))
                rect = label.get_rect(center=(x, y + self.size // 2 + 17))
                screen.blit(shadow, rect.move(2, 2))
                screen.blit(label, rect)

    def draw_note(self, screen: pygame.Surface, lane: int, x: int, y: int, alpha: int = 255, sustain_px: int = 0, downscroll: bool = False, kind: str = "", font=None) -> None:
        img = self.note_surfaces[lane].copy()
        img.set_alpha(alpha)
        color = LANE_COLORS[lane]
        if sustain_px > 4:
            rect_w = max(12, self.size // 4)
            if downscroll:
                rect = pygame.Rect(x - rect_w // 2, y - sustain_px, rect_w, sustain_px)
            else:
                rect = pygame.Rect(x - rect_w // 2, y, rect_w, sustain_px)
            pygame.draw.rect(screen, (*color, 155), rect, border_radius=rect_w // 2)
            pygame.draw.rect(screen, (255, 255, 255, 82), rect.inflate(4, 0), 2, border_radius=rect_w // 2)
        if alpha >= 220:
            glow = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*color, 48), (self.size, self.size), self.size // 2 + 18)
            screen.blit(glow, glow.get_rect(center=(x, y)))
        screen.blit(img, img.get_rect(center=(x, y)))
        if kind and font:
            label = font.render(kind[:10], True, (255, 245, 180))
            screen.blit(label, label.get_rect(center=(x, y - self.size // 2 - 9)))

    def draw_splash(self, screen: pygame.Surface, lane: int, x: int, y: int, life: float) -> None:
        life = max(0.0, min(1.0, life))
        color = LANE_COLORS[lane]
        surf = pygame.Surface((self.size * 3, self.size * 3), pygame.SRCALPHA)
        c = self.size * 3 // 2
        radius = int(self.size * (0.28 + (1.0 - life) * 0.85))
        alpha = int(190 * life)
        pygame.draw.circle(surf, (*color, alpha), (c, c), radius, 5)
        pygame.draw.circle(surf, (255, 255, 255, int(alpha * 0.65)), (c, c), max(4, radius // 3), 2)
        screen.blit(surf, surf.get_rect(center=(x, y)))
