from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


class PathResolver:
    """Overlay resolver.

    Search order:
    1. enabled mod's assets/
    2. enabled mod root
    3. data/
    """

    def __init__(self, root: Path, config: dict):
        self.root = Path(root)
        self.config = config
        self.data_dir = self.root / "data"
        self.mods_dir = self.root / "mods"
        self.refresh()

    def refresh(self) -> None:
        self.enabled_mods = list(self.config.get("mods", {}).get("enabled", []))
        self.roots: list[Path] = []
        for mod_id in self.enabled_mods:
            mod_root = self.mods_dir / mod_id
            if mod_root.exists():
                self.roots.append(mod_root / "assets")
                self.roots.append(mod_root)
        self.roots.append(self.data_dir)

    def rel(self, p: str | Path) -> Path:
        p = Path(str(p).replace("\\", "/"))
        if p.is_absolute():
            return p
        return p

    def resolve(self, rel_path: str | Path) -> Path | None:
        rel = self.rel(rel_path)
        if rel.is_absolute():
            return rel if rel.exists() else None
        for base in self.roots:
            p = base / rel
            if p.exists():
                return p
        return None

    def resolve_any(self, candidates: Iterable[str | Path]) -> Path | None:
        for candidate in candidates:
            p = self.resolve(candidate)
            if p:
                return p
        return None

    def glob_all(self, pattern: str) -> list[Path]:
        found: list[Path] = []
        seen: set[str] = set()
        for base in self.roots:
            if not base.exists():
                continue
            for p in base.glob(pattern):
                key = str(p.resolve()).lower()
                if key not in seen:
                    found.append(p)
                    seen.add(key)
        return found

    def list_mods(self) -> list[dict]:
        from .jsonx import load_json

        mods: list[dict] = []
        if not self.mods_dir.exists():
            return mods
        for folder in sorted(self.mods_dir.iterdir()):
            if not folder.is_dir():
                continue
            manifest_path = folder / "manifest.json"
            manifest = load_json(manifest_path, default={})
            if not isinstance(manifest, dict):
                manifest = {}
            manifest.setdefault("id", folder.name)
            manifest.setdefault("title", folder.name)
            manifest.setdefault("version", "0.0.0")
            manifest.setdefault("author", "unknown")
            manifest.setdefault("description", "")
            manifest.setdefault("dependencies", [])
            manifest.setdefault("priority", 0)
            manifest.setdefault("entryGraphs", {})
            manifest["_path"] = str(folder)
            manifest["_enabled"] = folder.name in self.enabled_mods
            mods.append(manifest)
        return sorted(mods, key=lambda m: int(m.get("priority", 0) or 0), reverse=True)

    def asset_candidates(self, asset_id: str, kind: str = "image") -> list[str]:
        """Expand FNF-ish asset IDs.

        Examples:
        - shared:characters/gf -> shared/images/characters/gf/...
        - freeplay/albumRoll/volume1 -> shared/images/freeplay/albumRoll/volume1.png
        """
        asset_id = str(asset_id).strip()
        if not asset_id:
            return []
        library = "shared"
        path = asset_id
        if ":" in asset_id:
            library, path = asset_id.split(":", 1)

        path = path.replace("\\", "/").strip("/")
        candidates: list[str] = []
        library_roots = [library]
        if library == "default":
            library_roots = ["preload", "shared"]

        if kind == "image":
            for root in library_roots:
                candidates.extend([
                    f"{root}/images/{path}.png",
                    f"{root}/images/{path}.jpg",
                    f"{root}/images/{path}.jpeg",
                    f"{root}/images/{path}/spritemap1.png",
                    f"{root}/images/{path}/spritemap.png",
                    f"{root}/images/{path}/atlas.png",
                ])
            candidates.extend([
                f"shared/images/{path}.png",
                f"shared/images/{path}/spritemap1.png",
                f"preload/images/{path}.png",
            ])
        elif kind == "atlas":
            for root in library_roots:
                candidates.extend([
                    f"{root}/images/{path}.xml",
                    f"{root}/images/{path}/spritemap1.json",
                    f"{root}/images/{path}/Animation.json",
                ])
            candidates.extend([
                f"shared/images/{path}.xml",
                f"shared/images/{path}/spritemap1.json",
                f"shared/images/{path}/Animation.json",
            ])
        elif kind == "sound":
            for ext in ("ogg", "mp3", "wav"):
                for root in library_roots:
                    candidates.append(f"{root}/sounds/{path}.{ext}")
                candidates.extend([
                    f"shared/sounds/{path}.{ext}",
                    f"preload/sounds/{path}.{ext}",
                ])
        elif kind == "music":
            for ext in ("ogg", "mp3", "wav"):
                for root in library_roots:
                    candidates.append(f"{root}/music/{path}.{ext}")
                candidates.extend([
                    f"shared/music/{path}.{ext}",
                    f"preload/music/{path}.{ext}",
                    f"songs/{path}.{ext}",
                ])
        return candidates

    def song_file_candidates(self, song_id: str, stem: str, variation: str | None = None) -> list[str]:
        exts = ("ogg", "mp3", "wav")
        out: list[str] = []
        stems = [stem]
        if variation:
            stems.insert(0, f"{stem}-{variation}")
        for ext in exts:
            for candidate_stem in stems:
                out.extend([
                    f"songs/{song_id}/{candidate_stem}.{ext}",
                    f"shared/songs/{song_id}/{candidate_stem}.{ext}",
                    f"preload/songs/{song_id}/{candidate_stem}.{ext}",
                ])
        return out

    def chart_candidates(self, song_id: str, variation: str | None = None) -> list[str]:
        names = [f"{song_id}-chart.json"]
        if variation:
            names.insert(0, f"{song_id}-chart-{variation}.json")
        out: list[str] = []
        for name in names:
            out.extend([
                f"preload/data/songs/{song_id}/{name}",
                f"data/songs/{song_id}/{name}",
                f"songs/{song_id}/{name}",
            ])
        out.extend([
            f"preload/data/songs/{song_id}/{song_id}-chart.json",
            f"data/songs/{song_id}/{song_id}-chart.json",
            f"songs/{song_id}/{song_id}-chart.json",
            f"charts/{song_id}.json",
            f"charts/{song_id}/{song_id}.json",
        ])
        return out

    def metadata_candidates(self, song_id: str, variation: str | None = None) -> list[str]:
        names = [f"{song_id}-metadata.json", "metadata.json"]
        if variation:
            names.insert(0, f"{song_id}-metadata-{variation}.json")
        out: list[str] = []
        for name in names:
            out.extend([
                f"preload/data/songs/{song_id}/{name}",
                f"data/songs/{song_id}/{name}",
                f"songs/{song_id}/{name}",
            ])
        out.extend([
            f"preload/data/songs/{song_id}/{song_id}-metadata.json",
            f"data/songs/{song_id}/{song_id}-metadata.json",
            f"songs/{song_id}/{song_id}-metadata.json",
            f"songs/{song_id}/metadata.json",
        ])
        return out
