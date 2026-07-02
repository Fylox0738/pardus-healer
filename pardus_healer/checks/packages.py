"""Bozuk / yarım yapılandırılmış paket kontrolü."""

from __future__ import annotations

from ..core.check import BaseCheck
from ..core.models import Fix
from ..core.shell import run, which


class BrokenPackagesCheck(BaseCheck):
    id = "broken_packages"
    title = "Bozuk Paketler"
    icon = "🔧"
    category = "Paketler"
    weight = 1.3
    default_fix = Fix(
        "Bozuk Paketleri Düzelt",
        "pkexec apt-get install -f -y",
        needs_root=True,
        description="Eksik bağımlılıkları tamamlar, yarım paketleri onarır.",
    )

    def run(self):
        if not which("dpkg"):
            return self.unknown("dpkg bulunamadı.")

        res = run(["dpkg", "--audit"], timeout=30)
        broken = res.stdout.strip()
        if res.ok and not broken:
            return self.ok(
                "Bozuk paket yok.",
                detail="dpkg --audit temiz.",
            )
        # Kaç paketin etkilendiğini kabaca say.
        count = sum(
            1 for line in broken.splitlines()
            if line and not line.startswith(" ")
        )
        return self.fail(
            f"{count} bozuk/yarım paket tespit edildi!"
            if count else "Bozuk paketler tespit edildi!",
            detail=broken[:800],
            root_cause="Kesintiye uğramış bir kurulum ya da güç kaybı "
            "paketleri yarım bırakmış olabilir.",
            recommendation="Bozuk paketleri düzelt komutunu çalıştırın.",
        )
