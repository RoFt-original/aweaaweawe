from __future__ import annotations

from pathlib import Path
from typing import Any

from .jsonx import load_json, save_json, merge_dict


DEFAULT_CONFIG: dict[str, Any] = {
    "window": {
        "width": 1280,
        "height": 720,
        "fps": 120,
        "fullscreen": False,
        "caption": "FoxFunkin Engine",
    },
    "gameplay": {
        "downscroll": False,
        "safe_zone_ms": 166,
        "sustain_release_grace_ms": 120,
        "input_offset_ms": 0,
        "audio_offset_ms": 0,
        "scroll_speed_multiplier": 1.0,
        "ghost_tapping": True,
        "botplay": False,
        "judgement_windows_ms": {
            "sick": 45,
            "good": 90,
            "bad": 135,
            "shit": 166
        }
    },
    "audio": {
        "master_volume": 0.9,
        "music_volume": 0.9,
        "sfx_volume": 0.85,
        "voices_volume": 0.9
    },
    "keybinds": {
        # FNF-like gameplay layout. Arrows remain as alternates.
        "left": ["d", "left"],
        "down": ["f", "down"],
        "up": ["j", "up"],
        "right": ["k", "right"],
        # Menu layout is separated so D/F/J/K does not break navigation.
        "menu_left": ["a", "left"],
        "menu_down": ["s", "down"],
        "menu_up": ["w", "up"],
        "menu_right": ["d", "right"],
        "accept": ["return", "space"],
        "back": ["escape"],
        "pause": ["return", "p"],
        "reset": ["r"],
        "variation": ["tab"],
        "fullscreen": ["f11"]
    },
    "mods": {
        "enabled": ["example_10min_mod"]
    },
    "debug": {
        "show_timing": False,
        "auto_discover_songs": True
    }
}


def load_config(root: Path) -> dict[str, Any]:
    path = root / "settings.json"
    existing = load_json(path, default={})
    config = merge_dict(DEFAULT_CONFIG, existing if isinstance(existing, dict) else {})
    migrate_config(config)
    if not path.exists():
        save_json(path, config)
    return config


def save_config(root: Path, config: dict[str, Any]) -> None:
    save_json(root / "settings.json", config)


def migrate_config(config: dict[str, Any]) -> None:
    """Keep older settings usable and split gameplay/menu input safely."""
    keybinds = config.setdefault("keybinds", {})

    # Older settings used A/S/W/D as gameplay lanes. That makes D both a lane and
    # menu-right once we add real FNF controls, so migrate only untouched defaults.
    legacy_gameplay = {
        "left": ["a", "left"],
        "down": ["s", "down"],
        "up": ["w", "up"],
        "right": ["d", "right"],
    }
    current_gameplay = {k: keybinds.get(k) for k in legacy_gameplay}
    if current_gameplay == legacy_gameplay:
        keybinds["left"] = ["d", "left"]
        keybinds["down"] = ["f", "down"]
        keybinds["up"] = ["j", "up"]
        keybinds["right"] = ["k", "right"]

    keybinds.setdefault("left", ["d", "left"])
    keybinds.setdefault("down", ["f", "down"])
    keybinds.setdefault("up", ["j", "up"])
    keybinds.setdefault("right", ["k", "right"])
    keybinds.setdefault("menu_left", ["a", "left"])
    keybinds.setdefault("menu_down", ["s", "down"])
    keybinds.setdefault("menu_up", ["w", "up"])
    keybinds.setdefault("menu_right", ["d", "right"])
    keybinds.setdefault("accept", ["return", "space"])
    keybinds.setdefault("back", ["escape"])
    keybinds.setdefault("pause", ["return", "p"])
    keybinds.setdefault("reset", ["r"])
    keybinds.setdefault("variation", ["tab"])
    keybinds.setdefault("fullscreen", ["f11"])

    gameplay = config.setdefault("gameplay", {})
    gameplay.setdefault("sustain_release_grace_ms", 120)
