from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from foxfunkin.core.jsonx import load_json
from foxfunkin.core.paths import PathResolver


@dataclass
class SongInfo:
    id: str
    name: str
    artist: str = ""
    charter: str = ""
    difficulties: list[str] = field(default_factory=lambda: ["normal"])
    variations: list[str] = field(default_factory=list)
    instrumental: str = ""
    player_vocals: list[str] = field(default_factory=list)
    opponent_vocals: list[str] = field(default_factory=list)
    stage: str = "mainStage"
    player: str = "bf"
    opponent: str = "dad"
    girlfriend: str = "gf"
    note_style: str = "funkin"
    bpm: float = 120.0
    metadata_path: Path | None = None
    source: str = "unknown"

    @property
    def display_name(self) -> str:
        return self.name or self.id


def slug_from_metadata_path(path: Path) -> str:
    name = path.name
    if name.endswith("-metadata.json"):
        return name[:-len("-metadata.json")]
    return path.parent.name


def parse_metadata(song_id: str, data: dict[str, Any], path: Path | None = None, source: str = "data") -> SongInfo:
    play = data.get("playData", {}) if isinstance(data, dict) else {}
    chars = play.get("characters", {}) if isinstance(play, dict) else {}
    time_changes = data.get("timeChanges", []) if isinstance(data, dict) else []
    bpm = 120.0
    if time_changes and isinstance(time_changes[0], dict):
        bpm = float(time_changes[0].get("bpm", bpm))
    difficulties = play.get("difficulties") or ["normal"]
    if isinstance(difficulties, str):
        difficulties = [difficulties]
    variations = play.get("songVariations") or []
    if isinstance(variations, str):
        variations = [variations]
    player_vocals = chars.get("playerVocals", []) if isinstance(chars, dict) else []
    opponent_vocals = chars.get("opponentVocals", []) if isinstance(chars, dict) else []
    if isinstance(player_vocals, str):
        player_vocals = [player_vocals]
    if isinstance(opponent_vocals, str):
        opponent_vocals = [opponent_vocals]
    return SongInfo(
        id=song_id,
        name=str(data.get("songName", song_id)) if isinstance(data, dict) else song_id,
        artist=str(data.get("artist", "")) if isinstance(data, dict) else "",
        charter=str(data.get("charter", "")) if isinstance(data, dict) else "",
        difficulties=list(difficulties),
        variations=[str(v) for v in variations],
        instrumental=str(chars.get("instrumental", "")) if isinstance(chars, dict) else "",
        player_vocals=[str(v) for v in player_vocals],
        opponent_vocals=[str(v) for v in opponent_vocals],
        stage=str(play.get("stage", "mainStage")) if isinstance(play, dict) else "mainStage",
        player=str(chars.get("player", "bf")) if isinstance(chars, dict) else "bf",
        opponent=str(chars.get("opponent", "dad")) if isinstance(chars, dict) else "dad",
        girlfriend=str(chars.get("girlfriend", "gf")) if isinstance(chars, dict) else "gf",
        note_style=str(play.get("noteStyle", "funkin")) if isinstance(play, dict) else "funkin",
        bpm=bpm,
        metadata_path=path,
        source=source,
    )


def discover_songs(resolver: PathResolver) -> list[SongInfo]:
    songs: dict[str, SongInfo] = {}

    for meta in resolver.glob_all("preload/data/songs/*/*-metadata.json"):
        song_id = slug_from_metadata_path(meta)
        data = load_json(meta, default={})
        if isinstance(data, dict):
            songs[song_id] = parse_metadata(song_id, data, meta, source=str(meta))

    for meta in resolver.glob_all("data/songs/*/*-metadata.json"):
        song_id = slug_from_metadata_path(meta)
        if song_id not in songs:
            data = load_json(meta, default={})
            if isinstance(data, dict):
                songs[song_id] = parse_metadata(song_id, data, meta, source=str(meta))

    for meta in resolver.glob_all("songs/*/*-metadata.json"):
        song_id = slug_from_metadata_path(meta)
        if song_id not in songs:
            data = load_json(meta, default={})
            if isinstance(data, dict):
                songs[song_id] = parse_metadata(song_id, data, meta, source=str(meta))

    # Audio-only discovery: lets /data/songs/tutorial show up even if metadata is missing.
    for audio in resolver.glob_all("songs/*/Inst.*"):
        song_id = audio.parent.name
        if song_id not in songs:
            songs[song_id] = SongInfo(id=song_id, name=song_id.replace("-", " ").title(), source=str(audio))

    return sorted(songs.values(), key=lambda s: s.display_name.lower())


def load_song_info(resolver: PathResolver, song_id: str) -> SongInfo:
    meta_path = resolver.resolve_any(resolver.metadata_candidates(song_id))
    if meta_path:
        data = load_json(meta_path, default={})
        if isinstance(data, dict):
            return parse_metadata(song_id, data, meta_path, source=str(meta_path))
    return SongInfo(id=song_id, name=song_id.replace("-", " ").title())


def load_song_variant_info(resolver: PathResolver, song_id: str, variation: str | None = None) -> SongInfo:
    base = load_song_info(resolver, song_id)
    if not variation:
        return base
    meta_path = resolver.resolve_any(resolver.metadata_candidates(song_id, variation))
    if not meta_path:
        return base
    data = load_json(meta_path, default={})
    if not isinstance(data, dict):
        return base
    variant = parse_metadata(song_id, data, meta_path, source=str(meta_path))
    if not variant.variations:
        variant.variations = list(base.variations)
    return variant
