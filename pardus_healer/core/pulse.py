"""Pardus Nabız: SOS Kartı olaylarının opt-in, anonim, yerel birikimi.

Hiçbir sunucuya veri göndermez — tamamen yerel bir JSONL dosyasına
yazılır (`~/.local/share/pardus-healer/pulse.jsonl`). Amaç, bireysel bir
onarım aracını "bu hafta hangi ilçelerde hangi sorun tekrarlanıyor?"
sorusuna cevap verebilen toplu bir görünürlüğe çevirmektir — kullanıcı
her seferinde açıkça onay verdiğinde (opt-in) bir satır eklenir.

Gerçek bir sunucu/aggregation altyapısı bu aşamada YOK; `seed_demo_data()`
yalnızca demo/jüri sunumu için örnek (uydurma) satırlar ekler.

Demo veri, gerçek kullanıcı verisiyle KARIŞMAMASI için ayrı bir dosyada
(`pulse_demo.jsonl`) saklanır ve `load_events()`/`top_issues()` her demo
kaydını `is_demo=True` ile işaretler — böylece arayüz ikisini hiçbir zaman
ayrım yapmadan tek bir sayıya karıştırmaz.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

_PULSE_FILE = Path.home() / ".local" / "share" / "pardus-healer" / "pulse.jsonl"
_DEMO_FILE = Path.home() / ".local" / "share" / "pardus-healer" / "pulse_demo.jsonl"


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


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    events: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def load_events(include_demo: bool = False) -> list[dict]:
    """Gerçek (kullanıcı onaylı) SOS olaylarını döndürür.

    ``include_demo=True`` verilirse ``pulse_demo.jsonl``'daki örnek veri de
    eklenir, ama her demo kaydı ``is_demo=True`` ile işaretlenir.
    """
    real = _load_jsonl(_PULSE_FILE)
    for e in real:
        e.setdefault("is_demo", False)
    if not include_demo:
        return real
    demo = _load_jsonl(_DEMO_FILE)
    for e in demo:
        e["is_demo"] = True
    return real + demo


def has_demo_data() -> bool:
    return _DEMO_FILE.exists() and _DEMO_FILE.stat().st_size > 0


def clear_demo_data() -> None:
    """Demo verisini kalıcı olarak siler (gerçek veriye dokunmaz)."""
    try:
        _DEMO_FILE.unlink()
    except OSError:
        pass


def top_issues(
    events: list[dict], limit: int = 5
) -> list[tuple[str, int, int, list[str]]]:
    """(sorun_basligi, gerçek_sayı, demo_sayı, bölge_listesi) — sık görülenden aza.

    Gerçek ve demo sayıları HER ZAMAN ayrı döner; arayüz bunları tek bir
    toplam sayıya karıştırmadan, demo olanı açıkça etiketleyerek gösterir.
    """
    grouped: dict[str, list[dict]] = {}
    for e in events:
        grouped.setdefault(e.get("issue", "Bilinmiyor"), []).append(e)
    ranked = sorted(grouped.items(), key=lambda kv: len(kv[1]), reverse=True)
    result = []
    for issue, items in ranked[:limit]:
        real_items = [it for it in items if not it.get("is_demo")]
        demo_items = [it for it in items if it.get("is_demo")]
        regions = sorted({it.get("region", "Belirtilmedi") for it in items})
        result.append((issue, len(real_items), len(demo_items), regions))
    return result


def seed_demo_data() -> int:
    """Demo/jüri sunumu için örnek (uydurma, anonim) bölgesel veri ekler.

    Bu veri gerçek kullanıcı verisiyle AYNI dosyaya değil, ayrı bir
    ``pulse_demo.jsonl`` dosyasına yazılır.
    Dönüş: eklenen satır sayısı.
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
    _DEMO_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(_DEMO_FILE, "a", encoding="utf-8") as f:
        for issue, region in demo:
            entry = {"ts": time.time(), "issue": issue, "region": region}
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return len(demo)
