from __future__ import annotations

from pathlib import Path
import random

import pygame

from foxfunkin.core.jsonx import load_json


class Character:
    def __init__(self, char_id: str, asset_manager, resolver, pos=(0, 0), scale: float = 1.0, flip: bool = False):
        self.id = char_id
        self.assets = asset_manager
        self.resolver = resolver
        self.pos = pygame.Vector2(pos)
        self.scale = scale
        self.flip = flip
        self.name = char_id
        self.asset_path = ""
        self.offsets = [0, 0]
        self.camera_offsets = [0, 0]
        self.flip_x = False
        self.anim_defs: list[dict] = []
        self.frames: dict[str, pygame.Surface] = {}
        self.animations: dict[str, list[str]] = {}
        self.current_anim = "idle"
        self.current_frames: list[str] = []
        self.frame_index = 0
        self.frame_timer = 0.0
        self.fps = 24.0
        self.placeholder_color = (
            random.randint(70, 210),
            random.randint(70, 210),
            random.randint(70, 210),
        )
        self.load()

    def metadata_candidates(self) -> list[str]:
        return [
            f"preload/data/characters/{self.id}.json",
            f"data/characters/{self.id}.json",
            f"characters/{self.id}.json",
        ]

    def load(self) -> None:
        meta_path = self.resolver.resolve_any(self.metadata_candidates())
        data = load_json(meta_path, default={}) if meta_path else {}
        if isinstance(data, dict):
            self.name = str(data.get("name", self.id))
            self.asset_path = str(data.get("assetPath", ""))
            self.offsets = data.get("offsets", [0, 0])
            self.camera_offsets = data.get("cameraOffsets", [0, 0])
            self.flip_x = bool(data.get("flipX", False))
            self.anim_defs = data.get("animations", []) if isinstance(data.get("animations", []), list) else []
            self.current_anim = str(data.get("startingAnimation", "idle"))

        if self.asset_path:
            self.frames = self.assets.atlas_for_asset_id(self.asset_path)

        self.build_animation_map()
        if self.current_anim not in self.animations and self.animations:
            self.current_anim = next(iter(self.animations))
        self.play(self.current_anim, force=True)

    def build_animation_map(self) -> None:
        if not self.frames:
            return

        frame_names = list(self.frames.keys())
        animation_map = self.assets.animation_frames_for_asset_id(self.asset_path) if self.asset_path else {}
        for anim in self.anim_defs:
            if not isinstance(anim, dict):
                continue
            name = str(anim.get("name", "idle"))
            prefix = str(anim.get("prefix", name))
            source_asset = str(anim.get("assetPath", self.asset_path) or self.asset_path)
            if source_asset and source_asset != self.asset_path:
                source_frames = self.assets.atlas_for_asset_id(source_asset)
                source_map = self.assets.animation_frames_for_asset_id(source_asset)
            else:
                source_frames = self.frames
                source_map = animation_map
            source_names = list(source_frames.keys())
            indices = anim.get("frameIndices")
            chosen: list[str] = []
            if isinstance(indices, list):
                for idx in indices:
                    key = str(idx)
                    if key in source_frames:
                        chosen.append(key)
            if not chosen:
                chosen = [fn for fn in source_names if fn.startswith(prefix)]
            if not chosen and source_map:
                for key, refs in source_map.items():
                    if key == prefix or key.lower().startswith(prefix.lower()):
                        chosen = [ref for ref in refs if ref in source_frames]
                        break
            if not chosen:
                chosen = source_names[:min(8, len(source_names))]
            if source_frames is not self.frames:
                # Keep alt animation frames addressable without replacing the default atlas.
                for key in chosen:
                    if key in source_frames:
                        self.frames[f"{source_asset}::{key}"] = source_frames[key]
                chosen = [f"{source_asset}::{key}" for key in chosen if f"{source_asset}::{key}" in self.frames]
            self.animations[name] = chosen

        if "idle" not in self.animations:
            for candidate in ("danceLeft", "danceRight", "idle"):
                if candidate in self.animations:
                    self.animations["idle"] = self.animations[candidate]
                    break
        if not self.animations and frame_names:
            self.animations["idle"] = frame_names[:min(8, len(frame_names))]

    def play(self, anim: str, force: bool = False) -> None:
        if not force and anim == self.current_anim:
            return
        if anim not in self.animations:
            # Common FNF aliases.
            aliases = {
                "singLEFT": ["left", "LEFT", "sing left"],
                "singDOWN": ["down", "DOWN"],
                "singUP": ["up", "UP"],
                "singRIGHT": ["right", "RIGHT"],
                "idle": ["danceLeft", "danceRight"],
            }
            for alt in aliases.get(anim, []):
                if alt in self.animations:
                    anim = alt
                    break
        self.current_anim = anim
        self.current_frames = self.animations.get(anim) or self.animations.get("idle") or []
        self.frame_index = 0
        self.frame_timer = 0.0

    def update(self, dt: float) -> None:
        if not self.current_frames:
            return
        self.frame_timer += dt
        step = 1.0 / self.fps
        while self.frame_timer >= step:
            self.frame_timer -= step
            self.frame_index = (self.frame_index + 1) % len(self.current_frames)

    def surface(self) -> pygame.Surface:
        if self.current_frames:
            key = self.current_frames[self.frame_index % len(self.current_frames)]
            frame = self.frames.get(key)
            if frame:
                surf = frame.copy()
                if self.flip or self.flip_x:
                    surf = pygame.transform.flip(surf, True, False)
                if self.scale != 1.0:
                    w, h = surf.get_size()
                    surf = pygame.transform.smoothscale(surf, (max(1, int(w * self.scale)), max(1, int(h * self.scale))))
                return surf
        return self.placeholder()

    def placeholder(self) -> pygame.Surface:
        surf = pygame.Surface((170, 240), pygame.SRCALPHA)
        color = self.placeholder_color
        pygame.draw.ellipse(surf, (*color, 255), (55, 10, 60, 60))
        pygame.draw.rect(surf, (*color, 230), (38, 75, 94, 110), border_radius=20)
        pygame.draw.line(surf, (255, 255, 255), (52, 105), (10, 155), 8)
        pygame.draw.line(surf, (255, 255, 255), (118, 105), (160, 155), 8)
        pygame.draw.line(surf, (255, 255, 255), (70, 180), (55, 235), 10)
        pygame.draw.line(surf, (255, 255, 255), (100, 180), (115, 235), 10)
        font = pygame.font.Font(None, 26)
        txt = font.render(self.id, True, (255, 255, 255))
        surf.blit(txt, txt.get_rect(center=(85, 210)))
        return surf

    def draw(self, screen: pygame.Surface, camera_offset=(0, 0)) -> None:
        surf = self.surface()
        x = self.pos.x + float(self.offsets[0] if len(self.offsets) > 0 else 0) + camera_offset[0]
        y = self.pos.y + float(self.offsets[1] if len(self.offsets) > 1 else 0) + camera_offset[1]
        rect = surf.get_rect(midbottom=(int(x), int(y)))
        screen.blit(surf, rect)
