from __future__ import annotations

from pathlib import Path
from typing import Any

from foxfunkin.core.jsonx import load_json, save_json


def score_key(song_id: str, difficulty: str, variation: str = "") -> str:
    return f"{song_id}:{variation or 'base'}:{difficulty}"


def load_highscores(root: Path) -> dict[str, Any]:
    data = load_json(root / "saves" / "highscores.json", default={})
    return data if isinstance(data, dict) else {}


def save_highscores(root: Path, data: dict[str, Any]) -> None:
    save_json(root / "saves" / "highscores.json", data)


def best_score(root: Path, song_id: str, difficulty: str, variation: str = "") -> dict[str, Any] | None:
    scores = load_highscores(root)
    value = scores.get(score_key(song_id, difficulty, variation))
    return value if isinstance(value, dict) else None


def update_highscore(root: Path, song_id: str, difficulty: str, variation: str, score_state) -> bool:
    scores = load_highscores(root)
    key = score_key(song_id, difficulty, variation)
    old = scores.get(key, {})
    old_score = int(old.get("score", -1)) if isinstance(old, dict) else -1
    if int(score_state.score) <= old_score:
        return False
    scores[key] = {
        "song": song_id,
        "difficulty": difficulty,
        "variation": variation or "",
        "score": int(score_state.score),
        "accuracy": round(float(score_state.accuracy), 3),
        "misses": int(score_state.misses),
        "max_combo": int(score_state.max_combo),
        "rank": str(score_state.rank),
    }
    save_highscores(root, scores)
    return True
