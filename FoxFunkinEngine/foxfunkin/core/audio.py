from __future__ import annotations

from pathlib import Path
import pygame


class AudioEngine:
    def __init__(self, config: dict):
        self.config = config
        self.available = False
        self.music_path: Path | None = None
        self.voice_sounds: list[pygame.mixer.Sound] = []
        self.voice_channels: list[pygame.mixer.Channel] = []
        self.started_ticks = 0
        self.paused_at = 0
        self.paused = False
        self.length_ms: float | None = None
        try:
            pygame.mixer.init()
            pygame.mixer.music.set_volume(config.get("audio", {}).get("music_volume", 0.9))
            self.available = True
        except pygame.error:
            self.available = False

    def load_song(self, inst_path: Path | None, voice_paths: list[Path] | None = None) -> None:
        self.stop()
        self.music_path = inst_path
        self.voice_sounds = []
        self.voice_channels = []
        self.length_ms = None
        if not self.available:
            return
        if inst_path and inst_path.exists():
            try:
                pygame.mixer.music.load(str(inst_path))
            except pygame.error:
                self.music_path = None
        for vp in voice_paths or []:
            if not vp or not vp.exists():
                continue
            try:
                snd = pygame.mixer.Sound(str(vp))
                snd.set_volume(self.config.get("audio", {}).get("voices_volume", 0.9))
                self.voice_sounds.append(snd)
            except pygame.error:
                pass

    def play(self, start_ms: int = 0) -> None:
        self.started_ticks = pygame.time.get_ticks() - int(start_ms)
        self.paused = False
        self.paused_at = 0
        if not self.available:
            return
        if self.music_path:
            try:
                pygame.mixer.music.play(0, max(0.0, start_ms / 1000.0))
            except pygame.error:
                pygame.mixer.music.play()
        self.voice_channels = []
        for snd in self.voice_sounds:
            try:
                ch = snd.play()
                if ch:
                    self.voice_channels.append(ch)
            except pygame.error:
                pass

    def play_sound(self, path: Path | None, volume: float | None = None) -> None:
        if not self.available or not path or not path.exists():
            return
        try:
            snd = pygame.mixer.Sound(str(path))
            snd.set_volume(float(volume if volume is not None else self.config.get("audio", {}).get("sfx_volume", 0.85)))
            snd.play()
        except pygame.error:
            pass

    def stop(self) -> None:
        if self.available:
            pygame.mixer.music.stop()
            for ch in getattr(self, "voice_channels", []):
                try:
                    ch.stop()
                except Exception:
                    pass
        self.started_ticks = pygame.time.get_ticks()
        self.paused = False

    def pause(self) -> None:
        if self.paused:
            return
        self.paused_at = self.position_ms()
        self.paused = True
        if self.available:
            pygame.mixer.music.pause()
            for ch in self.voice_channels:
                ch.pause()

    def resume(self) -> None:
        if not self.paused:
            return
        self.started_ticks = pygame.time.get_ticks() - int(self.paused_at)
        self.paused = False
        if self.available:
            pygame.mixer.music.unpause()
            for ch in self.voice_channels:
                ch.unpause()

    def position_ms(self) -> float:
        if self.paused:
            return float(self.paused_at)
        if self.available and self.music_path:
            pos = pygame.mixer.music.get_pos()
            if pos >= 0:
                return float(pos)
        return float(pygame.time.get_ticks() - self.started_ticks)

    def is_playing(self) -> bool:
        if self.paused:
            return True
        if self.available and self.music_path:
            return pygame.mixer.music.get_busy()
        return True
