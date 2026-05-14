from __future__ import annotations

from pathlib import Path
from foxfunkin.core.paths import project_root
from foxfunkin.core.jsonx import load_json
from .pack_mod import proprietary_hits


def validate_assets(root: Path | None = None, return_lines: bool = False):
    root = root or project_root()
    data = root / "data"
    lines: list[str] = []

    def ok(msg): lines.append("[OK] " + msg)
    def warn(msg): lines.append("[WARN] " + msg)
    def info(msg): lines.append("[INFO] " + msg)

    info(f"Root: {root}")
    if not data.exists():
        warn("data/ folder is missing")
    else:
        ok("data/ folder exists")

    expected = ["preload", "shared", "songs"]
    for name in expected:
        p = data / name
        if p.exists():
            ok(f"data/{name}/ found")
        else:
            warn(f"data/{name}/ missing")

    song_meta = list(data.glob("preload/data/songs/*/*-metadata.json"))
    song_charts = list(data.glob("preload/data/songs/*/*-chart.json"))
    audio_inst = list(data.glob("songs/*/Inst.*"))
    chars = list(data.glob("preload/data/characters/*.json"))
    stages = list(data.glob("preload/data/stages/*.json"))
    shared_images = list(data.glob("shared/images/**/*.*"))

    info(f"Song metadata: {len(song_meta)}")
    info(f"Song charts: {len(song_charts)}")
    info(f"Instrumentals: {len(audio_inst)}")
    info(f"Characters: {len(chars)}")
    info(f"Stages: {len(stages)}")
    info(f"Shared image files: {len(shared_images)}")

    if song_meta and song_charts:
        ok("FNF v2 song metadata/charts detected")
    elif audio_inst:
        warn("Audio found, but chart metadata is missing or incomplete")
    else:
        warn("No external songs detected. Example mod can still run.")

    # Basic missing audio/chart report.
    meta_ids = {p.parent.name for p in song_meta}
    chart_ids = {p.parent.name for p in song_charts}
    audio_ids = {p.parent.name for p in audio_inst}
    for song_id in sorted((meta_ids | chart_ids | audio_ids))[:50]:
        missing = []
        if song_id not in meta_ids: missing.append("metadata")
        if song_id not in chart_ids: missing.append("chart")
        if song_id not in audio_ids: missing.append("Inst")
        if missing:
            warn(f"{song_id}: missing {', '.join(missing)}")
    if len(meta_ids | chart_ids | audio_ids) > 50:
        info("Report truncated to first 50 songs.")

    mods_dir = root / "mods"
    if mods_dir.exists():
        for mod_root in sorted(p for p in mods_dir.iterdir() if p.is_dir()):
            manifest = load_json(mod_root / "manifest.json", default={})
            if not isinstance(manifest, dict):
                warn(f"mod {mod_root.name}: missing or invalid manifest.json")
                continue
            for key in ("id", "title", "version", "author", "description", "dependencies", "priority", "entryGraphs"):
                if key not in manifest:
                    warn(f"mod {mod_root.name}: manifest missing {key}")
            hits = proprietary_hits(mod_root)
            if hits:
                warn(f"mod {mod_root.name}: contains base-game-like asset paths; keep private unless you own replacements")

    if return_lines:
        return lines
    print("\n".join(lines))
    return None


def main():
    validate_assets()


if __name__ == "__main__":
    main()
