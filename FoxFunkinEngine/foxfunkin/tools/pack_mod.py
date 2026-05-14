from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

from foxfunkin.core.paths import project_root
from foxfunkin.core.jsonx import load_json


BASE_GAME_SONGS = {
    "tutorial", "bopeebo", "fresh", "dadbattle", "spookeez", "south", "monster",
    "pico", "philly-nice", "blammed", "satin-panties", "high", "milf",
    "cocoa", "eggnog", "winter-horrorland", "senpai", "roses", "thorns",
    "ugh", "guns", "stress", "darnell", "lit-up", "2hot", "blazin",
}


def validate_manifest(mod_root: Path) -> dict:
    manifest = load_json(mod_root / "manifest.json", default={})
    if not isinstance(manifest, dict):
        manifest = {}
    manifest.setdefault("id", mod_root.name)
    manifest.setdefault("title", mod_root.name)
    manifest.setdefault("version", "1.0.0")
    manifest.setdefault("author", "unknown")
    manifest.setdefault("description", "")
    manifest.setdefault("dependencies", [])
    manifest.setdefault("priority", 0)
    manifest.setdefault("entryGraphs", {})
    return manifest


def proprietary_hits(mod_root: Path) -> list[str]:
    hits: list[str] = []
    for p in mod_root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(mod_root).as_posix().lower()
        parts = rel.split("/")
        if len(parts) >= 2 and parts[0] == "songs" and parts[1] in BASE_GAME_SONGS:
            hits.append(rel)
        if "preload/data/songs/" in rel:
            for song in BASE_GAME_SONGS:
                if f"preload/data/songs/{song}/" in rel:
                    hits.append(rel)
                    break
        if parts[0] in {"shared", "week1", "week2", "week3", "week4", "week5", "week6", "week7", "weekend1"}:
            hits.append(rel)
    return sorted(set(hits))


def pack_mod(mod_id: str, output: Path | None = None, allow_proprietary: bool = False) -> Path:
    root = project_root()
    mod_root = root / "mods" / mod_id
    if not mod_root.exists():
        raise FileNotFoundError(f"Mod not found: {mod_root}")
    validate_manifest(mod_root)
    hits = proprietary_hits(mod_root)
    if hits and not allow_proprietary:
        preview = "\n".join(f"  - {h}" for h in hits[:12])
        raise RuntimeError(
            "This mod appears to include base-game FNF asset paths. "
            "Public packages should not redistribute proprietary funkin.assets content.\n"
            + preview
        )
    output = output or (root / "dist" / f"{mod_id}.ffmod.zip")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in mod_root.rglob("*"):
            if p.is_file():
                zf.write(p, p.relative_to(mod_root.parent))
    return output


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("mod_id")
    parser.add_argument("--output")
    parser.add_argument("--allow-proprietary", action="store_true", help="Allow local/private packages with base-game asset paths.")
    args = parser.parse_args(argv)
    out = pack_mod(args.mod_id, Path(args.output) if args.output else None, allow_proprietary=args.allow_proprietary)
    print(out)


if __name__ == "__main__":
    main()
