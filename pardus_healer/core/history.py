"""Sağlık skoru geçmişi — taramaların zaman içindeki kaydı.

Her tarama sonunda küçük bir özet (skor, not, sayımlar, zaman) ~/.config
altında JSON olarak saklanır. Böylece dashboard skorun trendini gösterebilir.
Depolama hataları sessizce yok sayılır; geçmiş hiçbir zaman uygulamayı
çökertmez.
"""

from __future__ import annotations

import datetime
import json
import os
from dataclasses import asdict, dataclass


def _history_path() -> str:
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
        os.path.expanduser("~"), ".config"
    )
    return os.path.join(base, "pardus-healer", "history.json")


@dataclass
class HistoryEntry:
    timestamp: str
    score: int
    grade: str
    fail: int
    warn: int
    ok: int


class History:
    """Sağlık skoru geçmişini yöneten basit, dosya tabanlı depo."""

    def __init__(self, max_entries: int = 60):
        self.max_entries = max_entries
        self.entries: list[HistoryEntry] = []
        self.load()

    def load(self) -> None:
        try:
            with open(_history_path(), "r", encoding="utf-8") as fh:
                data = json.load(fh)
            self.entries = [
                HistoryEntry(**e) for e in data if isinstance(e, dict)
            ][-self.max_entries:]
        except (OSError, ValueError, TypeError):
            self.entries = []

    def save(self) -> None:
        path = _history_path()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump([asdict(e) for e in self.entries], fh, indent=2)
        except OSError:
            pass

    def add(self, score: int, grade: str, fail: int, warn: int, ok: int) -> None:
        entry = HistoryEntry(
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            score=score, grade=grade, fail=fail, warn=warn, ok=ok,
        )
        self.entries.append(entry)
        self.entries = self.entries[-self.max_entries:]
        self.save()

    def scores(self) -> list[int]:
        return [e.score for e in self.entries]

    def last(self) -> HistoryEntry | None:
        return self.entries[-1] if self.entries else None

    def trend(self) -> int:
        """Son iki tarama arasındaki skor farkı (+iyileşme / -kötüleşme)."""
        if len(self.entries) < 2:
            return 0
        return self.entries[-1].score - self.entries[-2].score
