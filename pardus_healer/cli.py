"""Komut satırı arayüzü (arayüzsüz tanı).

GTK gerektirmez; sunucularda, betiklerde veya hızlı tanı için kullanılır.
Kullanım örnekleri:
    python3 run.py --cli
    python3 run.py --cli --html rapor.html --json rapor.json
    python3 run.py --cli --quiet          # yalnızca skor
"""

from __future__ import annotations

import argparse
import os
import sys

from .core import notify, sysinfo
from .core.advisor import RuleAdvisor
from .core.engine import DiagnosisEngine
from .core.history import History
from .core.models import Status


# ── renkler ──
_RESET = "\033[0m"
_STATUS_COLOR = {
    Status.OK: "\033[92m",      # yeşil
    Status.INFO: "\033[94m",    # mavi
    Status.WARN: "\033[93m",    # sarı
    Status.FAIL: "\033[91m",    # kırmızı
    Status.UNKNOWN: "\033[90m",  # gri
}
_GRADE_COLOR = {
    "A": "\033[92m", "B": "\033[92m", "C": "\033[93m",
    "D": "\033[93m", "F": "\033[91m",
}


def _enable_ansi() -> None:
    """Windows terminallerinde ANSI renk desteğini açmaya çalışır."""
    if os.name == "nt":
        os.system("")


def _c(text: str, color: str, use_color: bool) -> str:
    return f"{color}{text}{_RESET}" if use_color else text


def run_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pardus-healer",
        description="Pardus Healer — akıllı sistem tanılama (komut satırı).",
    )
    parser.add_argument("--cli", action="store_true",
                        help="Komut satırı modunu çalıştırır (arayüzsüz).")
    parser.add_argument("--html", metavar="YOL", help="HTML rapor kaydeder.")
    parser.add_argument("--json", metavar="YOL", help="JSON rapor kaydeder.")
    parser.add_argument("--quiet", action="store_true",
                        help="Yalnızca sağlık skorunu yazdırır.")
    parser.add_argument("--no-color", action="store_true",
                        help="Renkli çıktıyı kapatır.")
    parser.add_argument("--sequential", action="store_true",
                        help="Kontrolleri paralel yerine sırayla çalıştırır.")
    parser.add_argument("--notify", action="store_true",
                        help="Sorun bulunursa masaüstü bildirimi gönderir.")
    args = parser.parse_args(argv)

    use_color = not args.no_color and sys.stdout.isatty()
    if use_color:
        _enable_ansi()

    engine = DiagnosisEngine()
    report = engine.run_all(concurrent=not args.sequential)

    # geçmişe kaydet
    hist = History()
    hist.add(report.health_score, report.grade,
             report.fail_count, report.warn_count, report.ok_count)

    if args.quiet:
        print(f"{report.health_score} {report.grade}")
    else:
        _print_full(report, hist, use_color)

    if args.html:
        from .report.html_report import save_html_report
        path = save_html_report(report, args.html)
        print(f"\nHTML rapor: {path}")
    if args.json:
        from .report.json_report import save_json_report
        path = save_json_report(report, args.json)
        print(f"JSON rapor: {path}")

    if args.notify:
        notify.notify_report(report.fail_count, report.warn_count,
                             report.health_score)

    # kabuk betikleri için anlamlı çıkış kodu
    if report.fail_count > 0:
        return 2
    if report.warn_count > 0:
        return 1
    return 0


def _print_full(report, hist, use_color: bool) -> None:
    line = "═" * 62
    print(line)
    print("  PARDUS HEALER — SİSTEM TANI RAPORU")
    print(line)

    # sistem bilgisi
    info = sysinfo.collect()
    for key, val in info.as_pairs():
        print(f"  {key:16}: {val}")
    print("─" * 62)

    # skor
    gcolor = _GRADE_COLOR.get(report.grade, "")
    score_str = _c(f"{report.health_score}/100  (Not: {report.grade})",
                   gcolor, use_color)
    trend = hist.trend()
    trend_str = ""
    if trend > 0:
        trend_str = _c(f"  ▲ +{trend}", _STATUS_COLOR[Status.OK], use_color)
    elif trend < 0:
        trend_str = _c(f"  ▼ {trend}", _STATUS_COLOR[Status.FAIL], use_color)
    print(f"  SAĞLIK SKORU : {score_str}{trend_str}")
    print(f"  ÖZET         : {report.fail_count} sorun · "
          f"{report.warn_count} uyarı · {report.ok_count} sağlıklı · "
          f"{report.duration_ms} ms")

    # sparkline
    spark = _sparkline(hist.scores())
    if spark:
        print(f"  TREND        : {spark}")
    print(line)

    # değerlendirme (kural tabanlı — hızlı, güç gerektirmez)
    print("\n💬 DEĞERLENDİRME")
    for chunk in _wrap(RuleAdvisor().summarize(report), 76):
        print(f"  {chunk}")

    # içgörüler
    if report.insights:
        print("\n🧠 ÖNCELİKLİ İÇGÖRÜLER")
        for ins in report.insights:
            c = _STATUS_COLOR.get(ins.severity, "")
            badge = _c(f"[{ins.priority:3}]", c, use_color)
            print(f"  {badge} {ins.title}")
            print(f"        {ins.message}")

    # kontroller
    print("\n📋 KONTROLLER")
    for r in report.results:
        c = _STATUS_COLOR[r.status]
        icon = _c(f"{r.status.label_tr:10}", c, use_color)
        print(f"  {icon} {r.title:30} {r.summary}")


def _wrap(text: str, width: int) -> list[str]:
    """Metni kelime sınırlarında satırlara böler (terminal için)."""
    import textwrap
    return textwrap.wrap(text, width=width) or [""]


def _sparkline(values: list[int]) -> str:
    """Sayı dizisini Unicode blok karakterleriyle mini grafiğe çevirir."""
    if len(values) < 2:
        return ""
    blocks = "▁▂▃▄▅▆▇█"
    lo, hi = min(values), max(values)
    span = hi - lo or 1
    return "".join(blocks[int((v - lo) / span * (len(blocks) - 1))] for v in values)


if __name__ == "__main__":
    sys.exit(run_cli())
