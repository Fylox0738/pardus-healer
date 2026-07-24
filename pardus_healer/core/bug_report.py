"""SOS Kartı: Healer'ın tanı sonucunu, yarışmanın talep formuna birebir
oturan (Başlık / Hata türü / Önem derecesi / Adım adım senaryo /
Gerçekleşen-Olması gereken sonuç) bir rapora çevirir.

Bu, teknik olmayan bir kullanıcının (örn. bir öğretmenin) "Yardım İste"
butonuna basmasıyla üretilir; hem sade bir özet hem de doğrudan
`talep.pardus.org.tr`'ye veya okulun bağlı olduğu İl/İlçe BT Formatör
Öğretmeni'ne gönderilebilecek tam biçimli bir metin üretir.
"""

from __future__ import annotations

import datetime
import urllib.parse
from dataclasses import dataclass

from .models import DiagnosisReport, Status

_SEVERITY_TR = {
    Status.FAIL: "Kritik",
    Status.WARN: "Orta",
    Status.INFO: "Düşük",
    Status.UNKNOWN: "Düşük",
    Status.OK: "Düşük",
}


@dataclass
class SosReport:
    title: str
    severity: str
    plain_summary: str
    steps: str
    actual_result: str
    expected_result: str
    generated_at: str
    primary_issue: str
    system_info: str = ""


def _pick_primary_issue(report: DiagnosisReport):
    """En öncelikli insight'ı, yoksa en kritik CheckResult'u seçer."""
    if report.insights:
        return report.insights[0]
    for status in (Status.FAIL, Status.WARN):
        for r in report.results:
            if r.status is status:
                return r
    return None


def build_sos_report(
    report: DiagnosisReport,
    plain_summary: str,
    sysinfo_text: str = "",
) -> SosReport:
    """DiagnosisReport'tan yarışmanın talep formuna oturan bir SOS raporu üretir."""
    primary = _pick_primary_issue(report)
    generated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if primary is None:
        return SosReport(
            title="Pardus Healer: kritik bulgu yok",
            severity="Düşük",
            plain_summary=plain_summary,
            steps=(
                "1) Pardus Healer açıldı.\n"
                "2) \"Tümünü Tara\" ile otomatik tarama çalıştırıldı.\n"
                "3) Kritik veya uyarı seviyesinde bir bulguya rastlanmadı."
            ),
            actual_result=(
                f"Sağlık skoru {report.health_score}/100 (Not: {report.grade}); "
                f"{report.fail_count} sorun, {report.warn_count} uyarı bulundu."
            ),
            expected_result="—",
            generated_at=generated_at,
            primary_issue="Yok",
            system_info=sysinfo_text,
        )

    is_insight = hasattr(primary, "message")
    title = primary.title
    message = primary.message if is_insight else primary.summary
    status = primary.severity if is_insight else primary.status
    severity = _SEVERITY_TR.get(status, "Orta")

    if is_insight:
        related_ids = set(primary.related)
        related_titles = [r.title for r in report.results if r.check_id in related_ids]
    else:
        related_titles = [primary.title]

    steps = (
        "1) Pardus Healer uygulaması açıldı.\n"
        "2) Ana ekranda otomatik sistem taraması çalıştı (veya \"Tümünü Tara\" ile tekrarlandı).\n"
        f"3) Şu kontrol(ler) sorunlu/uyarı durumunda çıktı: {', '.join(t for t in related_titles if t) or title}.\n"
        "4) \"🆘 Yardım İste\" (SOS Kartı) butonuna basılarak bu rapor otomatik üretildi."
    )
    actual_result = f"{title}: {message}"

    fix = primary.suggested_fix if is_insight else primary.fix
    expected_result = (
        f"\"{fix.label}\" onarımının uygulanması ve kontrolün tekrar sağlıklı çıkması."
        if fix is not None
        else "Sorunun kök nedeninin giderilmesi."
    )

    return SosReport(
        title=f"Pardus SOS: {title}",
        severity=severity,
        plain_summary=plain_summary,
        steps=steps,
        actual_result=actual_result,
        expected_result=expected_result,
        generated_at=generated_at,
        primary_issue=title,
        system_info=sysinfo_text,
    )


def format_ticket_text(sos: SosReport) -> str:
    """`talep.pardus.org.tr` formuna neredeyse birebir yapıştırılabilecek metin bloğu."""
    lines = [
        f"Başlık: {sos.title}",
        "Hata türü: Fonksiyonel Hatalar/Öneriler",
        f"Önem derecesi: {sos.severity}",
        "",
        "Adım adım hata nasıl oluşur:",
        sos.steps,
        "",
        "Gerçekleşen sonuç:",
        sos.actual_result,
        "",
        "Olması gereken sonuç:",
        sos.expected_result,
        "",
        f"Rapor zamanı: {sos.generated_at}",
    ]
    if sos.system_info:
        lines.append(f"Sistem: {sos.system_info}")
    return "\n".join(lines).strip() + "\n"


def build_mailto_url(sos: SosReport, to_address: str = "") -> str:
    """Formatör Öğretmen'e (veya belirtilen adrese) gönderilecek hazır e-posta bağlantısı."""
    subject = urllib.parse.quote(sos.title)
    body = urllib.parse.quote(format_ticket_text(sos))
    return f"mailto:{to_address}?subject={subject}&body={body}"
