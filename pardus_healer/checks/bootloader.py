"""Önyükleyici (GRUB) tanı kontrolü — GÜVENLİ ALT KÜME.

Yalnızca ``os-prober`` + ``update-grub`` (grub-mkconfig) ile GRUB menü
YAPILANDIRMASINI yeniden üretir; MBR/EFI'ye ``grub-install`` ile YENİDEN
YAZMA YAPMAZ (bu, hatalı kullanımda sistemi önyüklenemez hale getirebilecek
riskli bir işlemdir ve bilinçli olarak kapsam dışı bırakılmıştır).
"""

from __future__ import annotations

from ..core.check import BaseCheck
from ..core.models import Fix
from ..core.shell import read_file, which


class BootloaderCheck(BaseCheck):
    id = "bootloader"
    title = "Önyükleyici (GRUB)"
    icon = "🥾"
    category = "Sistem"
    weight = 0.5
    default_fix = Fix(
        "GRUB Menüsünü Yenile",
        "pkexec sh -c \"apt-get install -y os-prober && "
        "sed -i 's/^GRUB_DISABLE_OS_PROBER=.*/GRUB_DISABLE_OS_PROBER=false/' "
        "/etc/default/grub && update-grub\"",
        needs_root=True,
        description="os-prober'ı kurar/etkinleştirir ve GRUB menüsünü diğer "
        "işletim sistemlerini (ör. Windows) görecek şekilde yeniden üretir. "
        "Disk/EFI'ye yazma (grub-install) YAPMAZ.",
    )

    def run(self):
        if not which("update-grub") and not which("grub-mkconfig"):
            return self.info(
                "GRUB bulunamadı.",
                detail="Bu sistem GRUB dışı bir önyükleyici kullanıyor "
                "olabilir (ör. systemd-boot).",
            )

        cfg = (read_file("/etc/default/grub") or "").replace(" ", "")
        prober_disabled = "GRUB_DISABLE_OS_PROBER=true" in cfg
        prober_installed = which("os-prober")

        if not prober_installed or prober_disabled:
            return self.warn(
                "Diğer işletim sistemleri GRUB menüsünde görünmeyebilir.",
                detail=(
                    "os-prober kurulu değil." if not prober_installed
                    else "os-prober devre dışı bırakılmış (GRUB_DISABLE_OS_PROBER=true)."
                ),
                root_cause="Çift önyükleme (ör. Windows) yapan sistemlerde "
                "os-prober olmadan diğer işletim sistemi menüde listelenmez.",
                recommendation="os-prober'ı kurup GRUB menüsünü yenileyin.",
            )

        return self.ok(
            "GRUB yapılandırması normal görünüyor.",
            detail="os-prober etkin; diğer işletim sistemleri taranabilir.",
        )
