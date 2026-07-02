"""Bellek (RAM) ve takas (swap) kullanım kontrolleri."""

from __future__ import annotations

from ..core.check import BaseCheck
from ..core.models import Metric
from ..core.shell import read_file


def _read_meminfo() -> dict[str, int]:
    """/proc/meminfo değerlerini kB cinsinden sözlük olarak döndürür."""
    text = read_file("/proc/meminfo")
    data: dict[str, int] = {}
    if not text:
        return data
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].endswith(":"):
            try:
                data[parts[0][:-1]] = int(parts[1])
            except ValueError:
                pass
    return data


class RamUsageCheck(BaseCheck):
    id = "ram"
    title = "RAM Kullanımı"
    icon = "🧠"
    category = "Donanım"
    weight = 1.0

    WARN_PCT = 80
    FAIL_PCT = 92

    def run(self):
        mem = _read_meminfo()
        total = mem.get("MemTotal", 0)
        avail = mem.get("MemAvailable")
        if not total or avail is None:
            return self.unknown("RAM bilgisi bu ortamda okunamadı.")

        used = total - avail
        pct = int(used / total * 100)
        used_gb = used / (1024 * 1024)
        total_gb = total / (1024 * 1024)
        metric = Metric(pct, "%", percent=pct)
        base = f"{used_gb:.1f} / {total_gb:.1f} GB kullanımda (%{pct})."

        if pct >= self.FAIL_PCT:
            return self.fail(
                f"RAM kritik seviyede! (%{pct})",
                detail=base,
                metric=metric,
                root_cause="Bellek dolmak üzere; sistem takasa yönelip "
                "yavaşlayabilir.",
                recommendation="Kullanılmayan uygulamaları kapatın.",
            )
        if pct >= self.WARN_PCT:
            return self.warn(
                f"RAM kullanımı yüksek. (%{pct})",
                detail=base,
                metric=metric,
            )
        return self.ok(f"RAM kullanımı normal. (%{pct})", detail=base, metric=metric)


class SwapUsageCheck(BaseCheck):
    id = "swap"
    title = "Takas (Swap) Kullanımı"
    icon = "♻️"
    category = "Donanım"
    weight = 0.6

    WARN_PCT = 50

    def run(self):
        mem = _read_meminfo()
        total = mem.get("SwapTotal", 0)
        free = mem.get("SwapFree", 0)
        if total == 0:
            return self.info(
                "Takas alanı tanımlı değil.",
                detail="SwapTotal = 0. Bu bir sorun olmayabilir.",
            )
        used = total - free
        pct = int(used / total * 100)
        used_gb = used / (1024 * 1024)
        total_gb = total / (1024 * 1024)
        metric = Metric(pct, "%", percent=pct)
        base = f"{used_gb:.1f} / {total_gb:.1f} GB takas kullanımda (%{pct})."
        if pct >= self.WARN_PCT:
            return self.warn(
                f"Takas kullanımı yüksek. (%{pct})",
                detail=base,
                metric=metric,
                root_cause="RAM yetersiz kaldığında sistem takas kullanır; "
                "bu belirgin yavaşlamaya yol açar.",
                recommendation="Bellek tüketen uygulamaları azaltmayı düşünün.",
            )
        return self.ok(f"Takas kullanımı normal. (%{pct})", detail=base, metric=metric)
