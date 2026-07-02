"""Genişletilmiş güvenlik kontrolleri: açık portlar, SSH sertleştirmesi,
başarısız girişler ve otomatik güvenlik güncellemeleri.
"""

from __future__ import annotations

import re

from ..core.check import BaseCheck
from ..core.models import Fix, Metric
from ..core.shell import read_file, run, which


class OpenPortsCheck(BaseCheck):
    id = "open_ports"
    title = "Açık Ağ Portları"
    icon = "🔌"
    category = "Güvenlik"
    weight = 0.9

    # Dış dünyaya (0.0.0.0 / ::) açık olması dikkat gerektiren servisler.
    RISKY = {
        "23": "Telnet", "21": "FTP", "3389": "RDP",
        "5900": "VNC", "3306": "MySQL", "5432": "PostgreSQL",
    }

    def run(self):
        if not which("ss"):
            return self.unknown("ss komutu bulunamadı.")
        res = run(["ss", "-tuln"], timeout=15)
        if not res.ok and not res.stdout:
            return self.unknown("Port bilgisi okunamadı.")

        listening = set()
        exposed_risky = []
        for line in res.stdout.splitlines()[1:]:
            m = re.search(r"[\d.*:\[\]]+:(\d+)\s", line)
            if not m:
                continue
            port = m.group(1)
            listening.add(port)
            # 0.0.0.0 veya [::] üzerinde dinliyorsa dış dünyaya açıktır.
            if ("0.0.0.0:" in line or "[::]:" in line or "*:" in line) and (
                port in self.RISKY
            ):
                exposed_risky.append(f"{self.RISKY[port]} ({port})")

        metric = Metric(len(listening), "port")
        if exposed_risky:
            uniq = sorted(set(exposed_risky))
            return self.warn(
                f"Riskli servis(ler) dışa açık: {', '.join(uniq)}",
                detail=f"{len(listening)} port dinlemede. Dışa açık riskli: "
                + ", ".join(uniq),
                metric=metric,
                root_cause="Hassas servisler tüm ağ arayüzlerinde dinliyor.",
                recommendation="Gerekli değilse bu servisleri kapatın ya da "
                "güvenlik duvarıyla sınırlayın.",
            )
        return self.ok(
            f"{len(listening)} port dinlemede, riskli açık port yok.",
            detail="Dışa açık bilinen riskli servis bulunamadı.",
            metric=metric,
        )


class SshHardeningCheck(BaseCheck):
    id = "ssh_hardening"
    title = "SSH Güvenliği"
    icon = "🔑"
    category = "Güvenlik"
    weight = 1.0

    def run(self):
        text = read_file("/etc/ssh/sshd_config")
        if text is None:
            return self.info(
                "SSH sunucusu yapılandırması yok.",
                detail="/etc/ssh/sshd_config bulunamadı; SSH sunucusu kurulu "
                "olmayabilir.",
            )

        permit_root = None
        password_auth = None
        for raw in text.splitlines():
            line = raw.strip()
            if line.startswith("#") or not line:
                continue
            low = line.lower()
            if low.startswith("permitrootlogin"):
                permit_root = line.split()[-1].lower()
            elif low.startswith("passwordauthentication"):
                password_auth = line.split()[-1].lower()

        problems = []
        if permit_root == "yes":
            problems.append("root ile doğrudan giriş açık (PermitRootLogin yes)")
        if password_auth == "yes":
            problems.append("parola ile giriş açık")

        if problems:
            return self.warn(
                "SSH sertleştirmesi önerilir.",
                detail="; ".join(problems),
                root_cause="Zayıf SSH ayarları kaba-kuvvet saldırılarını "
                "kolaylaştırır.",
                recommendation="root girişini kapatın, mümkünse anahtar tabanlı "
                "kimlik doğrulamaya geçin.",
            )
        return self.ok(
            "SSH ayarları makul.",
            detail="root doğrudan giriş kapalı görünüyor.",
        )


class UnattendedUpgradesCheck(BaseCheck):
    id = "auto_updates"
    title = "Otomatik Güvenlik Güncellemeleri"
    icon = "🔁"
    category = "Güvenlik"
    weight = 0.7
    default_fix = Fix(
        "Otomatik Güncellemeyi Kur ve Aç",
        "pkexec sh -c 'apt-get install -y unattended-upgrades && "
        "dpkg-reconfigure -f noninteractive unattended-upgrades'",
        needs_root=True,
        description="unattended-upgrades paketini kurar ve etkinleştirir.",
    )

    def run(self):
        if not which("apt-get"):
            return self.info(
                "Bu sistem APT tabanlı değil.",
                detail="Otomatik güncelleme kontrolü yalnızca APT sistemlerde "
                "geçerlidir.",
            )
        cfg = read_file("/etc/apt/apt.conf.d/20auto-upgrades")
        enabled = bool(cfg and "1" in cfg and "Update-Package-Lists" in cfg)
        if enabled:
            return self.ok(
                "Otomatik güvenlik güncellemeleri etkin.",
                detail="unattended-upgrades yapılandırılmış.",
            )
        return self.warn(
            "Otomatik güvenlik güncellemeleri kapalı.",
            detail="20auto-upgrades yapılandırması bulunamadı veya devre dışı.",
            root_cause="Güvenlik yamaları elle kurulmadıkça sistem güncel "
            "kalmayabilir.",
            recommendation="Otomatik güvenlik güncellemelerini etkinleştirin.",
        )
