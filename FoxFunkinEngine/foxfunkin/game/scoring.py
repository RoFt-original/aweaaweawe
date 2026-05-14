from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ScoreState:
    windows: dict[str, float]
    score: int = 0
    combo: int = 0
    max_combo: int = 0
    misses: int = 0
    hits: int = 0
    total_notes: int = 0
    rating_counts: dict[str, int] = field(default_factory=lambda: {"sick": 0, "good": 0, "bad": 0, "shit": 0, "miss": 0})
    health: float = 1.0
    last_rating: str = ""

    def judge(self, diff_ms: float) -> str | None:
        ad = abs(diff_ms)
        for name in ("sick", "good", "bad", "shit"):
            if ad <= float(self.windows.get(name, 166)):
                return name
        return None

    def register_hit(self, diff_ms: float) -> str:
        rating = self.judge(diff_ms) or "shit"
        values = {"sick": 350, "good": 200, "bad": 100, "shit": 50}
        self.score += values.get(rating, 50)
        self.combo += 1
        self.max_combo = max(self.max_combo, self.combo)
        self.hits += 1
        self.rating_counts[rating] = self.rating_counts.get(rating, 0) + 1
        self.health = min(2.0, self.health + {"sick": 0.035, "good": 0.025, "bad": 0.012, "shit": 0.006}.get(rating, 0.01))
        self.last_rating = rating.upper()
        return rating

    def register_miss(self) -> None:
        self.combo = 0
        self.misses += 1
        self.rating_counts["miss"] = self.rating_counts.get("miss", 0) + 1
        self.health = max(0.0, self.health - 0.08)
        self.last_rating = "MISS"

    @property
    def accuracy(self) -> float:
        weighted = (
            self.rating_counts.get("sick", 0) * 1.0 +
            self.rating_counts.get("good", 0) * 0.75 +
            self.rating_counts.get("bad", 0) * 0.45 +
            self.rating_counts.get("shit", 0) * 0.2
        )
        total = self.hits + self.misses
        return 0.0 if total == 0 else max(0.0, min(100.0, weighted / total * 100.0))

    @property
    def rank(self) -> str:
        acc = self.accuracy
        if self.misses == 0 and acc >= 99.5:
            return "FC SICK"
        if acc >= 95:
            return "S"
        if acc >= 90:
            return "A"
        if acc >= 80:
            return "B"
        if acc >= 70:
            return "C"
        return "D"
