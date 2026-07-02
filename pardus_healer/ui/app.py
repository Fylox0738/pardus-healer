"""Ana uygulama penceresi — tüm katmanları birbirine bağlar."""

from __future__ import annotations

import subprocess
import threading

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, GLib, Gtk  # noqa: E402

from ..config import Config
from ..core.engine import (
    DiagnosisEngine,
    compute_health_score,
    score_to_grade,
)
from ..core import notify, rules, sysinfo
from ..core.history import History
from ..core.models import CheckResult, DiagnosisReport, Fix
from ..report.html_report import save_html_report
from . import theme
from .checks_page import ChecksPage
from .dashboard import Dashboard
from .settings_page import SettingsPage


class HealerApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Pardus Healer")
        self.set_default_size(1200, 820)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.maximize()

        self.config = Config()
        self.engine = DiagnosisEngine()
        self.checks = self.engine.checks
        self.history = History()
        self.results_by_id: dict[str, CheckResult] = {}
        self._auto_timer_id = None
        self._is_running = False

        # CSS
        self.css_provider = Gtk.CssProvider()
        self._apply_css()

        # kök yerleşim: kenar çubuğu | içerik
        root = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.add(root)
        self.sidebar, self.nav_buttons = self._build_sidebar()
        root.pack_start(self.sidebar, False, False, 0)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        right.get_style_context().add_class("main-area")
        root.pack_start(right, True, True, 0)

        # üst banner (tarama sırasında görünür)
        self.banner = Gtk.Label(label="")
        self.banner.get_style_context().add_class("apt-banner")
        self.banner.set_no_show_all(True)
        self.banner.set_visible(False)
        right.pack_start(self.banner, False, False, 0)

        # sayfa yığını
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(180)
        right.pack_start(self.stack, True, True, 0)

        self.dashboard = Dashboard(on_fix=self.run_fix)
        self.checks_page = ChecksPage(
            self.checks,
            recheck_callback=self.recheck_one,
            refresh_all_callback=self.refresh_all,
            report_callback=self.generate_report,
        )
        self.settings_page = SettingsPage(
            self.config.dark_mode,
            self.config.auto_interval_min,
            on_dark_toggle=self.on_dark_toggle,
            on_interval_change=self.on_interval_change,
        )
        self.stack.add_named(self.dashboard, "dashboard")
        self.stack.add_named(self.checks_page, "checks")
        self.stack.add_named(self.settings_page, "settings")
        self.stack.set_visible_child_name("dashboard")

        self.show_all()
        self.banner.set_visible(False)

        # zamanlayıcıyı uygula ve ilk taramayı başlat
        self.on_interval_change(self.config.auto_interval_min, announce=False)
        self.refresh_all()

    # ───────── CSS ─────────
    def _apply_css(self):
        self.css_provider.load_from_data(theme.get_css(self.config.dark_mode))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    # ───────── kenar çubuğu ─────────
    def _build_sidebar(self):
        sb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        sb.get_style_context().add_class("sidebar")
        sb.set_size_request(210, -1)
        sb.set_margin_top(18)
        sb.set_margin_bottom(18)

        brand = Gtk.Label(label="Pardus Healer")
        brand.get_style_context().add_class("sidebar-brand")
        brand.set_halign(Gtk.Align.START)
        brand.set_margin_start(18)
        brand.set_margin_bottom(6)
        sb.pack_start(brand, False, False, 0)

        sep = Gtk.Separator()
        sep.get_style_context().add_class("sidebar-sep")
        sep.set_margin_start(14)
        sep.set_margin_end(14)
        sep.set_margin_top(4)
        sep.set_margin_bottom(4)
        sb.pack_start(sep, False, False, 0)

        buttons = {}
        for page, label in [
            ("dashboard", "📊  Genel Bakış"),
            ("checks", "🩺  Kontroller"),
            ("settings", "⚙️  Ayarlar"),
        ]:
            btn = Gtk.Button(label=label)
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.get_style_context().add_class(
                "sidebar-btn-active" if page == "dashboard" else "sidebar-btn"
            )
            btn.connect("clicked", self._on_nav, page)
            sb.pack_start(btn, False, False, 0)
            buttons[page] = btn

        sb.pack_start(Gtk.Label(label=""), True, True, 0)
        return sb, buttons

    def _on_nav(self, _btn, page):
        self.stack.set_visible_child_name(page)
        for name, btn in self.nav_buttons.items():
            ctx = btn.get_style_context()
            ctx.remove_class("sidebar-btn-active")
            ctx.remove_class("sidebar-btn")
            ctx.add_class("sidebar-btn-active" if name == page else "sidebar-btn")

    # ───────── banner ─────────
    def _set_banner(self, text: str, visible: bool):
        self.banner.set_label(text)
        self.banner.set_visible(visible)

    # ───────── tarama ─────────
    def refresh_all(self):
        if self._is_running:
            return
        self._is_running = True
        self.checks_page.log("── Tüm kontroller çalıştırılıyor ──")
        self.checks_page.set_all_checking()
        self._set_banner("🔍  Sistem taranıyor, lütfen bekleyin...", True)
        threading.Thread(target=self._refresh_worker, daemon=True).start()

    def _refresh_worker(self):
        # Kontroller G/Ç bağımlı olduğundan paralel çalıştırılır: tarama
        # süresi, en yavaş kontrol kadar kısalır.
        from concurrent.futures import ThreadPoolExecutor, as_completed

        with ThreadPoolExecutor(max_workers=min(8, len(self.checks))) as pool:
            futures = [pool.submit(c.execute) for c in self.checks]
            for fut in as_completed(futures):
                GLib.idle_add(self._apply_result, fut.result())
        GLib.idle_add(self._on_refresh_done)

    def _apply_result(self, result: CheckResult):
        self.results_by_id[result.check_id] = result
        card = self.checks_page.get_card(result.check_id)
        if card is not None:
            card.update(result)
        return False

    def _on_refresh_done(self):
        self._is_running = False
        self._set_banner("", False)
        report = self._build_report()
        # geçmişe kaydet (trend için)
        self.history.add(
            report.health_score, report.grade,
            report.fail_count, report.warn_count, report.ok_count,
        )
        self._update_dashboard(report)
        self.checks_page.log(
            f"── Tarama tamamlandı · Sağlık skoru: {report.health_score}/100 "
            f"(Not: {report.grade}) ──"
        )
        # kritik durumda masaüstü bildirimi (varsa)
        notify.notify_report(
            report.fail_count, report.warn_count, report.health_score
        )
        return False

    def _update_dashboard(self, report: DiagnosisReport):
        """Dashboard'ı skor, geçmiş ve güncel sistem bilgisiyle tazeler."""
        self.dashboard.update(
            report,
            self.config.dark_mode,
            history_scores=self.history.scores(),
            sysinfo_pairs=sysinfo.collect().as_pairs(),
        )

    def recheck_one(self, check_id: str):
        card = self.checks_page.get_card(check_id)
        if card is not None:
            card.set_checking()
        threading.Thread(
            target=self._recheck_worker, args=(check_id,), daemon=True
        ).start()

    def _recheck_worker(self, check_id: str):
        result = self.engine.run_one(check_id)
        if result is not None:
            GLib.idle_add(self._apply_result, result)
            GLib.idle_add(self._refresh_dashboard_only)

    def _refresh_dashboard_only(self):
        self._update_dashboard(self._build_report())
        return False

    def _build_report(self) -> DiagnosisReport:
        """Saklanan sonuçlardan (kontrol sırasına göre) bir rapor kurar."""
        import datetime
        ordered = [
            self.results_by_id[c.id]
            for c in self.checks
            if c.id in self.results_by_id
        ]
        insights = rules.evaluate(ordered)
        score = compute_health_score(ordered)
        return DiagnosisReport(
            results=ordered,
            insights=insights,
            health_score=score,
            grade=score_to_grade(score),
            started_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

    # ───────── içgörü onarımı ─────────
    def run_fix(self, fix: Fix):
        """Dashboard içgörüsündeki önerilen onarımı çalıştırır."""
        self.stack.set_visible_child_name("checks")
        self._on_nav_sync("checks")
        self.checks_page.log(f"──▶ Çalıştırılıyor: {fix.command}")
        threading.Thread(target=self._fix_worker, args=(fix,), daemon=True).start()

    def _on_nav_sync(self, page):
        for name, btn in self.nav_buttons.items():
            ctx = btn.get_style_context()
            ctx.remove_class("sidebar-btn-active")
            ctx.remove_class("sidebar-btn")
            ctx.add_class("sidebar-btn-active" if name == page else "sidebar-btn")

    def _fix_worker(self, fix: Fix):
        try:
            proc = subprocess.Popen(
                fix.resolved_command(), shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            )
            assert proc.stdout is not None
            for line in iter(proc.stdout.readline, ""):
                if line:
                    GLib.idle_add(self.checks_page.log, line.rstrip())
            proc.stdout.close()
            proc.wait()
            GLib.idle_add(
                self.checks_page.log,
                f"İşlem tamamlandı (çıkış kodu: {proc.returncode})\n",
            )
        except Exception as exc:
            GLib.idle_add(self.checks_page.log, f"Hata: {exc}\n")
        finally:
            GLib.idle_add(self.refresh_all)

    # ───────── ayar callback'leri ─────────
    def on_dark_toggle(self, active: bool):
        self.config.dark_mode = active
        self._apply_css()
        # gösterge rengini/temayı tazele
        self._update_dashboard(self._build_report())

    def on_interval_change(self, minutes: int, announce: bool = True):
        self.config.auto_interval_min = minutes
        if self._auto_timer_id is not None:
            GLib.source_remove(self._auto_timer_id)
            self._auto_timer_id = None
        if minutes > 0:
            self._auto_timer_id = GLib.timeout_add_seconds(
                minutes * 60, self._auto_tick
            )
            if announce:
                self.checks_page.log(
                    f"Otomatik kontrol {minutes} dakikada bir olarak ayarlandı."
                )
        elif announce:
            self.checks_page.log("Otomatik kontrol kapatıldı.")

    def _auto_tick(self):
        self.checks_page.log("── Otomatik kontrol başlatıldı ──")
        self.refresh_all()
        return True

    # ───────── rapor ─────────
    def generate_report(self):
        report = self._build_report()
        if not report.results:
            self.checks_page.log("Rapor için önce bir tarama yapın.")
            return
        try:
            path = save_html_report(report)
            self.checks_page.log(f"Rapor kaydedildi → {path}")
            # tarayıcıda aç (varsa)
            try:
                subprocess.Popen(["xdg-open", path])
            except Exception:
                pass
            dlg = Gtk.MessageDialog(
                transient_for=self, flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK, text="Rapor Oluşturuldu",
            )
            dlg.format_secondary_text(f"HTML rapor kaydedildi:\n{path}")
            dlg.run()
            dlg.destroy()
        except Exception as exc:
            self.checks_page.log(f"Rapor hatası: {exc}")
