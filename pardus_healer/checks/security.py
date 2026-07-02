"""Güvenlik odaklı kontroller: güvenlik duvarı ve bekleyen yeniden başlatma."""

from __future__ import annotations

import os

from ..core.check import BaseCheck
from ..core.models import Fix
from ..core.shell import run, which


class FirewallCheck(BaseCheck):
    id = "firewall"
    title = "Güvenlik Duvarı (UFW)"
    icon = "🔥"
    category = "Güvenlik"
    weight = 1.0
    default_fix = Fix(
        "Güvenlik Duvarını Etkinleştir",
        "pkexec ufw --force enable",
        needs_root=True,
        description="UFW güvenlik duvarını etkinleştirir.",
    )

    def run(self):
        if not which("ufw"):
            return self.info(
                "UFW kurulu değil.",
                detail="Güvenlik duvarı yönetimi için ufw paketi bulunamadı.",
                recommendation="İsterseniz 'ufw' paketini kurabilirsiniz.",
            )
        # 'ufw status' root gerektirir; root değilsek yorum yapmayalım.
        res = run(["ufw", "status"], timeout=10)
        if not res.ok:
            is_root = getattr(os, "geteuid", lambda: 1)() == 0
            if not is_root:
                return self.unknown(
                    "Güvenlik duvarı durumu için yetki gerekiyor.",
                    detail="Durum bilgisi root olmadan okunamadı.",
                )
            return self.unknown("Güvenlik duvarı durumu okunamadı.")

        out = res.stdout.lower()
        if "status: active" in out:
            return self.ok(
                "Güvenlik duvarı etkin.",
                detail="UFW aktif ve gelen bağlantıları filtreliyor.",
            )
        return self.warn(
            "Güvenlik duvarı kapalı.",
            detail="UFW kurulu ama etkin değil.",
            root_cause="Gelen bağlantılar filtrelenmiyor.",
            recommendation="Güvenliğiniz için güvenlik duvarını etkinleştirin.",
        )


class PendingRebootCheck(BaseCheck):
    id = "pending_reboot"
    title = "Yeniden Başlatma Gereksinimi"
    icon = "🔁"
    category = "Sistem"
    weight = 0.7

    def run(self):
        # Debian/Pardus güncelleme sonrası bu dosyayı oluşturur.
        if os.path.exists("/var/run/reboot-required") or os.path.exists(
            "/run/reboot-required"
        ):
            return self.warn(
                "Sistemin yeniden başlatılması gerekiyor.",
                detail="Bir güncelleme, değişikliklerin tamamlanması için "
                "yeniden başlatma istiyor.",
                root_cause="Çekirdek veya çekirdek kütüphaneleri güncellendi.",
                recommendation="Uygun bir zamanda bilgisayarı yeniden başlatın.",
            )
        return self.ok(
            "Yeniden başlatma gerekmiyor.",
            detail="Bekleyen bir yeniden başlatma isteği yok.",
        )
