"""Bekleyen güncelleme ve güvenlik güncellemesi kontrolleri."""

from __future__ import annotations

import re

from ..core.check import BaseCheck
from ..core.models import Fix, Metric
from ..core.shell import run, which

_UPGRADE_RE = re.compile(r"(\d+)\s+upgraded")


def _count_upgradable() -> int | None:
    """`apt-get -s upgrade` simülasyonundan yükseltilebilir paket sayısı."""
    if not which("apt-get"):
        return None
    res = run(["apt-get", "-s", "upgrade"], timeout=40)
    if not res.stdout:
        return None
    for line in res.stdout.splitlines():
        m = _UPGRADE_RE.search(line)
        if m:
            return int(m.group(1))
    return 0


class UpdatesCheck(BaseCheck):
    id = "updates"
    title = "Bekleyen Güncellemeler"
    icon = "🔄"
    category = "Paketler"
    weight = 0.8
    default_fix = Fix(
        "Güncelle",
        "pkexec apt-get upgrade -y",
        needs_root=True,
        description="Bekleyen tüm paket güncellemelerini kurar.",
    )

    def run(self):
        count = _count_upgradable()
        if count is None:
            return self.unknown(
                "Güncelleme durumu okunamadı.",
                detail="apt-get simülasyonu sonuç vermedi.",
            )
        if count == 0:
            return self.ok(
                "Sistem güncel.",
                detail="Bekleyen güncelleme yok.",
                metric=Metric(0, "paket"),
            )
        status_msg = f"{count} paket güncellenebilir."
        metric = Metric(count, "paket")
        # Çok sayıda bekleyen güncelleme sadece bir uyarıdır, arıza değil.
        return self.warn(
            status_msg,
            detail=f"{count} adet paket için yeni sürüm mevcut.",
            metric=metric,
            recommendation="Uygun bir zamanda güncellemeleri kurun.",
        )


class SecurityUpdatesCheck(BaseCheck):
    id = "security_updates"
    title = "Güvenlik Güncellemeleri"
    icon = "🛡️"
    category = "Güvenlik"
    weight = 1.4
    default_fix = Fix(
        "Güvenlik Güncellemelerini Kur",
        "pkexec apt-get upgrade -y",
        needs_root=True,
        description="Bekleyen güncellemeleri kurar (güvenlik dahil).",
    )

    def run(self):
        if not which("apt-get"):
            return self.unknown("apt-get bulunamadı.")

        res = run(["apt-get", "-s", "upgrade"], timeout=40)
        if not res.stdout:
            return self.unknown("Güvenlik güncellemesi durumu okunamadı.")

        # Simülasyon çıktısında 'security' geçen 'Inst' satırlarını say.
        sec = 0
        for line in res.stdout.splitlines():
            if line.startswith("Inst") and "security" in line.lower():
                sec += 1

        if sec == 0:
            return self.ok(
                "Bekleyen güvenlik güncellemesi yok.",
                detail="Kritik güvenlik yamaları güncel.",
                metric=Metric(0, "yama"),
            )
        return self.fail(
            f"{sec} güvenlik güncellemesi bekliyor!",
            detail=f"{sec} adet güvenlikle ilgili paket güncellemesi mevcut.",
            metric=Metric(sec, "yama"),
            root_cause="Sisteminizde bilinen güvenlik açıkları için yamalar "
            "henüz kurulmamış.",
            recommendation="Güvenlik güncellemelerini en kısa sürede kurun.",
        )
