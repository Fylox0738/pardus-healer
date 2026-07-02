"""Düz metin rapor üreticisi (eski davranışla uyumlu, hızlı paylaşım için)."""

from __future__ import annotations

from ..core.models import DiagnosisReport


def build_text_report(report: DiagnosisReport) -> str:
    lines: list[str] = []
    add = lines.append
    add("=" * 58)
    add("  PARDUS HEALER — SİSTEM RAPORU")
    add(f"  Tarih / Saat : {report.started_at}")
    add(f"  Sağlık Skoru : {report.health_score}/100  (Not: {report.grade})")
    add(f"  Özet         : {report.fail_count} sorun, "
        f"{report.warn_count} uyarı, {report.ok_count} sağlıklı")
    add("=" * 58)
    add("")

    if report.insights:
        add("── ÖNCELİKLİ İÇGÖRÜLER ──")
        for ins in report.insights:
            add(f"[{ins.priority:3}] {ins.title}")
            add(f"      {ins.message}")
            add("")

    add("── KONTROL SONUÇLARI ──")
    for r in report.results:
        add(f"[{r.status.label_tr}]  {r.title}")
        add(f"        {r.summary}")
        if r.root_cause:
            add(f"        Olası neden : {r.root_cause}")
        if r.recommendation:
            add(f"        Öneri       : {r.recommendation}")
        add("")
    return "\n".join(lines)
