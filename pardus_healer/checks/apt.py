"""APT paket sistemi sağlık kontrolü."""

from __future__ import annotations

from ..core.check import BaseCheck
from ..core.models import Fix
from ..core.shell import run, which


class AptHealthCheck(BaseCheck):
    id = "apt_health"
    title = "APT Depo Sağlığı"
    icon = "📦"
    category = "Paketler"
    weight = 1.2
    default_fix = Fix(
        "Depoları Onar",
        "pkexec sh -c 'apt-get update && dpkg --configure -a'",
        needs_root=True,
        description="Depo listesini günceller ve yarım kalan yapılandırmaları tamamlar.",
    )

    def run(self):
        if not which("apt-get"):
            return self.unknown(
                "apt-get bulunamadı.",
                detail="Bu sistem APT tabanlı görünmüyor.",
            )

        # 'apt-get check' bağımlılık tutarlılığını doğrular; root gerektirmez.
        res = run(["apt-get", "check"], timeout=40)
        if res.timed_out:
            return self.warn(
                "APT kontrolü zaman aşımına uğradı.",
                detail="apt-get check 40 sn içinde tamamlanmadı.",
                recommendation="Sistem yoğunsa tekrar deneyin.",
            )
        if res.ok:
            return self.ok(
                "APT paket sistemi tutarlı.",
                detail="Bağımlılık ağacı sağlıklı.",
            )
        return self.fail(
            "APT paket sisteminde tutarsızlık var!",
            detail=res.out[:800],
            root_cause="Karşılanmayan bağımlılıklar ya da yarım kalmış "
            "kurulum/güncelleme olabilir.",
            recommendation="Depoları onarın; sorun sürerse bozuk paketleri "
            "düzeltin.",
        )
