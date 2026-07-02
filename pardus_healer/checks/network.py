"""Ağ bağlantısı kontrolleri: internet erişimi ve DNS çözümlemesi."""

from __future__ import annotations

import socket

from ..core.check import BaseCheck
from ..core.models import Fix


class InternetCheck(BaseCheck):
    id = "internet"
    title = "İnternet Bağlantısı"
    icon = "🌐"
    category = "Ağ"
    weight = 1.5
    default_fix = Fix(
        "Ağı Yenile",
        "pkexec systemctl restart NetworkManager",
        needs_root=True,
        description="NetworkManager servisini yeniden başlatır.",
    )

    # Bilinen, hızlı ve güvenilir TCP uç noktaları (ping'e göre daha az
    # güvenlik duvarı sorunu yaşar).
    ENDPOINTS = [("1.1.1.1", 53), ("8.8.8.8", 53), ("9.9.9.9", 53)]

    def run(self):
        for host, port in self.ENDPOINTS:
            try:
                socket.setdefaulttimeout(3)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect((host, port))
                return self.ok(
                    "İnternet bağlantısı aktif.",
                    detail=f"{host}:{port} adresine ulaşıldı.",
                )
            except OSError:
                continue
        return self.fail(
            "İnternet bağlantısı yok!",
            detail="Hiçbir bilinen sunucuya ulaşılamadı.",
            root_cause="Ağ arayüzü kapalı, kablo/Wi-Fi bağlı değil ya da "
            "NetworkManager durmuş olabilir.",
            recommendation="Kablo/Wi-Fi bağlantınızı kontrol edin; sorun "
            "sürerse ağı yenileyin.",
        )


class DnsCheck(BaseCheck):
    id = "dns"
    title = "DNS Çözümlemesi"
    icon = "🧭"
    category = "Ağ"
    weight = 0.8
    default_fix = Fix(
        "DNS Önbelleğini Temizle",
        "pkexec systemctl restart systemd-resolved",
        needs_root=True,
        description="systemd-resolved servisini yeniden başlatır.",
    )

    def run(self):
        try:
            socket.setdefaulttimeout(3)
            addr = socket.gethostbyname("pardus.org.tr")
            return self.ok(
                "Alan adları çözümleniyor.",
                detail=f"pardus.org.tr → {addr}",
            )
        except OSError:
            # İnternet varsa ama DNS yoksa bu ayrı bir sorundur.
            return self.warn(
                "Alan adları çözümlenemiyor.",
                detail="pardus.org.tr çözümlenemedi.",
                root_cause="DNS sunucusu yanıt vermiyor ya da internet yok.",
                recommendation="Önce internet bağlantısını kontrol edin; "
                "bağlantı varsa DNS önbelleğini temizleyin.",
            )
