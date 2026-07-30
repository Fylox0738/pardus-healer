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

    # Yalnızca "/" kontrol ediliyordu — okul/kurum kurulumlarında sık
    # görülen ayrı "/home" bölümü doluysa (kök diskte hâlâ bolca yer varken)
    # bu tamamen kaçırılıyordu. "/home" ayrı bir
    # bölüm değilse (aynı dosya sistemini paylaşıyorsa) tekilleştirilip
    # yalnızca bir kez raporlanır.
    MOUNTS_TO_CHECK = ["/", "/home"]

    def run(self):
        readings = []
        for mount in self.MOUNTS_TO_CHECK:
            if not os.path.isdir(mount):
                continue
            try:
                st = os.statvfs(mount)
            except (OSError, AttributeError):
                # statvfs Windows'ta yok; Linux dışı ortamda bilinemez.
                continue
            total = st.f_frsize * st.f_blocks
            if total == 0:
                continue
            free = st.f_frsize * st.f_bavail
            used = total - (st.f_frsize * st.f_bfree)
            pct = int(used / total * 100)
            readings.append((mount, pct, free / (1024 ** 3)))

        if not readings:
            return self.unknown("Disk bilgisi bu ortamda alınamıyor.")

        seen = set()
        uniq = []
        for mount, pct, free_gb in readings:
            key = (pct, round(free_gb, 1))
            if key in seen:
                continue
            seen.add(key)
            uniq.append((mount, pct, free_gb))

        mount, pct, free_gb = max(uniq, key=lambda t: t[1])
        metric = Metric(pct, "%", percent=pct)
        label = "kök disk" if mount == "/" else f"'{mount}' bölümü"
        base = f"Boş alan: {free_gb:.1f} GB — {label} %{pct} dolu."
        others = [f"{m} %{p}" for m, p, _ in uniq if (m, p) != (mount, pct)]
        if others:
            base += f" (Diğer izlenen bölümler: {', '.join(others)})"

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
