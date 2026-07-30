"""Yazıcı (CUPS) tanı kontrolü.

Pardus forumlarında en sık tekrarlanan gerçek şikayetlerden biri
"yazıcım çalışmıyor" sınıfıdır (bkz. DEVELOPMENT_OPPORTUNITIES.md #2).
CUPS servisinin durumunu ve tanımlı yazıcıların durumunu kontrol eder.
"""

from __future__ import annotations

from ..core.check import BaseCheck
from ..core.models import Fix
from ..core.shell import run, which


class PrinterCheck(BaseCheck):
    id = "printer"
    title = "Yazıcı (CUPS)"
    icon = "🖨️"
    category = "Donanım"
    weight = 0.5
    default_fix = Fix(
        "CUPS Servisini Başlat",
        "pkexec sh -c 'apt-get install -y cups && systemctl enable --now cups'",
        needs_root=True,
        description="CUPS yazdırma servisini kurar ve başlatır.",
    )

    def run(self):
        if not which("lpstat"):
            return self.info(
                "CUPS (yazdırma sistemi) kurulu değil.",
                detail="Yazıcı kullanmıyorsanız bu normaldir.",
            )

        if not self._service_active("cups"):
            return self.warn(
                "CUPS servisi çalışmıyor.",
                detail="Yazıcılar bu servis olmadan kullanılamaz.",
                root_cause="cups.service durdurulmuş ya da devre dışı.",
                recommendation="CUPS servisini başlatın.",
            )

        res = run(["lpstat", "-p"], timeout=10)
        printers = [ln for ln in res.stdout.splitlines() if ln.startswith("printer ")]
        if not printers:
            return self.info(
                "Tanımlı yazıcı bulunamadı.",
                detail="CUPS çalışıyor ama sisteme eklenmiş bir yazıcı yok.",
                recommendation="Ayarlar > Yazıcılar'dan yeni yazıcı ekleyin.",
            )

        disabled = [ln for ln in printers if "disabled" in ln.lower()]
        if disabled:
            names = ", ".join(ln.split()[1] for ln in disabled if len(ln.split()) > 1)
            return self.warn(
                f"{len(disabled)} yazıcı devre dışı: {names}",
                detail="\n".join(disabled),
                root_cause="Yazıcı sıkışması, kağıt/mürekkep hatası ya da "
                "manuel olarak durdurulmuş olabilir.",
                recommendation="Yazıcı kuyruğunu kontrol edip yeniden "
                "etkinleştirin (cupsenable <yazıcı_adı>).",
            )

        return self.ok(
            f"{len(printers)} yazıcı tanımlı, hepsi etkin.",
            detail="\n".join(printers),
        )

    @staticmethod
    def _service_active(name: str) -> bool:
        if not which("systemctl"):
            return False
        res = run(["systemctl", "is-active", "--quiet", name], timeout=10)
        return res.ok
