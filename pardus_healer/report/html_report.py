"""Profesyonel, tek dosyalık (gömülü CSS) HTML rapor üreticisi.

Çıktı tarayıcıda açılabilir, yazdırılabilir veya PDF'e aktarılabilir.
Hiçbir dış bağımlılık gerektirmez.
"""

from __future__ import annotations

import html
import os

from ..core.models import DiagnosisReport, Status

_STATUS_COLOR = {
    Status.OK: "#22c55e",
    Status.INFO: "#3b82f6",
    Status.WARN: "#eab308",
    Status.FAIL: "#ef4444",
    Status.UNKNOWN: "#94a3b8",
}

_GRADE_COLOR = {
    "A": "#22c55e",
    "B": "#84cc16",
    "C": "#eab308",
    "D": "#f97316",
    "F": "#ef4444",
}


def _esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def _score_ring(score: int, grade: str) -> str:
    """Sağlık skorunu gösteren SVG halka."""
    color = _GRADE_COLOR.get(grade, "#3b82f6")
    circumference = 2 * 3.14159 * 52
    offset = circumference * (1 - score / 100)
    return f"""
    <svg width="150" height="150" viewBox="0 0 120 120">
      <circle cx="60" cy="60" r="52" fill="none" stroke="#e2e8f0" stroke-width="12"/>
      <circle cx="60" cy="60" r="52" fill="none" stroke="{color}" stroke-width="12"
              stroke-linecap="round" stroke-dasharray="{circumference:.1f}"
              stroke-dashoffset="{offset:.1f}"
              transform="rotate(-90 60 60)"/>
      <text x="60" y="56" text-anchor="middle" font-size="30" font-weight="800"
            fill="{color}">{score}</text>
      <text x="60" y="76" text-anchor="middle" font-size="12" fill="#64748b">/ 100</text>
    </svg>
    """


def build_html_report(report: DiagnosisReport) -> str:
    grade_color = _GRADE_COLOR.get(report.grade, "#3b82f6")

    insight_html = ""
    if report.insights:
        rows = []
        for ins in report.insights:
            c = _STATUS_COLOR.get(ins.severity, "#eab308")
            rows.append(f"""
            <div class="insight" style="border-left-color:{c}">
              <div class="insight-head">
                <span class="prio" style="background:{c}">{ins.priority}</span>
                <strong>{_esc(ins.title)}</strong>
              </div>
              <p>{_esc(ins.message)}</p>
            </div>""")
        insight_html = f"""
        <section>
          <h2>🧠 Öncelikli İçgörüler</h2>
          {''.join(rows)}
        </section>"""

    result_rows = []
    for r in report.results:
        c = _STATUS_COLOR[r.status]
        extra = ""
        if r.root_cause:
            extra += f'<div class="sub"><b>Olası neden:</b> {_esc(r.root_cause)}</div>'
        if r.recommendation:
            extra += f'<div class="sub"><b>Öneri:</b> {_esc(r.recommendation)}</div>'
        result_rows.append(f"""
        <tr>
          <td class="badge-cell">
            <span class="badge" style="background:{c}">{_esc(r.status.label_tr)}</span>
          </td>
          <td>
            <div class="rtitle">{_esc(r.icon)} {_esc(r.title)}
              <span class="cat">{_esc(r.category)}</span>
            </div>
            <div class="rsum">{_esc(r.summary)}</div>
            {extra}
          </td>
        </tr>""")

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pardus Healer — Sistem Raporu</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    font-family: 'Segoe UI', system-ui, sans-serif; margin: 0;
    background: #f4f6f9; color: #1e293b; line-height: 1.5;
  }}
  .wrap {{ max-width: 860px; margin: 0 auto; padding: 24px; }}
  header {{
    background: linear-gradient(135deg, #0d1b2a, #1a2b4c);
    color: #fff; border-radius: 16px; padding: 28px 32px;
    display: flex; align-items: center; gap: 28px; flex-wrap: wrap;
  }}
  header h1 {{ margin: 0 0 4px; font-size: 26px; color: #00d4c7; }}
  header .meta {{ color: #94a3b8; font-size: 14px; }}
  .grade {{
    font-size: 44px; font-weight: 800; color: {grade_color};
    line-height: 1;
  }}
  .summary-pills {{ display: flex; gap: 10px; margin-top: 10px; flex-wrap: wrap; }}
  .pill {{
    background: rgba(255,255,255,.1); padding: 4px 12px;
    border-radius: 20px; font-size: 13px;
  }}
  h2 {{ font-size: 18px; margin: 28px 0 12px; color: #1a2b4c; }}
  .insight {{
    background: #fff; border-radius: 10px; padding: 14px 18px;
    margin-bottom: 10px; border-left: 5px solid #eab308;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
  }}
  .insight-head {{ display: flex; align-items: center; gap: 10px; }}
  .prio {{
    color: #fff; font-weight: 700; font-size: 12px;
    padding: 2px 9px; border-radius: 12px;
  }}
  .insight p {{ margin: 6px 0 0; color: #475569; font-size: 14px; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff;
           border-radius: 10px; overflow: hidden;
           box-shadow: 0 1px 3px rgba(0,0,0,.06); }}
  td {{ padding: 14px 16px; border-bottom: 1px solid #eef2f6;
        vertical-align: top; }}
  .badge-cell {{ width: 90px; }}
  .badge {{ color: #fff; font-size: 11px; font-weight: 700;
            padding: 3px 10px; border-radius: 6px; white-space: nowrap; }}
  .rtitle {{ font-weight: 700; }}
  .cat {{ font-size: 11px; color: #94a3b8; font-weight: 500;
          margin-left: 6px; }}
  .rsum {{ color: #475569; font-size: 14px; margin-top: 2px; }}
  .sub {{ color: #64748b; font-size: 13px; margin-top: 4px; }}
  footer {{ text-align: center; color: #94a3b8; font-size: 12px;
            margin-top: 30px; }}
  @media print {{ body {{ background: #fff; }} }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>{_score_ring(report.health_score, report.grade)}</div>
    <div style="flex:1; min-width:220px;">
      <h1>Pardus Healer — Sistem Raporu</h1>
      <div class="meta">Oluşturulma: {_esc(report.started_at)} · Süre:
        {report.duration_ms} ms</div>
      <div class="summary-pills">
        <span class="pill">Not: <b style="color:{grade_color}">{report.grade}</b></span>
        <span class="pill">❌ {report.fail_count} sorun</span>
        <span class="pill">⚠️ {report.warn_count} uyarı</span>
        <span class="pill">✅ {report.ok_count} sağlıklı</span>
      </div>
    </div>
  </header>
  {insight_html}
  <section>
    <h2>📋 Kontrol Sonuçları</h2>
    <table>{''.join(result_rows)}</table>
  </section>
  <footer>Pardus Healer · Akıllı Sistem Tanılama Aracı</footer>
</div>
</body>
</html>"""


def save_html_report(report: DiagnosisReport, path: str | None = None) -> str:
    """Raporu HTML olarak kaydeder ve dosya yolunu döndürür."""
    if path is None:
        home = os.path.expanduser("~")
        path = os.path.join(home, "pardus-healer-rapor.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(build_html_report(report))
    return path
