"""Açılış (boot) süresi kontrolü.

Okul/paylaşımlı makinelerde en sık şikayet 'sistem çok geç açılıyor'.
Bu kontrol systemd-analyze ile toplam açılış süresini ölçer ve gerektiğinde
en yavaş servisleri işaret eder.
"""

from __future__ import annotations

import re

from ..core.check import BaseCheck
from ..core.models import Metric
from ..core.shell import run, which

_TOTAL_RE = re.compile(r"^\s*(?:(\d+)h\s*)?(?:(\d+)min\s*)?([\d.]+)s")


class BootTimeCheck(BaseCheck):
    id = "boot_time"
    title = "Açılış Süresi"
    icon = "🚀"
    category = "Sistem"
    weight = 0.6

    WARN_SEC = 60
    FAIL_SEC = 120

    def run(self):
        if not which("systemd-analyze"):
            return self.unknown(
                "systemd-analyze bulunamadı.",
                detail="Açılış süresi ölçülemiyor.",
            )
        res = run(["systemd-analyze", "time"], timeout=15)
        if not res.ok and not res.stdout:
            return self.unknown("Açılış süresi okunamadı.")

        seconds = self._parse_total(res.stdout)
        if seconds is None:
            return self.unknown("Açılış süresi ayrıştırılamadı.")

        metric = Metric(round(seconds, 1), "sn")
        base = f"Son açılış {seconds:.0f} saniye sürdü."
        slow = self._slowest_units()
        if slow:
            base += f" En yavaş: {slow}."

        if seconds >= self.FAIL_SEC:
            return self.fail(
                f"Açılış çok yavaş. ({seconds:.0f} sn)",
                detail=base,
                metric=metric,
                root_cause="Bazı servisler açılışta uzun sürüyor olabilir.",
                recommendation="Gereksiz başlangıç servislerini gözden geçirin.",
            )
        if seconds >= self.WARN_SEC:
            return self.warn(
                f"Açılış biraz yavaş. ({seconds:.0f} sn)",
                detail=base,
                metric=metric,
            )
        return self.ok(
            f"Açılış hızlı. ({seconds:.0f} sn)",
            detail=base,
            metric=metric,
        )

    @staticmethod
    def _parse_total(text: str):
        # örnek: "Startup finished in 4.2s (kernel) + 12.6s (userspace) = 16.8s"
        # 60 sn'yi aşan açılışlarda systemd toplamı "1min 7.311s" biçiminde
        # yazar — bu yüzden yalnızca saf saniye değil, saat/dakika/saniye
        # bileşenlerini de ayrıştırıp topluyoruz (bkz. TECHNICAL_AUDIT.md
        # Kol 1, madde: "açılış süresi 60sn+ yanlış hesaplanıyor").
        for line in text.splitlines():
            line = line.strip()
            idx = line.rfind("=")
            if idx == -1:
                continue
            total = BootTimeCheck._parse_duration(line[idx + 1:])
            if total is not None:
                return total
        # Tek satırlık/basit çıktılar için son çare: metnin başındaki süreyi dene.
        return BootTimeCheck._parse_duration(text.strip())

    @staticmethod
    def _parse_duration(segment: str):
        m = _TOTAL_RE.match(segment.strip())
        if not m:
            return None
        hours = float(m.group(1)) if m.group(1) else 0.0
        minutes = float(m.group(2)) if m.group(2) else 0.0
        try:
            seconds = float(m.group(3))
        except ValueError:
            return None
        return hours * 3600 + minutes * 60 + seconds

    def _slowest_units(self) -> str:
        if not which("systemd-analyze"):
            return ""
        res = run(["systemd-analyze", "blame", "--no-pager"], timeout=15)
        if not res.ok:
            return ""
        lines = [ln.strip() for ln in res.stdout.splitlines() if ln.strip()]
        if not lines:
            return ""
        # ilk satır en yavaş servistir: "12.345s  servis.service"
        parts = lines[0].split()
        if len(parts) >= 2:
            return f"{parts[-1]} ({parts[0]})"
        return ""
