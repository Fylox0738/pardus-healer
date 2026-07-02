"""Masaüstü bildirimi yardımcısı.

`notify-send` varsa kritik tanı sonuçlarında masaüstü bildirimi gösterir.
Yoksa sessizce hiçbir şey yapmaz (uygulamayı asla etkilemez).
"""

from __future__ import annotations

from .shell import run, which


def send(title: str, body: str, urgency: str = "normal") -> bool:
    """Bir masaüstü bildirimi gönderir. Başarılıysa True döner."""
    if not which("notify-send"):
        return False
    res = run(
        ["notify-send", "-a", "Pardus Healer", "-u", urgency, title, body],
        timeout=5,
    )
    return res.ok


def notify_report(fail_count: int, warn_count: int, score: int) -> None:
    """Tarama sonucuna göre uygun bir bildirim gösterir."""
    if fail_count > 0:
        send(
            f"⚠ {fail_count} sorun tespit edildi",
            f"Sağlık skoru: {score}/100. Ayrıntılar için Pardus Healer'ı açın.",
            urgency="critical",
        )
    elif warn_count > 0:
        send(
            f"{warn_count} uyarı var",
            f"Sağlık skoru: {score}/100.",
            urgency="normal",
        )
