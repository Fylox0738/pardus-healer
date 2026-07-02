"""Disk doluluk kontrolü."""

from __future__ import annotations

import os

from ..core.check import BaseCheck
from ..core.models import Fix, Metric


class DiskSpaceCheck(BaseCheck):
    id = "disk"
    title = "Disk Doluluk Durumu"
    icon = "💾"
    category = "Donanım"
    weight = 1.4
    default_fix = Fix(
        "Disk Temizle",
        "pkexec sh -c 'apt-get clean && apt-get autoremove -y'",
        needs_root=True,
        description="APT önbelleğini boşaltır ve gereksiz paketleri kaldırır.",
    )

    WARN_PCT = 80
    FAIL_PCT = 90

    def run(self):
        try:
            st = os.statvfs("/")
        except (OSError, AttributeError):
            # statvfs Windows'ta yok; Linux dışı ortamda bilinemez.
            return self.unknown("Disk bilgisi bu ortamda alınamıyor.")

        total = st.f_frsize * st.f_blocks
        free = st.f_frsize * st.f_bavail
        if total == 0:
            return self.unknown("Disk bilgisi okunamadı.")

        used = total - (st.f_frsize * st.f_bfree)
        pct = int(used / total * 100)
        free_gb = free / (1024 ** 3)
        metric = Metric(pct, "%", percent=pct)
        base = f"Boş alan: {free_gb:.1f} GB — kök disk %{pct} dolu."

        if pct >= self.FAIL_PCT:
            return self.fail(
                f"Disk kritik seviyede dolu! (%{pct})",
                detail=base,
                metric=metric,
                root_cause="Kök bölüm dolmak üzere; güncelleme ve günlük "
                "işlemler başarısız olabilir.",
                recommendation="Önbelleği temizleyin, gereksiz dosya/paketleri "
                "kaldırın.",
            )
        if pct >= self.WARN_PCT:
            return self.warn(
                f"Disk dolmak üzere. (%{pct})",
                detail=base,
                metric=metric,
                recommendation="Yakında yer açmanız önerilir.",
            )
        return self.ok(
            f"Disk durumu normal. (%{pct})",
            detail=base,
            metric=metric,
        )
