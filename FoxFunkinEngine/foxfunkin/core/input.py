from __future__ import annotations

import pygame


def key_constant(name: str) -> int:
    value = getattr(pygame, f"K_{name.lower()}", None)
    if value is None:
        return pygame.K_UNKNOWN
    return value


class InputMap:
    def __init__(self, config: dict):
        self.bindings: dict[str, list[int]] = {}
        for action, names in config.get("keybinds", {}).items():
            self.bindings[action] = [key_constant(n) for n in names]

    def action_for_key(self, key: int) -> str | None:
        for action, keys in self.bindings.items():
            if key in keys:
                return action
        return None

    def menu_action_for_key(self, key: int) -> str | None:
        menu_actions = {
            "menu_left": "left",
            "menu_down": "down",
            "menu_up": "up",
            "menu_right": "right",
        }
        for action, keys in self.bindings.items():
            if key not in keys:
                continue
            if action in menu_actions:
                return menu_actions[action]
            if action in ("accept", "back", "variation", "fullscreen"):
                return action
        return None

    def pressed(self, action: str, keys_state=None) -> bool:
        if keys_state is None:
            keys_state = pygame.key.get_pressed()
        return any(keys_state[k] for k in self.bindings.get(action, []) if k >= 0)

    def lane_for_key(self, key: int) -> int | None:
        for idx, action in enumerate(("left", "down", "up", "right")):
            if key in self.bindings.get(action, []):
                return idx
        return None

    def lane_labels(self) -> tuple[str, str, str, str]:
        labels: list[str] = []
        for action in ("left", "down", "up", "right"):
            names = []
            for key in self.bindings.get(action, []):
                if key != pygame.K_UNKNOWN:
                    names.append(pygame.key.name(key).upper())
            labels.append("/".join(names[:2]) or "?")
        return tuple(labels)  # type: ignore[return-value]
