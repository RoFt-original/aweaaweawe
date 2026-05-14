from __future__ import annotations

import pygame

from foxfunkin.core.audio import AudioEngine
from .states import State
from .chart import load_chart, Note
from .characters import Character
from .stage import Stage
from .notes import NoteRenderer
from .scoring import ScoreState
from .camera import Camera
from .events import EventDispatcher
from .visual_script import VisualGraphExecutor
from .ui import Toast, draw_text, draw_panel, clamp
from .highscores import update_highscore


class GameplayState(State):
    def enter(self, song_id: str = "fox-test", difficulty: str = "normal", variation: str = "", **kwargs):
        self.song_id = song_id
        self.difficulty = difficulty
        self.variation = variation or ""
        self.chart = load_chart(self.app.resolver, song_id, difficulty, self.variation)
        self.song = self.chart.song
        self.audio = AudioEngine(self.app.config)
        self.audio.load_song(self.chart.inst_path, self.chart.voice_paths)

        self.font = self.app.assets.font(24)
        self.big = self.app.assets.font(42)
        self.small = self.app.assets.font(18)
        self.note_renderer = NoteRenderer(self.app.assets, self.app.resolver, self.song.note_style, size=64)
        self.stage = Stage(self.song.stage, self.app.assets, self.app.resolver)

        w, h = self.app.screen.get_size()
        self.characters = {
            "dad": Character(self.song.opponent, self.app.assets, self.app.resolver, pos=self.stage.character_position("dad", (w * 0.25, h * 0.63)), scale=0.72, flip=False),
            "gf": Character(self.song.girlfriend, self.app.assets, self.app.resolver, pos=self.stage.character_position("gf", (w * 0.50, h * 0.55)), scale=0.62, flip=False),
            "bf": Character(self.song.player, self.app.assets, self.app.resolver, pos=self.stage.character_position("bf", (w * 0.75, h * 0.66)), scale=0.72, flip=True),
        }
        self.character_draw_order = sorted(
            ["dad", "gf", "bf"],
            key=lambda key: self.stage.character_z(key, {"gf": 100, "dad": 200, "bf": 300}.get(key, 0)),
        )

        windows = self.app.config.get("gameplay", {}).get("judgement_windows_ms", {})
        self.score_state = ScoreState(windows=windows)
        self.score_state.total_notes = len([n for n in self.chart.notes if n.must_hit])
        self.camera = Camera()
        self.camera.target_zoom = self.stage.camera_zoom
        self.toast = Toast()
        self.graph_executor = VisualGraphExecutor(self.app.resolver)
        self.dispatcher = EventDispatcher(self)
        self.script_variables: dict[str, object] = {}
        self.entry_graphs = self.load_entry_graphs()
        self.event_index = 0
        self.events = list(self.chart.events)
        self.scroll_speed = self.chart.scroll_speed * float(self.app.config.get("gameplay", {}).get("scroll_speed_multiplier", 1.0))
        self.spawned_text: list[dict] = []
        self.paused = False
        self.finished = False
        self.song_started = 0
        self.countdown_done = False
        self.countdown_time = 0.0
        self.countdown_label = "READY"
        self.countdown_step = -1
        self.last_beat = -1
        self.last_step = -1
        self.input_offset = float(self.app.config.get("gameplay", {}).get("input_offset_ms", 0))
        self.audio_offset = float(self.app.config.get("gameplay", {}).get("audio_offset_ms", 0))
        self.safe_zone = float(self.app.config.get("gameplay", {}).get("safe_zone_ms", 166))
        self.sustain_grace = float(self.app.config.get("gameplay", {}).get("sustain_release_grace_ms", 120))
        self.downscroll = bool(self.app.config.get("gameplay", {}).get("downscroll", False))
        self.botplay = bool(self.app.config.get("gameplay", {}).get("botplay", False))
        self.held_lanes: set[int] = set()
        self.active_sustains: dict[int, Note] = {}

        if not self.chart.inst_path:
            self.toast.push("No Inst audio found; running silent chart timer.")
        if not self.chart.chart_path:
            self.toast.push("No chart found; using generated fallback notes.")

    def load_entry_graphs(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {"OnBeat": [], "OnStep": [], "OnNoteHit": []}
        for manifest in self.app.resolver.list_mods():
            if not manifest.get("_enabled"):
                continue
            entries = manifest.get("entryGraphs", {})
            if isinstance(entries, dict):
                for key, value in entries.items():
                    values = value if isinstance(value, list) else [value]
                    out.setdefault(str(key), []).extend(str(v) for v in values if v)
        return out

    def exit(self):
        self.audio.stop()

    def song_position(self) -> float:
        if not self.countdown_done:
            return 0.0
        return self.audio.position_ms() + self.audio_offset

    def handle_event(self, event):
        if event.type == pygame.KEYUP:
            lane = self.app.input.lane_for_key(event.key)
            if lane is not None:
                self.release_lane(lane)
            return
        if event.type != pygame.KEYDOWN:
            return
        action = self.app.input.action_for_key(event.key)
        if action == "pause":
            self.toggle_pause()
            return
        if action == "fullscreen" and hasattr(self.app, "toggle_fullscreen"):
            self.app.toggle_fullscreen()
            return
        if action == "back":
            self.audio.stop()
            from .menus import FreeplayState
            self.app.states.change(FreeplayState)
            return
        if action == "reset":
            self.app.states.change(GameplayState, song_id=self.song_id, difficulty=self.difficulty, variation=self.variation)
            return
        lane = self.app.input.lane_for_key(event.key)
        if lane is not None and not self.paused:
            self.held_lanes.add(lane)
            self.try_hit(lane)

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.audio.pause()
            self.toast.push("Paused")
        else:
            self.audio.resume()
            self.toast.push("Resume")

    def play_character_animation(self, target: str, anim: str, force: bool = False):
        aliases = {
            "player": "bf",
            "boyfriend": "bf",
            "opponent": "dad",
            "dad": "dad",
            "gf": "gf",
            "girlfriend": "gf",
            "bf": "bf",
        }
        key = aliases.get(target, target)
        char = self.characters.get(key)
        if char:
            char.play(anim, force=force)

    def spawn_text(self, text: str, duration: float = 2.0):
        if text:
            self.spawned_text.append({"text": text, "ttl": float(duration)})

    def try_hit(self, lane: int):
        if not self.countdown_done:
            return
        pos = self.song_position() + self.input_offset
        candidates = [
            n for n in self.chart.notes
            if n.must_hit and not n.hit and not n.missed and n.lane == lane and abs(n.time_ms - pos) <= self.safe_zone
        ]
        if not candidates:
            if not self.app.config.get("gameplay", {}).get("ghost_tapping", True):
                self.score_state.register_miss()
            return
        note = min(candidates, key=lambda n: abs(n.time_ms - pos))
        note.hit = True
        if note.length_ms > 0:
            self.active_sustains[lane] = note
        diff = pos - note.time_ms
        rating = self.score_state.register_hit(diff)
        anim = ("singLEFT", "singDOWN", "singUP", "singRIGHT")[lane]
        self.characters["bf"].play(anim, force=True)
        self.camera.bump(0.012 if rating == "sick" else 0.006)
        self.run_entry_graphs("OnNoteHit", {"lane": lane, "kind": note.kind, "rating": rating, "time": note.time_ms})

    def release_lane(self, lane: int) -> None:
        self.held_lanes.discard(lane)
        note = self.active_sustains.get(lane)
        if not note or note.sustain_finished or note.missed:
            return
        pos = self.song_position()
        if pos < note.end_time_ms - self.sustain_grace:
            note.missed = True
            note.sustain_finished = True
            self.active_sustains.pop(lane, None)
            self.score_state.register_miss()
            self.characters["bf"].play(("singLEFTmiss", "singDOWNmiss", "singUPmiss", "singRIGHTmiss")[lane], force=True)
            self.camera.shake(4, 0.08)

    def update_sustains(self, pos: float) -> None:
        for lane, note in list(self.active_sustains.items()):
            if note.missed:
                self.active_sustains.pop(lane, None)
                continue
            if lane not in self.held_lanes and pos < note.end_time_ms - self.sustain_grace:
                note.missed = True
                note.sustain_finished = True
                self.active_sustains.pop(lane, None)
                self.score_state.register_miss()
                self.camera.shake(4, 0.08)
                continue
            if pos >= note.end_time_ms:
                note.sustain_finished = True
                self.active_sustains.pop(lane, None)

    def auto_hit_opponent(self, pos: float):
        for note in self.chart.notes:
            if note.must_hit or note.hit or note.missed:
                continue
            if note.time_ms <= pos:
                note.hit = True
                anim = ("singLEFT", "singDOWN", "singUP", "singRIGHT")[note.lane]
                self.characters["dad"].play(anim, force=True)

    def botplay_hits(self, pos: float):
        if not self.botplay:
            return
        for note in self.chart.notes:
            if not note.must_hit or note.hit or note.missed:
                continue
            if abs(note.time_ms - pos) <= 12:
                note.hit = True
                note.sustain_finished = True
                self.score_state.register_hit(0)
                self.characters["bf"].play(("singLEFT", "singDOWN", "singUP", "singRIGHT")[note.lane], force=True)

    def miss_passed_notes(self, pos: float):
        for note in self.chart.notes:
            if not note.must_hit or note.hit or note.missed:
                continue
            if pos - note.time_ms > self.safe_zone:
                note.missed = True
                self.score_state.register_miss()
                self.camera.shake(3, 0.08)

    def process_events(self, pos: float):
        while self.event_index < len(self.events):
            event = self.events[self.event_index]
            try:
                t = float(event.get("t", 0))
            except Exception:
                t = 0
            if t > pos:
                break
            self.dispatcher.dispatch(event)
            self.event_index += 1

    def update_beat(self, pos: float):
        beat_len = 60000.0 / max(1.0, self.song.bpm)
        beat = int(pos // beat_len)
        if beat != self.last_beat:
            self.last_beat = beat
            self.run_entry_graphs("OnBeat", {"beat": beat, "time": pos})
            if beat % 2 == 0:
                for key, char in self.characters.items():
                    if char.current_anim.startswith("sing"):
                        char.play("idle")
                self.camera.bump(0.006)
        step = int(pos // max(1.0, beat_len / 4.0))
        if step != self.last_step:
            self.last_step = step
            self.run_entry_graphs("OnStep", {"step": step, "time": pos})

    def run_entry_graphs(self, event_type: str, payload: dict) -> None:
        for graph_ref in self.entry_graphs.get(event_type, []):
            self.graph_executor.run(graph_ref, self, event_type, payload)

    def update_countdown(self, dt: float) -> None:
        if self.countdown_done:
            return
        self.countdown_time += dt
        step_len = max(0.28, (60000.0 / max(1.0, self.song.bpm)) / 1000.0)
        labels = ["READY", "SET", "GO"]
        step = int(self.countdown_time // step_len)
        if step != self.countdown_step:
            self.countdown_step = step
            self.countdown_label = labels[step] if step < len(labels) else ""
            if self.countdown_label:
                self.toast.push(self.countdown_label, min(0.8, step_len))
        if self.countdown_time >= step_len * len(labels):
            self.countdown_done = True
            self.song_started = pygame.time.get_ticks()
            self.audio.play()

    def update(self, dt):
        self.toast.update(dt)
        if self.paused:
            return
        if not self.countdown_done:
            self.update_countdown(dt)
            for char in self.characters.values():
                char.update(dt)
            return
        pos = self.song_position()
        self.camera.update(dt)
        self.process_events(pos)
        self.auto_hit_opponent(pos)
        self.botplay_hits(pos)
        self.update_sustains(pos)
        self.miss_passed_notes(pos)
        self.update_beat(pos)
        for char in self.characters.values():
            char.update(dt)

        for item in self.spawned_text:
            item["ttl"] -= dt
        self.spawned_text = [x for x in self.spawned_text if x["ttl"] > 0]

        if self.score_state.health <= 0:
            self.finish(failed=True)
        elif pos >= self.chart.length_ms and not self.finished:
            self.finish(failed=False)

    def finish(self, failed: bool = False):
        self.finished = True
        self.audio.stop()
        self.app.states.change(ResultsState, song_id=self.song_id, difficulty=self.difficulty, variation=self.variation, score_state=self.score_state, failed=failed)

    def lane_positions(self):
        w, h = self.app.screen.get_size()
        gap = 74
        opp_center = int(w * 0.28)
        ply_center = int(w * 0.72)
        opp = [opp_center + (i - 1.5) * gap for i in range(4)]
        ply = [ply_center + (i - 1.5) * gap for i in range(4)]
        return [int(x) for x in opp], [int(x) for x in ply]

    def draw(self, screen):
        w, h = screen.get_size()
        self.stage.draw(screen, self.song_position())
        cam_off = (self.camera.offset.x, self.camera.offset.y)

        for key in self.character_draw_order:
            self.characters[key].draw(screen, cam_off)

        pos = self.song_position()
        receptor_y = h - 130 if self.downscroll else 120
        opp_xs, ply_xs = self.lane_positions()
        self.note_renderer.draw_receptors(screen, opp_xs, receptor_y, self.small)
        self.note_renderer.draw_receptors(screen, ply_xs, receptor_y, self.small)

        px_per_ms = 0.42 * self.scroll_speed
        visible_ahead = h / max(0.01, px_per_ms) + 500
        for note in self.chart.notes:
            if note.missed:
                continue
            active_sustain = note.hit and note.length_ms > 0 and not note.sustain_finished
            if note.hit and not active_sustain:
                continue
            delta = note.time_ms - pos
            if active_sustain:
                delta = max(0.0, note.end_time_ms - pos)
            if delta < -240 or delta > visible_ahead:
                continue
            xs = ply_xs if note.must_hit else opp_xs
            x = xs[note.lane]
            y = receptor_y - delta * px_per_ms if self.downscroll else receptor_y + delta * px_per_ms
            if active_sustain:
                y = receptor_y
                sustain_px = int(max(0.0, note.end_time_ms - pos) * px_per_ms)
            else:
                sustain_px = int(note.length_ms * px_per_ms) if note.length_ms > 0 else 0
            alpha = 255 if note.must_hit else 150
            self.note_renderer.draw_note(screen, note.lane, x, int(y), alpha=alpha, sustain_px=sustain_px, downscroll=self.downscroll, kind=note.kind, font=self.small)

        self.draw_hud(screen)
        self.toast.draw(screen, self.small)

        for i, item in enumerate(self.spawned_text[-3:]):
            surf = self.big.render(str(item["text"]), True, (255, 240, 120))
            rect = surf.get_rect(center=(w // 2, h // 2 - 80 + i * 48))
            bg = rect.inflate(30, 18)
            pygame.draw.rect(screen, (0, 0, 0, 170), bg, border_radius=12)
            screen.blit(surf, rect)

        if self.paused:
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            draw_text(screen, self.big, "PAUSED", (w // 2, h // 2), (255, 255, 255), "center")
        elif not self.countdown_done and self.countdown_label:
            draw_text(screen, self.big, self.countdown_label, (w // 2, h // 2 - 70), (255, 230, 90), "center")

    def draw_hud(self, screen):
        w, h = screen.get_size()
        top_y = 18
        health_rect = pygame.Rect(w // 2 - 220, top_y, 440, 20)
        pygame.draw.rect(screen, (60, 20, 30), health_rect, border_radius=8)
        fill = health_rect.copy()
        fill.width = int(health_rect.width * clamp(self.score_state.health / 2.0, 0.0, 1.0))
        pygame.draw.rect(screen, (80, 220, 130), fill, border_radius=8)
        pygame.draw.rect(screen, (240, 240, 240), health_rect, 2, border_radius=8)

        variant = f" / {self.variation}" if self.variation else ""
        left = f"{self.song.display_name} [{self.difficulty}{variant}]"
        right = f"Score {self.score_state.score}  Combo {self.score_state.combo}  Miss {self.score_state.misses}  Acc {self.score_state.accuracy:.1f}%"
        draw_text(screen, self.font, left, (22, 14), (245, 245, 245))
        draw_text(screen, self.font, right, (w - 22, 14), (245, 245, 245), "topright")
        if self.score_state.last_rating:
            draw_text(screen, self.big, self.score_state.last_rating, (w // 2, 62), (255, 230, 90), "center")
        if self.botplay:
            draw_text(screen, self.font, "BOTPLAY", (w // 2, h - 48), (255, 200, 70), "center")


class ResultsState(State):
    def enter(self, song_id: str, difficulty: str, score_state: ScoreState, failed: bool = False, variation: str = "", **kwargs):
        self.song_id = song_id
        self.difficulty = difficulty
        self.variation = variation or ""
        self.score_state = score_state
        self.failed = failed
        self.new_best = False if failed else update_highscore(self.app.root, song_id, difficulty, self.variation, score_state)
        self.title = self.app.assets.font(62)
        self.font = self.app.assets.font(32)
        self.small = self.app.assets.font(22)

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        action = self.app.input.action_for_key(event.key)
        if action == "accept":
            self.app.states.change(GameplayState, song_id=self.song_id, difficulty=self.difficulty, variation=self.variation)
        elif action == "back":
            from .menus import FreeplayState
            self.app.states.change(FreeplayState)

    def draw(self, screen):
        w, h = screen.get_size()
        screen.fill((12, 12, 18))
        title = "FAILED" if self.failed else "RESULTS"
        draw_text(screen, self.title, title, (w // 2, 100), (255, 230, 100) if not self.failed else (255, 90, 90), "center")
        panel = pygame.Rect(w // 2 - 260, 170, 520, 300)
        draw_panel(screen, panel, fill=(22, 22, 34, 230), border=(100, 100, 140))
        lines = [
            f"Score: {self.score_state.score}",
            f"Max Combo: {self.score_state.max_combo}",
            f"Misses: {self.score_state.misses}",
            f"Accuracy: {self.score_state.accuracy:.2f}%",
            f"Rank: {self.score_state.rank}",
        ]
        if self.new_best:
            lines.append("New Best!")
        y = panel.y + 35
        for line in lines:
            draw_text(screen, self.font, line, (w // 2, y), (240, 240, 245), "center")
            y += 48
        draw_text(screen, self.small, "Enter: retry    Esc: freeplay", (w // 2, h - 60), (180, 180, 200), "center")
