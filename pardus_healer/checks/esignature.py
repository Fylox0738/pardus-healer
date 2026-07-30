"""e-İmza / e-Devlet uyumluluk kontrolü.

Türkiye'de yaygın e-imza/akıllı kart araçları ve e-Devlet'in bazı eski
JNLP tabanlı hizmetleri Java çalışma zamanına ve PC/SC akıllı kart
servisine (pcscd) ihtiyaç duyar. Bu, kamu personeli/öğrencinin en sık
karşılaştığı "e-imza çalışmıyor" sınıfı sorunları tek yerde toplar
.
"""

from __future__ import annotations

from ..core.check import BaseCheck
from ..core.models import Fix
from ..core.shell import run, which


class ESignatureCheck(BaseCheck):
    id = "esignature"
    title = "e-İmza / e-Devlet Uyumluluğu"
    icon = "🪪"
    category = "Kamu Hizmetleri"
    weight = 0.7
    # icedtea-netx: Pardus deposunda mevcut (depo.pardus.org.tr,
    # icedtea-web 1.8.8 — Pardus 21/23/25 tabanlarının üçünde de var) ve
    # forumdaki topluluk çözümü de aynı paketi kuruyor (bkz.
    # forum.pardus.org.tr/t/27051). Üst akım bakım modunda; modern
    # alternatif OpenWebStart, info() önerisinde belirtiliyor.
    default_fix = Fix(
        "Java ve Akıllı Kart Servisini Kur",
        "pkexec sh -c 'apt-get install -y default-jre pcsc-tools pcscd "
        "libccid icedtea-netx && systemctl enable --now pcscd'",
        needs_root=True,
        description="e-imza/e-Devlet için gereken Java çalışma zamanını, "
        "JNLP aracını ve akıllı kart (PC/SC) servisini kurar, pcscd'yi "
        "etkinleştirir.",
    )

    def run(self):
        has_java = which("java")
        pcscd_active = self._service_active("pcscd")
        has_jnlp = which("javaws") or which("itweb-settings")

        if not has_java:
            return self.fail(
                "Java çalışma zamanı kurulu değil.",
                detail="Birçok e-imza aracı ve e-Devlet'in bazı hizmetleri "
                "Java gerektirir.",
                root_cause="default-jre (veya eşdeğeri) kurulu değil.",
                recommendation="Java çalışma zamanını kurun.",
            )

        if not pcscd_active:
            return self.warn(
                "Akıllı kart servisi (pcscd) çalışmıyor.",
                detail="USB e-imza tokeni/akıllı kart okuyucusu bu servis "
                "olmadan sistem tarafından tanınmayabilir.",
                root_cause="pcscd servisi kurulu değil ya da durdurulmuş.",
                recommendation="pcscd'yi kurup etkinleştirin.",
            )

        if not has_jnlp:
            return self.info(
                "Java Web Start (JNLP) aracı bulunamadı.",
                detail="e-Devlet'in bazı eski hizmetleri .jnlp ile açılır; "
                "güncel hizmetlerin çoğu artık buna ihtiyaç duymuyor.",
                recommendation="Sorun yaşarsanız icedtea-netx paketini kurun "
                "(Pardus depolarında mevcut); modern alternatif olarak "
                "OpenWebStart da kullanılabilir.",
            )

        return self.ok(
            "Java ve akıllı kart servisi hazır.",
            detail="e-imza/e-Devlet için gerekli temel bileşenler kurulu.",
        )

    @staticmethod
    def _service_active(name: str) -> bool:
        if not which("systemctl"):
            return False
        res = run(["systemctl", "is-active", "--quiet", name], timeout=10)
        return res.ok
