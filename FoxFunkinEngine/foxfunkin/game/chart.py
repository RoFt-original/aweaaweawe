from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from foxfunkin.core.jsonx import load_json
from foxfunkin.core.paths import PathResolver
from .song import SongInfo, load_song_variant_info


@dataclass
class Note:
    time_ms: float
    direction: int
    length_ms: float = 0.0
    must_hit: bool = True
    kind: str = ""
    hit: bool = False
    missed: bool = False
    sustain_finished: bool = False

    @property
    def lane(self) -> int:
        return int(self.direction) % 4

    @property
    def end_time_ms(self) -> float:
        return self.time_ms + max(0.0, self.length_ms)


@dataclass
class Chart:
    song: SongInfo
    difficulty: str = "normal"
    variation: str = ""
    scroll_speed: float = 1.5
    events: list[dict[str, Any]] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)
    chart_path: Path | None = None
    inst_path: Path | None = None
    voice_paths: list[Path] = field(default_factory=list)

    @property
    def length_ms(self) -> float:
        last = 0.0
        for note in self.notes:
            last = max(last, note.end_time_ms)
        for ev in self.events:
            try:
                last = max(last, float(ev.get("t", 0)))
            except Exception:
                pass
        return last + 3000


class LegacyChartAdapter:
    @staticmethod
    def parse(song_info: SongInfo, data: dict, difficulty: str) -> tuple[list[Note], float, list[dict]]:
        song = data.get("song", data)
        speed = float(song.get("speed", song.get("scrollSpeed", 1.5)) or 1.5)
        notes: list[Note] = []
        for section in song.get("notes", []):
            must_hit_section = bool(section.get("mustHitSection", True))
            for raw in section.get("sectionNotes", []):
                if not isinstance(raw, list) or len(raw) < 2:
                    continue
                t = float(raw[0])
                d = int(raw[1])
                sustain = float(raw[2]) if len(raw) > 2 else 0.0
                # Old charts encode perspective through mustHitSection. This maps it into 0-7 lanes.
                lane = d % 4
                is_player = (d < 4 and must_hit_section) or (d >= 4 and not must_hit_section)
                direction = lane + (4 if is_player else 0)
                kind = str(raw[3]) if len(raw) > 3 and raw[3] is not None else ""
                notes.append(Note(t, direction, sustain, must_hit=is_player, kind=kind))
        notes.sort(key=lambda n: n.time_ms)
        return notes, speed, []


def parse_v2_chart(song_info: SongInfo, data: dict, difficulty: str) -> tuple[list[Note], float, list[dict]]:
    scroll = data.get("scrollSpeed", 1.5)
    if isinstance(scroll, dict):
        speed = float(scroll.get(difficulty, scroll.get("normal", next(iter(scroll.values()), 1.5))))
    else:
        speed = float(scroll or 1.5)

    notes_data = data.get("notes", {})
    selected = []
    if isinstance(notes_data, dict):
        selected = notes_data.get(difficulty) or notes_data.get("normal") or next(iter(notes_data.values()), [])
    elif isinstance(notes_data, list):
        selected = notes_data

    notes: list[Note] = []
    for item in selected:
        if not isinstance(item, dict):
            continue
        t = float(item.get("t", item.get("time", 0)))
        d = int(item.get("d", item.get("direction", 4)))
        length = float(item.get("l", item.get("length", item.get("sustain", 0))) or 0)
        must_hit = d >= 4
        kind = str(item.get("k", item.get("kind", "")) or "")
        notes.append(Note(t, d, length, must_hit=must_hit, kind=kind))
    notes.sort(key=lambda n: n.time_ms)

    events = list(data.get("events", [])) if isinstance(data.get("events", []), list) else []
    events.sort(key=lambda ev: float(ev.get("t", 0)) if isinstance(ev, dict) else 0)
    return notes, speed, events


def load_chart(resolver: PathResolver, song_id: str, difficulty: str = "normal", variation: str | None = None) -> Chart:
    variation = variation or ""
    song_info = load_song_variant_info(resolver, song_id, variation or None)
    chart_path = resolver.resolve_any(resolver.chart_candidates(song_id, variation or None))
    notes: list[Note] = []
    events: list[dict] = []
    speed = 1.5

    if chart_path:
        data = load_json(chart_path, default={})
        if isinstance(data, dict) and "song" in data:
            notes, speed, events = LegacyChartAdapter.parse(song_info, data, difficulty)
        elif isinstance(data, dict):
            notes, speed, events = parse_v2_chart(song_info, data, difficulty)

    if not notes:
        # Playable fallback, so a mod can boot even before audio exists.
        for i, t in enumerate(range(1000, 17000, 500)):
            lane = i % 4
            notes.append(Note(float(t), lane + 4, 0.0, must_hit=True))
            if i % 4 == 0:
                notes.append(Note(float(t + 250), lane, 0.0, must_hit=False))

    instrumental = song_info.instrumental or variation or None
    inst = resolver.resolve_any(resolver.song_file_candidates(song_id, "Inst", instrumental))
    voice_paths = []
    vocal_stems = ["Voices-bf", "Voices-dad", "Voices-gf", f"Voices-{song_info.player}", f"Voices-{song_info.opponent}"]
    vocal_stems.extend(f"Voices-{v}" for v in song_info.player_vocals)
    vocal_stems.extend(f"Voices-{v}" for v in song_info.opponent_vocals)
    for stem in vocal_stems:
        p = resolver.resolve_any(resolver.song_file_candidates(song_id, stem, variation or None))
        if p and p not in voice_paths:
            voice_paths.append(p)

    return Chart(
        song=song_info,
        difficulty=difficulty,
        variation=variation,
        scroll_speed=speed,
        events=events,
        notes=notes,
        chart_path=chart_path,
        inst_path=inst,
        voice_paths=voice_paths,
    )
