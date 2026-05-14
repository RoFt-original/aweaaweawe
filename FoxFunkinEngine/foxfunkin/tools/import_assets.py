from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from foxfunkin.core.jsonx import save_json
from foxfunkin.core.paths import project_root
from .asset_validator import validate_assets


EXPECTED_ROOTS = [
    "fonts", "preload", "shared", "songs", "tutorial", "week1", "week2", "week3",
    "week4", "week5", "week6", "week7", "weekend1", "videos", "exclude",
]


LIKELY_ASSET_CONTAINERS = [
    Path("assets"),
    Path("export/release/windows/bin/assets"),
    Path("export/release/macos/bin/assets"),
    Path("export/release/linux/bin/assets"),
]


def find_asset_root(source: Path) -> Path:
    """Accept either funkin.assets root, an assets/ folder, or a built FNF folder."""
    source = source.resolve()
    if any((source / name).exists() for name in EXPECTED_ROOTS):
        return source
    for rel in LIKELY_ASSET_CONTAINERS:
        candidate = source / rel
        if candidate.exists() and any((candidate / name).exists() for name in EXPECTED_ROOTS):
            return candidate
    for candidate in source.rglob("preload"):
        parent = candidate.parent
        if (parent / "shared").exists() or (parent / "songs").exists():
            return parent
    raise FileNotFoundError(
        "Could not find an FNF assets root. Point import_assets.bat at a folder "
        "that contains preload/, shared/, songs/, week1/, etc."
    )


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def import_assets(source: Path, root: Path | None = None) -> list[str]:
    root = root or project_root()
    source = find_asset_root(source)
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for name in EXPECTED_ROOTS:
        src = source / name
        if src.exists():
            copy_tree(src, data_dir / name)
            copied.append(name)
    save_json(data_dir / ".asset_source.local.json", {
        "source": str(source),
        "copied": copied,
        "note": "Local import only. Do not commit third-party/original game assets unless you own the rights.",
    })
    return copied


def main(argv=None):
    parser = argparse.ArgumentParser(description="Import a local FNF-compatible assets folder into data/.")
    parser.add_argument("source", help="Path to local assets folder or a folder containing assets/")
    args = parser.parse_args(argv)
    copied = import_assets(Path(args.source))
    print("Copied: " + (", ".join(copied) if copied else "nothing"))
    print()
    validate_assets(project_root())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
