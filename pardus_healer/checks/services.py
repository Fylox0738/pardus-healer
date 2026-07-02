"""systemd servis durumu kontrolü."""

from __future__ import annotations

from ..core.check import BaseCheck
from ..core.models import Fix
from ..core.shell import run, which


class FailedServicesCheck(BaseCheck):
    id = "failed_services"
    title = "Sistem Servisleri"
    icon = "🧩"
    category = "Sistem"
    weight = 1.2
    default_fix = Fix(
        "Başarısız Servisleri Sıfırla",
        "pkexec systemctl reset-failed",
        needs_root=True,
        description="Başarısız servis kayıtlarını temizler (yeniden dener).",
    )

    def run(self):
        if not which("systemctl"):
            return self.unknown(
                "systemctl bulunamadı.",
                detail="Bu sistem systemd kullanmıyor olabilir.",
            )

        res = run(
            ["systemctl", "--failed", "--no-legend", "--plain", "--no-pager"],
            timeout=20,
        )
        if res.timed_out:
            return self.warn("Servis durumu zaman aşımına uğradı.")

        lines = [ln for ln in res.stdout.splitlines() if ln.strip()]
        if not lines:
            return self.ok(
                "Tüm servisler çalışıyor.",
                detail="Başarısız (failed) durumda servis yok.",
            )

        names = [ln.split()[0] for ln in lines]
        preview = ", ".join(names[:5])
        if len(names) > 5:
            preview += f" (+{len(names) - 5} tane daha)"
        return self.fail(
            f"{len(names)} servis başarısız durumda!",
            detail="Başarısız servisler:\n" + "\n".join(names),
            root_cause=f"Şu servis(ler) başlatılamadı: {preview}",
            recommendation="İlgili servisin günlüklerini inceleyin; geçici "
            "hata ise servisleri sıfırlayıp yeniden başlatın.",
        )
