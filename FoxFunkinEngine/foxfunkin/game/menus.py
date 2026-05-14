from __future__ import annotations

import pygame

from foxfunkin.core.config import save_config
from foxfunkin.core.input import InputMap
from foxfunkin.core.jsonx import load_json
from .states import State
from .song import discover_songs, load_song_variant_info
from .gameplay import GameplayState
from .ui import draw_text, draw_panel
from .highscores import best_score


class MenuState(State):
    items: list[str] = []

    def enter(self, **kwargs):
        self.selected = 0
        self.title_font = self.app.assets.font(64)
        self.font = self.app.assets.font(32)
        self.small = self.app.assets.font(22)

    def move(self, delta: int):
        if self.items:
            self.selected = (self.selected + delta) % len(self.items)

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        action = self.app.input.action_for_key(event.key)
        if action == "up":
            self.move(-1)
        elif action == "down":
            self.move(1)
        elif action == "accept":
            self.choose()
        elif action == "fullscreen" and hasattr(self.app, "toggle_fullscreen"):
            self.app.toggle_fullscreen()
        elif action == "back":
            self.back()

    def choose(self):
        pass

    def back(self):
        self.app.states.change(MainMenuState)

    def draw_items(self, screen, title):
        w, _ = screen.get_size()
        screen.fill((14, 14, 21))
        draw_text(screen, self.title_font, title, (w // 2, 90), (255, 255, 255), "center")
        y = 190
        for i, item in enumerate(self.items):
            color = (255, 220, 80) if i == self.selected else (230, 230, 230)
            prefix = "> " if i == self.selected else "  "
            draw_text(screen, self.font, prefix + item, (w // 2, y), color, "center")
            y += 48


class TitleState(State):
    def enter(self, **kwargs):
        self.title_font = self.app.assets.font(72)
        self.font = self.app.assets.font(28)
        self.blink = 0.0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            self.app.states.change(MainMenuState)

    def update(self, dt):
        self.blink += dt

    def draw(self, screen):
        w, h = screen.get_size()
        screen.fill((14, 14, 20))
        draw_text(screen, self.title_font, "FoxFunkin", (w // 2, h // 2 - 80), (255, 245, 245), "center")
        draw_text(screen, self.font, "fan rhythm engine - external /data - mod first", (w // 2, h // 2 - 20), (200, 200, 220), "center")
        if int(self.blink * 2) % 2 == 0:
            draw_text(screen, self.font, "PRESS ANY KEY", (w // 2, h // 2 + 80), (255, 220, 80), "center")
        draw_text(screen, self.font, "Public builds ship without original FNF assets. Put local assets into /data.", (w // 2, h - 42), (160, 160, 170), "center")


class MainMenuState(MenuState):
    def enter(self, **kwargs):
        super().enter(**kwargs)
        self.items = ["Freeplay", "Story Mode", "Mods", "Options", "Asset Check", "Quit"]

    def choose(self):
        item = self.items[self.selected]
        if item == "Freeplay":
            self.app.states.change(FreeplayState)
        elif item == "Story Mode":
            self.app.states.change(StoryState)
        elif item == "Mods":
            self.app.states.change(ModsState)
        elif item == "Options":
            self.app.states.change(OptionsState)
        elif item == "Asset Check":
            self.app.states.change(AssetCheckState)
        elif item == "Quit":
            self.app.running = False

    def back(self):
        self.app.states.change(TitleState)

    def draw(self, screen):
        self.draw_items(screen, "FoxFunkin")


class FreeplayState(MenuState):
    def enter(self, **kwargs):
        super().enter(**kwargs)
        self.songs = discover_songs(self.app.resolver)
        self.diff_index = 0
        self.var_index = 0
        self.refresh_items()

    def current_song(self):
        return self.songs[self.selected] if self.songs else None

    def variations_for(self, song):
        return [""] + [v for v in song.variations if v]

    def selected_variation(self):
        song = self.current_song()
        if not song:
            return ""
        values = self.variations_for(song)
        self.var_index %= max(1, len(values))
        return values[self.var_index]

    def current_variant_info(self):
        song = self.current_song()
        if not song:
            return None
        return load_song_variant_info(self.app.resolver, song.id, self.selected_variation() or None)

    def current_difficulty(self):
        song = self.current_variant_info()
        if not song:
            return "normal"
        diffs = song.difficulties or ["normal"]
        self.diff_index %= max(1, len(diffs))
        return diffs[self.diff_index]

    def refresh_items(self):
        if not self.songs:
            self.items = ["No songs found"]
            return
        self.items = []
        for i, song in enumerate(self.songs):
            suffix = ""
            if i == self.selected:
                variant = self.selected_variation()
                diff = self.current_difficulty()
                suffix = f" [{diff}{' / ' + variant if variant else ''}]"
            self.items.append(song.display_name + suffix)

    def move(self, delta: int):
        super().move(delta)
        self.diff_index = 0
        self.var_index = 0
        self.refresh_items()

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        action = self.app.input.action_for_key(event.key)
        if action == "left":
            self.diff_index -= 1
            self.refresh_items()
        elif action == "right":
            self.diff_index += 1
            self.refresh_items()
        elif action == "variation":
            self.var_index += 1
            self.diff_index = 0
            self.refresh_items()
        else:
            super().handle_event(event)

    def choose(self):
        song = self.current_song()
        if song:
            self.app.states.change(GameplayState, song_id=song.id, difficulty=self.current_difficulty(), variation=self.selected_variation())

    def draw(self, screen):
        self.draw_items(screen, "Freeplay")
        w, h = screen.get_size()
        if self.songs:
            base = self.current_song()
            song = self.current_variant_info()
            variation = self.selected_variation()
            difficulty = self.current_difficulty()
            best = best_score(self.app.root, base.id, difficulty, variation) if base else None
            rect = pygame.Rect(w // 2 - 330, h - 160, 660, 112)
            draw_panel(screen, rect, fill=(20, 20, 30, 225), border=(90, 90, 120))
            draw_text(screen, self.small, f"ID: {base.id if base else song.id}  Variation: {variation or 'base'}", (rect.x + 20, rect.y + 18), (220, 220, 230))
            draw_text(screen, self.small, f"Artist: {song.artist or '-'}  BPM: {song.bpm:g}  Stage: {song.stage}", (rect.x + 20, rect.y + 48), (190, 190, 205))
            best_text = f"Best: {best.get('score')} {best.get('rank')}" if best else "Best: -"
            draw_text(screen, self.small, f"Left/Right difficulty  Tab variation  {best_text}", (rect.x + 20, rect.y + 78), (190, 190, 205))
        else:
            draw_text(screen, self.small, "Put assets into /data, or create a mod with create_mod.bat.", (w // 2, h - 80), (255, 220, 80), "center")


class StoryState(MenuState):
    def enter(self, **kwargs):
        super().enter(**kwargs)
        self.levels = self.load_levels()
        self.items = [level.get("name", level.get("id", "Week")) for level in self.levels] or ["No story songs"]

    def load_levels(self):
        levels = []
        for path in self.app.resolver.glob_all("preload/data/levels/*.json"):
            data = load_json(path, default={})
            if not isinstance(data, dict):
                continue
            data.setdefault("id", path.stem)
            data.setdefault("name", data.get("name") or data.get("title") or path.stem)
            levels.append(data)
        return levels

    def choose(self):
        if not self.levels:
            return
        songs = self.levels[self.selected].get("songs", [])
        if songs:
            self.app.states.change(GameplayState, song_id=str(songs[0]), difficulty="normal")

    def draw(self, screen):
        self.draw_items(screen, "Story Mode")
        if self.levels:
            songs = self.levels[self.selected].get("songs", [])
            draw_text(screen, self.small, "Songs: " + ", ".join(str(s) for s in songs), (screen.get_width() // 2, screen.get_height() - 60), (180, 180, 200), "center")
        else:
            draw_text(screen, self.small, "Add level JSON files to preload/data/levels.", (screen.get_width() // 2, screen.get_height() - 60), (180, 180, 200), "center")


class ModsState(MenuState):
    def enter(self, **kwargs):
        super().enter(**kwargs)
        self.mods = self.app.resolver.list_mods()
        self.items = [self.label(m) for m in self.mods] or ["No mods found"]

    def label(self, mod):
        return ("[x] " if mod.get("_enabled") else "[ ] ") + f"{mod.get('title')} ({mod.get('id')})"

    def choose(self):
        if not self.mods:
            return
        mod = self.mods[self.selected]
        mod_id = mod["id"]
        enabled = self.app.config.setdefault("mods", {}).setdefault("enabled", [])
        if mod_id in enabled:
            enabled.remove(mod_id)
        else:
            enabled.append(mod_id)
        save_config(self.app.root, self.app.config)
        self.app.resolver.refresh()
        self.enter()

    def draw(self, screen):
        self.draw_items(screen, "Mods")
        draw_text(screen, self.small, "Enter toggles. Mods override /data files by path.", (screen.get_width() // 2, screen.get_height() - 60), (180, 180, 200), "center")


class OptionsState(MenuState):
    def enter(self, **kwargs):
        super().enter(**kwargs)
        self.items = self.make_items()

    def make_items(self):
        gp = self.app.config["gameplay"]
        au = self.app.config["audio"]
        return [
            f"Downscroll: {'ON' if gp.get('downscroll') else 'OFF'}",
            f"Botplay: {'ON' if gp.get('botplay') else 'OFF'}",
            f"Scroll multiplier: {gp.get('scroll_speed_multiplier', 1.0):.2f}",
            f"Input offset: {gp.get('input_offset_ms', 0)} ms",
            f"Music volume: {au.get('music_volume', 0.9):.2f}",
            "Rebind controls",
            "Save and Back",
        ]

    def choose(self):
        gp = self.app.config["gameplay"]
        au = self.app.config["audio"]
        idx = self.selected
        if idx == 0:
            gp["downscroll"] = not gp.get("downscroll", False)
        elif idx == 1:
            gp["botplay"] = not gp.get("botplay", False)
        elif idx == 2:
            gp["scroll_speed_multiplier"] = round((float(gp.get("scroll_speed_multiplier", 1.0)) + 0.25), 2)
            if gp["scroll_speed_multiplier"] > 3.0:
                gp["scroll_speed_multiplier"] = 0.5
        elif idx == 3:
            gp["input_offset_ms"] = int(gp.get("input_offset_ms", 0)) + 5
            if gp["input_offset_ms"] > 100:
                gp["input_offset_ms"] = -100
        elif idx == 4:
            au["music_volume"] = round(float(au.get("music_volume", 0.9)) + 0.1, 2)
            if au["music_volume"] > 1.0:
                au["music_volume"] = 0.0
            pygame.mixer.music.set_volume(au["music_volume"])
        elif idx == 5:
            self.app.states.change(RebindState)
            return
        elif idx == 6:
            save_config(self.app.root, self.app.config)
            self.back()
            return
        save_config(self.app.root, self.app.config)
        self.items = self.make_items()

    def draw(self, screen):
        self.draw_items(screen, "Options")


class RebindState(MenuState):
    ACTIONS = ["left", "down", "up", "right", "accept", "back", "pause", "reset", "variation", "fullscreen"]

    def enter(self, **kwargs):
        super().enter(**kwargs)
        self.waiting_for: str | None = None
        self.items = self.make_items()

    def make_items(self):
        keybinds = self.app.config.setdefault("keybinds", {})
        return [f"{action}: {', '.join(keybinds.get(action, []))}" for action in self.ACTIONS] + ["Back"]

    def choose(self):
        if self.selected >= len(self.ACTIONS):
            self.back()
            return
        self.waiting_for = self.ACTIONS[self.selected]

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if self.waiting_for:
            self.app.config.setdefault("keybinds", {})[self.waiting_for] = [pygame.key.name(event.key)]
            save_config(self.app.root, self.app.config)
            self.app.input = InputMap(self.app.config)
            self.waiting_for = None
            self.items = self.make_items()
            return
        super().handle_event(event)

    def back(self):
        self.app.states.change(OptionsState)

    def draw(self, screen):
        self.draw_items(screen, "Rebind")
        if self.waiting_for:
            draw_text(screen, self.font, f"Press key for {self.waiting_for}", (screen.get_width() // 2, screen.get_height() - 70), (255, 220, 80), "center")


class AssetCheckState(State):
    def enter(self, **kwargs):
        self.font = self.app.assets.font(24)
        self.title = self.app.assets.font(48)
        from foxfunkin.tools.asset_validator import validate_assets
        self.lines = validate_assets(self.app.root, return_lines=True)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            self.app.states.change(MainMenuState)

    def draw(self, screen):
        screen.fill((12, 12, 18))
        draw_text(screen, self.title, "Asset Check", (screen.get_width() // 2, 50), (255, 255, 255), "center")
        y = 115
        for line in self.lines[:22]:
            color = (160, 255, 160) if line.startswith("[OK]") else (255, 220, 100) if line.startswith("[WARN]") else (230, 230, 240)
            draw_text(screen, self.font, line, (70, y), color)
            y += 26
        draw_text(screen, self.font, "Press any key to return.", (screen.get_width() // 2, screen.get_height() - 45), (180, 180, 200), "center")
