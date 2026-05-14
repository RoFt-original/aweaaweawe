from __future__ import annotations

import traceback
from pathlib import Path

import pygame

from foxfunkin.core.config import load_config
from foxfunkin.core.paths import project_root, PathResolver
from foxfunkin.core.asset_manager import AssetManager
from foxfunkin.core.input import InputMap
from foxfunkin.game.states import StateMachine
from foxfunkin.game.menus import TitleState


class App:
    def __init__(self):
        pygame.init()
        self.root = project_root()
        self.config = load_config(self.root)
        window = self.config.get("window", {})
        flags = pygame.FULLSCREEN if window.get("fullscreen") else 0
        self.screen = pygame.display.set_mode((int(window.get("width", 1280)), int(window.get("height", 720))), flags)
        pygame.display.set_caption(str(window.get("caption", "FoxFunkin Engine")))
        self.clock = pygame.time.Clock()
        self.running = True
        self.fullscreen = bool(window.get("fullscreen"))
        self.resolver = PathResolver(self.root, self.config)
        self.assets = AssetManager(self.resolver)
        self.input = InputMap(self.config)
        self.states = StateMachine(self)
        self.states.change(TitleState)

    def run(self):
        fps = int(self.config.get("window", {}).get("fps", 120))
        while self.running:
            dt = self.clock.tick(fps) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.states.handle_event(event)
            self.states.update(dt)
            self.states.draw(self.screen)
            pygame.display.flip()
        pygame.quit()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        size = (int(self.config.get("window", {}).get("width", 1280)), int(self.config.get("window", {}).get("height", 720)))
        flags = pygame.FULLSCREEN if self.fullscreen else 0
        self.screen = pygame.display.set_mode(size, flags)


def main() -> int:
    try:
        App().run()
        return 0
    except Exception:
        root = project_root()
        log_dir = root / "logs"
        log_dir.mkdir(exist_ok=True)
        (log_dir / "crash.txt").write_text(traceback.format_exc(), encoding="utf-8")
        print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
