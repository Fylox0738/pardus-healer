"""Pardus Nabız: SOS Kartı olaylarının opt-in, anonim, yerel birikimi.

Hiçbir sunucuya veri göndermez — tamamen yerel bir JSONL dosyasına
yazılır (`~/.local/share/pardus-healer/pulse.jsonl`). Amaç, bireysel bir
onarım aracını "bu hafta hangi ilçelerde hangi sorun tekrarlanıyor?"
sorusuna cevap verebilen toplu bir görünürlüğe çevirmektir — kullanıcı
her seferinde açıkça onay verdiğinde (opt-in) bir satır eklenir.

Gerçek bir sunucu/aggregation altyapısı bu aşamada YOK; `seed_demo_data()`
yalnızca demo/jüri sunumu için örnek (uydurma) satırlar ekler.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

_PULSE_FILE = Path.home() / ".local" / "share" / "pardus-healer" / "pulse.jsonl"


def record_event(issue_title: str, region: str = "") -> None:
    """Kullanıcı açıkça onay verdiğinde bir SOS olayını yerel günlüğe ekler.

    Kişisel/tanımlayıcı veri içermez: yalnızca sorun başlığı ve
    kullanıcının kendi girdiği serbest metin bölge adı (isteğe bağlı).
    """
    _PULSE_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": time.time(),
        "issue": issue_title,
        "region": region.strip() or "Belirtilmedi",
    }
    with open(_PULSE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_events() -> list[dict]:
    if not _PULSE_FILE.exists():
        return []
    events: list[dict] = []
    with open(_PULSE_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def top_issues(events: list[dict], limit: int = 5) -> list[tuple[str, int, list[str]]]:
    """(sorun_basligi, toplam_sayi, bölge_listesi) — en sık görülenden aza sıralı."""
    grouped: dict[str, list[str]] = {}
    for e in events:
        grouped.setdefault(e.get("issue", "Bilinmiyor"), []).append(
            e.get("region", "Belirtilmedi")
        )
    ranked = sorted(grouped.items(), key=lambda kv: len(kv[1]), reverse=True)
    return [
        (issue, len(regions), sorted(set(regions)))
        for issue, regions in ranked[:limit]
    ]


def seed_demo_data() -> int:
    """Demo/jüri sunumu için örnek (uydurma, anonim) bölgesel veri ekler.

    Dönüş: eklenen satır sayısı. Gerçek kullanıcı verisiyle karışmaması
    için yalnızca demo modunda, açıkça çağrıldığında kullanılmalı.
    """
    demo = [
        ("NetworkManager bağlantı sorunu", "Kadıköy"),
        ("NetworkManager bağlantı sorunu", "Üsküdar"),
        ("NetworkManager bağlantı sorunu", "Beşiktaş"),
        ("NetworkManager bağlantı sorunu", "Kadıköy"),
        ("Disk alanı kritik seviyede", "Kadıköy"),
        ("Disk alanı kritik seviyede", "Şişli"),
        ("Bozuk paketler tespit edildi", "Üsküdar"),
    ]
    for issue, region in demo:
        record_event(issue, region)
    return len(demo)
