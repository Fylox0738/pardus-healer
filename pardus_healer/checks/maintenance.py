"""Bakım kontrolleri: geri kazanılabilir disk alanı (önbellek/çöp temizliği).

Okul/paylaşımlı makinelerde biriken APT önbelleği, eski günlükler ve küçük
resim önbelleği zamanla gigabaytları yer. Bu kontrol ne kadar alan geri
kazanılabileceğini ölçer ve tek tıkla güvenli temizlik sunar.
"""

from __future__ import annotations

import os

from ..core.check import BaseCheck
from ..core.models import Fix, Metric
from ..core.shell import run, which


def _dir_size(path: str, cap_bytes: int = 20 * 1024 ** 3) -> int:
    """Bir dizinin toplam boyutu (bayt). Erişilemeyen dosyalar atlanır."""
    total = 0
    try:
        for root, _dirs, files in os.walk(path, onerror=lambda e: None):
            for name in files:
                try:
                    total += os.path.getsize(os.path.join(root, name))
                except OSError:
                    pass
            if total > cap_bytes:
                return total
    except OSError:
        pass
    return total


class CacheCleanupCheck(BaseCheck):
    id = "cache_cleanup"
    title = "Temizlenebilir Alan"
    icon = "🧹"
    category = "Bakım"
    weight = 0.7
    default_fix = Fix(
        "Şimdi Temizle",
        "pkexec sh -c 'apt-get clean && journalctl --vacuum-size=200M'",
        needs_root=True,
        description="APT önbelleğini boşaltır ve eski sistem günlüklerini "
        "200 MB ile sınırlar.",
    )

    WARN_MB = 500       # bu kadar üstü temizlik öner
    INFO_MB = 50

    def run(self):
        reclaimable = 0

        # APT indirilen paket önbelleği
        reclaimable += _dir_size("/var/cache/apt/archives")

        # kullanıcının küçük resim önbelleği
        cache_home = os.environ.get("XDG_CACHE_HOME") or os.path.join(
            os.path.expanduser("~"), ".cache")
        reclaimable += _dir_size(os.path.join(cache_home, "thumbnails"))

        # sistem günlüğü disk kullanımı (varsa)
        if which("journalctl"):
            res = run(["journalctl", "--disk-usage"], timeout=10)
            reclaimable += self._parse_journal_usage(res.stdout)

        mb = reclaimable / (1024 * 1024)
        metric = Metric(round(mb, 1), "MB")
        human = f"{mb / 1024:.1f} GB" if mb >= 1024 else f"{mb:.0f} MB"
        base = f"Yaklaşık {human} önbellek/çöp temizlenebilir."

        if mb >= self.WARN_MB:
            return self.warn(
                f"{human} boşaltılabilir.",
                detail=base,
                metric=metric,
                root_cause="Zamanla biriken paket önbelleği ve eski günlükler "
                "yer kaplıyor.",
                recommendation="Tek tıkla temizleyerek yer açabilirsiniz.",
            )
        if mb >= self.INFO_MB:
            return self.info(
                f"{human} önbellek mevcut.",
                detail=base + " (henüz temizlik şart değil.)",
                metric=metric,
            )
        return self.ok(
            "Temizlenecek önemli bir birikim yok.",
            detail=base,
            metric=metric,
        )

    @staticmethod
    def _parse_journal_usage(text: str) -> int:
        """'Archived and active journals take up 512.0M ...' → bayt."""
        if not text:
            return 0
        import re
        m = re.search(r"take up\s+([\d.]+)\s*([KMGT])", text)
        if not m:
            return 0
        value = float(m.group(1))
        mult = {"K": 1024, "M": 1024 ** 2, "G": 1024 ** 3, "T": 1024 ** 4}
        return int(value * mult.get(m.group(2), 1))
