from __future__ import annotations

from pathlib import Path
import json
import xml.etree.ElementTree as ET

import pygame

from .paths import PathResolver


class AssetManager:
    def __init__(self, resolver: PathResolver):
        self.resolver = resolver
        self.image_cache: dict[str, pygame.Surface] = {}
        self.font_cache: dict[tuple[str, int], pygame.font.Font] = {}
        self.atlas_cache: dict[str, dict[str, pygame.Surface]] = {}
        self.animation_cache: dict[str, dict[str, list[str]]] = {}

    def font(self, size: int, name: str | None = None) -> pygame.font.Font:
        key = (name or "_default", int(size))
        if key not in self.font_cache:
            font_path = None
            if name:
                font_path = self.resolver.resolve(f"fonts/{name}")
            self.font_cache[key] = pygame.font.Font(str(font_path) if font_path else None, size)
        return self.font_cache[key]

    def text(self, value: str, size: int = 24, color=(255, 255, 255), name: str | None = None) -> pygame.Surface:
        return self.font(size, name).render(str(value), True, color)

    def image(self, candidates, size: tuple[int, int] | None = None, label: str = "missing") -> pygame.Surface:
        if isinstance(candidates, (str, Path)):
            candidates = [candidates]
        path = self.resolver.resolve_any(candidates)
        key = str(path or candidates)
        if key not in self.image_cache:
            if path:
                try:
                    surf = pygame.image.load(str(path)).convert_alpha()
                except pygame.error:
                    surf = self.placeholder(size or (180, 180), label=f"bad image\n{path.name}")
            else:
                surf = self.placeholder(size or (180, 180), label=label)
            self.image_cache[key] = surf
        surf = self.image_cache[key]
        if size and surf.get_size() != size:
            return pygame.transform.smoothscale(surf, size)
        return surf.copy()

    def placeholder(self, size=(180, 180), label: str = "missing") -> pygame.Surface:
        w, h = max(8, int(size[0])), max(8, int(size[1]))
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((34, 34, 42, 255))
        pygame.draw.rect(surf, (230, 70, 90), surf.get_rect(), 3)
        pygame.draw.line(surf, (230, 70, 90), (0, 0), (w, h), 2)
        pygame.draw.line(surf, (230, 70, 90), (w, 0), (0, h), 2)
        try:
            font = self.font(max(12, min(22, w // 8)))
            y = 8
            for line in str(label).splitlines()[:4]:
                text = font.render(line[:24], True, (240, 240, 240))
                surf.blit(text, (8, y))
                y += text.get_height() + 2
        except Exception:
            pass
        return surf

    def audio_path(self, candidates) -> Path | None:
        if isinstance(candidates, (str, Path)):
            candidates = [candidates]
        return self.resolver.resolve_any(candidates)

    def load_sparrow_atlas(self, png_path: Path, xml_path: Path) -> dict[str, pygame.Surface]:
        key = f"sparrow:{png_path}:{xml_path}"
        if key in self.atlas_cache:
            return self.atlas_cache[key]
        frames: dict[str, pygame.Surface] = {}
        try:
            sheet = pygame.image.load(str(png_path)).convert_alpha()
            root = ET.parse(str(xml_path)).getroot()
            for node in root.findall(".//SubTexture"):
                name = node.attrib.get("name", "")
                x = int(float(node.attrib.get("x", 0)))
                y = int(float(node.attrib.get("y", 0)))
                w = int(float(node.attrib.get("width", 1)))
                h = int(float(node.attrib.get("height", 1)))
                rect = pygame.Rect(x, y, w, h)
                frames[name] = sheet.subsurface(rect).copy()
        except Exception:
            frames = {}
        self.atlas_cache[key] = frames
        return frames

    def load_animate_atlas(self, folder: Path) -> dict[str, pygame.Surface]:
        key = f"animate:{folder}"
        if key in self.atlas_cache:
            return self.atlas_cache[key]
        frames: dict[str, pygame.Surface] = {}
        try:
            atlas_json = folder / "spritemap1.json"
            if not atlas_json.exists():
                atlas_json = folder / "spritemap.json"
            data = json.loads(atlas_json.read_text(encoding="utf-8-sig"))
            image_name = data.get("ATLAS", {}).get("meta", {}).get("image") or data.get("meta", {}).get("image") or "spritemap1.png"
            image_path = folder / image_name
            if not image_path.exists():
                image_path = folder / "spritemap1.png"
            sheet = pygame.image.load(str(image_path)).convert_alpha()
            sprites = data.get("ATLAS", {}).get("SPRITES") or data.get("SPRITES") or []
            for item in sprites:
                spr = item.get("SPRITE", item)
                name = str(spr.get("name", len(frames)))
                x = int(float(spr.get("x", 0)))
                y = int(float(spr.get("y", 0)))
                w = int(float(spr.get("w", spr.get("width", 1))))
                h = int(float(spr.get("h", spr.get("height", 1))))
                frames[name] = sheet.subsurface(pygame.Rect(x, y, w, h)).copy()
        except Exception:
            frames = {}
        self.atlas_cache[key] = frames
        return frames

    def load_animate_animation_map(self, folder: Path) -> dict[str, list[str]]:
        key = f"anim-map:{folder}"
        if key in self.animation_cache:
            return self.animation_cache[key]
        path = folder / "Animation.json"
        if not path.exists():
            self.animation_cache[key] = {}
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            self.animation_cache[key] = {}
            return {}

        symbols: dict[str, list[str]] = {}
        for sym in data.get("SD", {}).get("S", []):
            name = str(sym.get("SN", ""))
            frames = self._collect_animate_frame_refs(sym)
            if name and frames:
                symbols[name] = frames

        out: dict[str, list[str]] = dict(symbols)
        for layer in data.get("AN", {}).get("TL", {}).get("L", []):
            if not isinstance(layer, dict):
                continue
            for frame in layer.get("FR", []):
                label = str(frame.get("N", ""))
                if not label:
                    continue
                refs: list[str] = []
                start = int(frame.get("I", 0) or 0)
                duration = int(frame.get("DU", 1) or 1)
                for other in data.get("AN", {}).get("TL", {}).get("L", []):
                    for other_frame in other.get("FR", []):
                        idx = int(other_frame.get("I", 0) or 0)
                        if start <= idx < start + duration:
                            for entry in other_frame.get("E", []):
                                si = entry.get("SI") if isinstance(entry, dict) else None
                                if isinstance(si, dict):
                                    refs.extend(symbols.get(str(si.get("SN", "")), []))
                if refs:
                    out[label] = refs

        self.animation_cache[key] = out
        return out

    def _collect_animate_frame_refs(self, node: dict) -> list[str]:
        refs: list[str] = []
        for layer in node.get("TL", {}).get("L", []):
            for frame in layer.get("FR", []):
                repeat = max(1, int(frame.get("DU", 1) or 1))
                frame_refs: list[str] = []
                for entry in frame.get("E", []):
                    if not isinstance(entry, dict):
                        continue
                    asi = entry.get("ASI")
                    si = entry.get("SI")
                    if isinstance(asi, dict) and asi.get("N") is not None:
                        frame_refs.append(str(asi.get("N")))
                    elif isinstance(si, dict) and si.get("FF") is not None:
                        frame_refs.append(str(si.get("FF")))
                for _ in range(repeat):
                    refs.extend(frame_refs)
        seen: set[str] = set()
        compact: list[str] = []
        for ref in refs:
            if ref not in seen:
                compact.append(ref)
                seen.add(ref)
        return compact

    def atlas_for_asset_id(self, asset_id: str) -> dict[str, pygame.Surface]:
        # animate folder first
        for candidate in self.resolver.asset_candidates(asset_id, "image"):
            path = self.resolver.resolve(candidate)
            if path and path.name.lower().startswith("spritemap") and path.parent.exists():
                frames = self.load_animate_atlas(path.parent)
                if frames:
                    return frames

        # sparrow sheet/xml pair
        img_candidates = self.resolver.asset_candidates(asset_id, "image")
        for img_candidate in img_candidates:
            img = self.resolver.resolve(img_candidate)
            if not img or img.suffix.lower() not in (".png", ".jpg", ".jpeg"):
                continue
            xml_candidates = []
            if img.suffix.lower() == ".png":
                xml_candidates.append(str(Path(img_candidate).with_suffix(".xml")))
            xml_candidates.extend(self.resolver.asset_candidates(asset_id, "atlas"))
            xml = self.resolver.resolve_any(xml_candidates)
            if xml and xml.suffix.lower() == ".xml":
                frames = self.load_sparrow_atlas(img, xml)
                if frames:
                    return frames
        return {}

    def animation_frames_for_asset_id(self, asset_id: str) -> dict[str, list[str]]:
        for candidate in self.resolver.asset_candidates(asset_id, "atlas"):
            path = self.resolver.resolve(candidate)
            if path and path.name == "Animation.json":
                return self.load_animate_animation_map(path.parent)
        for candidate in self.resolver.asset_candidates(asset_id, "image"):
            path = self.resolver.resolve(candidate)
            if path and path.parent.exists() and (path.parent / "Animation.json").exists():
                return self.load_animate_animation_map(path.parent)
        return {}

    def asset_image(self, asset_id: str, size=None, label=None) -> pygame.Surface:
        return self.image(self.resolver.asset_candidates(asset_id, "image"), size=size, label=label or asset_id)
