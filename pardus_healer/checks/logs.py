"""Sistem günlüğü (journal) hata taraması."""

from __future__ import annotations

from ..core.check import BaseCheck
from ..core.shell import run, which


class JournalErrorsCheck(BaseCheck):
    id = "journal_errors"
    title = "Sistem Günlüğü Hataları"
    icon = "📜"
    category = "Sistem"
    weight = 0.7

    # Bu eşiklerin altındaki hata sayısı normal kabul edilir (her sistemde
    # birkaç iyi huylu hata olur).
    WARN_THRESHOLD = 15
    FAIL_THRESHOLD = 60

    def run(self):
        if not which("journalctl"):
            return self.unknown(
                "journalctl bulunamadı.",
                detail="systemd günlüğü bu sistemde mevcut değil.",
            )

        # Son açılıştan bu yana öncelik 'err' ve üzeri girdiler.
        res = run(
            ["journalctl", "-p", "3", "-b", "--no-pager", "-q"],
            timeout=25,
        )
        if res.timed_out:
            return self.warn("Günlük taraması zaman aşımına uğradı.")
        if not res.ok and not res.stdout:
            return self.unknown(
                "Günlük okunamadı.",
                detail="journalctl'e erişim için yetki gerekebilir.",
            )

        lines = [ln for ln in res.stdout.splitlines() if ln.strip()]
        count = len(lines)
        tail = "\n".join(lines[-8:]) if lines else ""

        if count >= self.FAIL_THRESHOLD:
            return self.fail(
                f"Bu açılışta {count} hata kaydı var!",
                detail="Son hatalar:\n" + tail,
                root_cause="Tekrarlayan bir donanım/servis hatası günlüğü "
                "dolduruyor olabilir.",
                recommendation="Günlükteki en sık tekrar eden hatayı inceleyin.",
            )
        if count >= self.WARN_THRESHOLD:
            return self.warn(
                f"Bu açılışta {count} hata kaydı var.",
                detail="Son hatalar:\n" + tail,
                recommendation="Sık tekrarlıyorsa ilgili servisi kontrol edin.",
            )
        return self.ok(
            f"Günlük temiz. ({count} önemli hata)",
            detail="Kritik seviyede tekrarlayan hata yok.",
        )
