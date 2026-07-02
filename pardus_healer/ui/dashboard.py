"""Genel bakış paneli: sağlık skoru, özet istatistikler ve akıllı içgörüler."""

from __future__ import annotations

from typing import Callable

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from ..core.models import DiagnosisReport, Fix, Insight, Status
from .widgets import HealthGauge, LiveMeter, TrendChart

_GRADE_HEX = {
    "A": "#22c55e", "B": "#84cc16", "C": "#eab308",
    "D": "#f97316", "F": "#ef4444",
}


class Dashboard(Gtk.Box):
    """Tanı turunun üst düzey özetini gösteren panel."""

    def __init__(self, on_fix: Callable[[Fix], None]):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.on_fix = on_fix
        self.set_margin_start(28)
        self.set_margin_end(28)
        self.set_margin_top(22)
        self.set_margin_bottom(16)

        title = Gtk.Label(label="Sistem Sağlığı")
        title.set_halign(Gtk.Align.START)
        title.get_style_context().add_class("page-title")
        self.pack_start(title, False, False, 0)

        # --- Üst şerit: gösterge + istatistikler ---
        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)

        self.gauge = HealthGauge(170)
        gauge_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        gauge_box.pack_start(self.gauge, False, False, 0)
        self.grade_label = Gtk.Label(label="—")
        self.grade_label.get_style_context().add_class("score-grade")
        gauge_box.pack_start(self.grade_label, False, False, 0)
        top.pack_start(gauge_box, False, False, 0)

        # istatistik kutuları
        stats = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        stats.set_valign(Gtk.Align.CENTER)
        self.stat_fail = self._make_stat("Sorun", "0")
        self.stat_warn = self._make_stat("Uyarı", "0")
        self.stat_ok = self._make_stat("Sağlıklı", "0")
        for s in (self.stat_fail, self.stat_warn, self.stat_ok):
            stats.pack_start(s["box"], False, False, 0)
        top.pack_start(stats, False, False, 0)

        # trend grafiği
        trend_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        trend_box.set_valign(Gtk.Align.CENTER)
        trend_lbl = Gtk.Label(label="Skor Geçmişi")
        trend_lbl.set_halign(Gtk.Align.START)
        trend_lbl.get_style_context().add_class("dash-stat-label")
        trend_box.pack_start(trend_lbl, False, False, 0)
        self.trend_chart = TrendChart(240, 84)
        trend_box.pack_start(self.trend_chart, False, False, 0)
        top.pack_start(trend_box, True, True, 0)
        self.pack_start(top, False, False, 0)

        # sistem bilgisi şeridi
        self.sysinfo_label = Gtk.Label(label="")
        self.sysinfo_label.set_halign(Gtk.Align.START)
        self.sysinfo_label.set_xalign(0.0)
        self.sysinfo_label.set_line_wrap(True)
        self.sysinfo_label.get_style_context().add_class("page-sub")
        self.pack_start(self.sysinfo_label, False, False, 0)

        # ── Canlı izleme (gerçek zamanlı CPU/RAM/Disk) ──
        live_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        live_card.get_style_context().add_class("dash-stat")
        live_head = Gtk.Label(label="📡  Canlı İzleme")
        live_head.set_halign(Gtk.Align.START)
        live_head.get_style_context().add_class("dash-stat-label")
        live_card.pack_start(live_head, False, False, 0)

        meters = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=22)
        meters.set_homogeneous(True)
        self.meter_cpu = LiveMeter("İşlemci", "🧮")
        self.meter_ram = LiveMeter("Bellek", "🧠")
        self.meter_disk = LiveMeter("Disk", "💾")
        for m in (self.meter_cpu, self.meter_ram, self.meter_disk):
            meters.pack_start(m, True, True, 0)
        live_card.pack_start(meters, False, False, 0)
        self.pack_start(live_card, False, False, 0)

        # --- İçgörüler ---
        ins_title = Gtk.Label(label="🧠  Akıllı İçgörüler")
        ins_title.set_halign(Gtk.Align.START)
        ins_title.get_style_context().add_class("settings-section-title")
        ins_title.set_margin_top(6)
        self.pack_start(ins_title, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.insights_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        scroll.add(self.insights_box)
        self.pack_start(scroll, True, True, 0)

        self._show_placeholder("Kontroller çalıştırıldığında içgörüler burada görünür.")

    def update_live(self, sample, dark: bool) -> None:
        """Canlı izleme çubuklarını günceller (saniyede ~bir çağrılır)."""
        self.meter_cpu.set_percent(sample.cpu_percent, dark)
        self.meter_ram.set_percent(sample.ram_percent, dark)
        self.meter_disk.set_percent(sample.disk_percent, dark)

    # ---- yardımcılar ----
    def _make_stat(self, label: str, value: str) -> dict:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.get_style_context().add_class("dash-stat")
        num = Gtk.Label(label=value)
        num.get_style_context().add_class("dash-stat-num")
        lbl = Gtk.Label(label=label)
        lbl.get_style_context().add_class("dash-stat-label")
        box.pack_start(num, False, False, 0)
        box.pack_start(lbl, False, False, 0)
        return {"box": box, "num": num}

    def _clear_insights(self) -> None:
        for child in self.insights_box.get_children():
            self.insights_box.remove(child)

    def _show_placeholder(self, text: str) -> None:
        self._clear_insights()
        lbl = Gtk.Label(label=text)
        lbl.set_halign(Gtk.Align.START)
        lbl.get_style_context().add_class("card-info")
        self.insights_box.pack_start(lbl, False, False, 0)
        self.insights_box.show_all()

    # ---- güncelleme ----
    def update(
        self,
        report: DiagnosisReport,
        dark: bool,
        history_scores: list[int] | None = None,
        sysinfo_pairs: list[tuple[str, str]] | None = None,
    ) -> None:
        self.gauge.set_value(report.health_score, report.grade, dark)
        color = _GRADE_HEX.get(report.grade, "#3b82f6")
        self.grade_label.set_markup(
            f"<span foreground='{color}'>Not: {report.grade}</span>"
        )
        self.stat_fail["num"].set_label(str(report.fail_count))
        self.stat_warn["num"].set_label(str(report.warn_count))
        self.stat_ok["num"].set_label(str(report.ok_count))
        self.trend_chart.set_values(history_scores or [], dark)
        if sysinfo_pairs:
            self.sysinfo_label.set_text(
                "   ·   ".join(f"{k}: {v}" for k, v in sysinfo_pairs)
            )

        self._clear_insights()
        if not report.insights:
            good = report.fail_count == 0 and report.warn_count == 0
            self._show_placeholder(
                "✅ Her şey yolunda görünüyor — öncelikli bir sorun yok."
                if good else
                "Belirgin bir kök-neden ilişkisi bulunamadı; kart listesini inceleyin."
            )
            return
        for ins in report.insights:
            self.insights_box.pack_start(self._make_insight(ins), False, False, 0)
        self.insights_box.show_all()

    def _make_insight(self, ins: Insight) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.get_style_context().add_class("insight")
        box.get_style_context().add_class(
            "insight-fail" if ins.severity is Status.FAIL else "insight-warn"
        )

        head = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        prio = Gtk.Label(label=str(ins.priority))
        prio.get_style_context().add_class("insight-prio")
        head.pack_start(prio, False, False, 0)
        t = Gtk.Label(label=ins.title)
        t.set_halign(Gtk.Align.START)
        t.get_style_context().add_class("insight-title")
        head.pack_start(t, False, False, 0)
        box.pack_start(head, False, False, 0)

        msg = Gtk.Label(label=ins.message)
        msg.set_halign(Gtk.Align.START)
        msg.set_xalign(0.0)
        msg.set_line_wrap(True)
        msg.get_style_context().add_class("insight-msg")
        box.pack_start(msg, False, False, 0)

        if ins.suggested_fix is not None:
            btn = Gtk.Button(label=f"⚡ {ins.suggested_fix.label}")
            btn.get_style_context().add_class("fix-button")
            btn.set_halign(Gtk.Align.START)
            btn.connect("clicked", lambda _b, f=ins.suggested_fix: self.on_fix(f))
            box.pack_start(btn, False, False, 4)
        return box
