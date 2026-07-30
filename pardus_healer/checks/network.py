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
                # Global socket.setdefaulttimeout() yerine soket üzerinde
                # doğrudan ayarlanıyor — engine kontrolleri paralel
                # çalıştırdığından (ThreadPoolExecutor) global varsayılan,
                # eşzamanlı çalışan başka bir kontrolün soketini de
                # etkileyebilirdi.
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(3)
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

    # Tek bir sabit alan adına (yalnızca "pardus.org.tr") bağımlıydı — o
    # tek alan adı geçici olarak çözümlenemezse (kayıt değişikliği, o
    # sunucunun kendi sorunu vb.) DNS'in tamamı bozukmuş gibi yanlış bir
    # WARN üretiyordu. Şimdi birden fazla
    # bağımsız alan adı deneniyor; yalnızca HİÇBİRİ çözümlenmezse uyarılır.
    DOMAINS = ["pardus.org.tr", "debian.org", "cloudflare.com"]

    def run(self):
        # NOT: socket.setdefaulttimeout() burada kasıtlı olarak
        # KULLANILMIYOR — socket.gethostbyname() alttaki C kütüphanesi
        # gethostbyname()'i çağırır ve Python'ın soket zaman aşımı
        # ayarını hiçbir zaman dikkate almaz; global durumu değiştirmenin
        # (paralel çalışan diğer kontrolleri etkileme riski dışında)
        # burada hiçbir faydası yoktur.
        for domain in self.DOMAINS:
            try:
                addr = socket.gethostbyname(domain)
                return self.ok(
                    "Alan adları çözümleniyor.",
                    detail=f"{domain} → {addr}",
                )
            except OSError:
                continue
        return self.warn(
            "Alan adları çözümlenemiyor.",
            detail=f"Denenen alan adları çözümlenemedi: {', '.join(self.DOMAINS)}",
            root_cause="DNS sunucusu yanıt vermiyor ya da internet yok.",
            recommendation="Önce internet bağlantısını kontrol edin; "
            "bağlantı varsa DNS önbelleğini temizleyin.",
        )
