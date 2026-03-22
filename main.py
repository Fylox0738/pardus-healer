import gi
import subprocess
import threading
import socket
import os
import datetime

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf, Pango

# ──────────────────────────────────────────────
# CSS  (Açık Mod — varsayılan)
# ──────────────────────────────────────────────
CSS_LIGHT = b"""
/* ---- Genel ---- */
window, .main-area {
    background-color: #f4f6f9;
}

/* ---- Splash ---- */
.splash-bg {
    background-color: #0d1b2a;
}
.splash-title {
    font-weight: 900;
    font-size: 32pt;
    color: #00a79d;
}
.splash-sub {
    font-size: 12pt;
    color: #8899aa;
}

/* ---- Sidebar ---- */
.sidebar {
    background-color: #1a2b4c;
}
.sidebar-btn {
    background: transparent;
    color: #aabbcc;
    font-weight: 600;
    font-size: 12pt;
    border: none;
    border-radius: 8px;
    padding: 12px 18px;
}
.sidebar-btn:hover {
    background: rgba(255,255,255,0.08);
    color: #ffffff;
}
.sidebar-btn-active {
    background: rgba(0, 167, 157, 0.25);
    color: #00a79d;
    font-weight: 700;
    font-size: 12pt;
    border: none;
    border-radius: 8px;
    padding: 12px 18px;
}
.sidebar-brand {
    font-weight: 900;
    font-size: 16pt;
    color: #00a79d;
}
.sidebar-sep {
    background-color: rgba(255,255,255,0.08);
    min-height: 1px;
}

/* ---- Başlık ---- */
.page-title {
    font-weight: 800;
    font-size: 22pt;
    color: #1a2b4c;
}

/* ---- Kartlar ---- */
.card {
    background-color: #ffffff;
    border-radius: 10px;
    padding: 18px 22px;
    margin: 6px 0px;
    border: 1px solid #e1e8ed;
}
.card-ok    { border-left: 4px solid #22c55e; }
.card-warn  { border-left: 4px solid #eab308; }
.card-fail  { border-left: 4px solid #ef4444; }
.card-wait  { border-left: 4px solid #94a3b8; }

.card-title {
    font-weight: 700;
    font-size: 13pt;
    color: #1a2b4c;
}
.card-info {
    font-size: 10.5pt;
    color: #4a5568;
    margin-top: 2px;
}
.status-icon {
    font-size: 22pt;
}

/* ---- Butonlar ---- */
.fix-button {
    background: #00a79d;
    color: white;
    font-weight: bold;
    border-radius: 6px;
    padding: 8px 20px;
    border: none;
}
.report-button {
    background: #1a2b4c;
    color: white;
    font-weight: bold;
    border-radius: 6px;
    padding: 8px 20px;
    border: none;
}

/* ---- Banner ---- */
.apt-banner {
    background-color: #fef3cd;
    color: #856404;
    font-weight: 600;
    font-size: 10.5pt;
    padding: 8px 16px;
    border-bottom: 1px solid #f0d77c;
}

/* ---- Terminal ---- */
.terminal-title {
    font-weight: bold;
    font-size: 13pt;
    color: #1a2b4c;
    margin-bottom: 4px;
}
.terminal-view {
    background-color: #1e2124;
    color: #d4d4d4;
    font-family: monospace;
    font-size: 11pt;
    padding: 14px;
    border-radius: 8px;
    border-left: 4px solid #00a79d;
}

/* ---- Ayarlar ---- */
.settings-section-title {
    font-weight: 700;
    font-size: 14pt;
    color: #1a2b4c;
    margin-bottom: 6px;
}
.settings-label {
    font-size: 11pt;
    color: #4a5568;
}
"""

CSS_DARK = b"""
/* ---- Genel (Koyu) ---- */
window, .main-area {
    background-color: #0f172a;
}

/* ---- Splash ---- */
.splash-bg {
    background-color: #0d1b2a;
}
.splash-title {
    font-weight: 900;
    font-size: 32pt;
    color: #00a79d;
}
.splash-sub {
    font-size: 12pt;
    color: #8899aa;
}

/* ---- Sidebar ---- */
.sidebar {
    background-color: #0d1b2a;
}
.sidebar-btn {
    background: transparent;
    color: #8899aa;
    font-weight: 600;
    font-size: 12pt;
    border: none;
    border-radius: 8px;
    padding: 12px 18px;
}
.sidebar-btn:hover {
    background: rgba(255,255,255,0.06);
    color: #ffffff;
}
.sidebar-btn-active {
    background: rgba(0, 167, 157, 0.2);
    color: #00a79d;
    font-weight: 700;
    font-size: 12pt;
    border: none;
    border-radius: 8px;
    padding: 12px 18px;
}
.sidebar-brand {
    font-weight: 900;
    font-size: 16pt;
    color: #00a79d;
}
.sidebar-sep {
    background-color: rgba(255,255,255,0.06);
    min-height: 1px;
}

/* ---- Başlık ---- */
.page-title {
    font-weight: 800;
    font-size: 22pt;
    color: #e2e8f0;
}

/* ---- Kartlar ---- */
.card {
    background-color: #1e293b;
    border-radius: 10px;
    padding: 18px 22px;
    margin: 6px 0px;
    border: 1px solid #334155;
}
.card-ok    { border-left: 4px solid #22c55e; }
.card-warn  { border-left: 4px solid #eab308; }
.card-fail  { border-left: 4px solid #ef4444; }
.card-wait  { border-left: 4px solid #475569; }

.card-title {
    font-weight: 700;
    font-size: 13pt;
    color: #e2e8f0;
}
.card-info {
    font-size: 10.5pt;
    color: #94a3b8;
    margin-top: 2px;
}
.status-icon {
    font-size: 22pt;
}

/* ---- Butonlar ---- */
.fix-button {
    background: #00a79d;
    color: white;
    font-weight: bold;
    border-radius: 6px;
    padding: 8px 20px;
    border: none;
}
.report-button {
    background: #334155;
    color: #e2e8f0;
    font-weight: bold;
    border-radius: 6px;
    padding: 8px 20px;
    border: none;
}

/* ---- Banner ---- */
.apt-banner {
    background-color: #854d0e;
    color: #fef3cd;
    font-weight: 600;
    font-size: 10.5pt;
    padding: 8px 16px;
    border-bottom: 1px solid #a16207;
}

/* ---- Terminal ---- */
.terminal-title {
    font-weight: bold;
    font-size: 13pt;
    color: #e2e8f0;
    margin-bottom: 4px;
}
.terminal-view {
    background-color: #020617;
    color: #d4d4d4;
    font-family: monospace;
    font-size: 11pt;
    padding: 14px;
    border-radius: 8px;
    border-left: 4px solid #00a79d;
}

/* ---- Ayarlar ---- */
.settings-section-title {
    font-weight: 700;
    font-size: 14pt;
    color: #e2e8f0;
    margin-bottom: 6px;
}
.settings-label {
    font-size: 11pt;
    color: #94a3b8;
}
"""


# ════════════════════════════════════════════════
#  SPLASH SCREEN
# ════════════════════════════════════════════════
class SplashScreen(Gtk.Window):
    def __init__(self, on_finished_cb):
        super().__init__(title="Pardus Healer")
        self.set_default_size(480, 300)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_decorated(False)
        self.set_resizable(False)
        self.on_finished_cb = on_finished_cb

        overlay = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        overlay.get_style_context().add_class("splash-bg")
        self.add(overlay)

        # Üst boşluk
        overlay.pack_start(Gtk.Label(label=""), True, True, 0)

        # Logo / Yazı
        logo_path = "/usr/share/pixmaps/pardus-logo.png"
        if os.path.exists(logo_path):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(logo_path, 80, 80, True)
                img = Gtk.Image.new_from_pixbuf(pixbuf)
                overlay.pack_start(img, False, False, 0)
            except Exception:
                pass

        title = Gtk.Label(label="Pardus Healer")
        title.get_style_context().add_class("splash-title")
        overlay.pack_start(title, False, False, 10)

        sub = Gtk.Label(label="Sistem tanılama başlatılıyor...")
        sub.get_style_context().add_class("splash-sub")
        overlay.pack_start(sub, False, False, 0)

        # Progress bar
        self.progress = Gtk.ProgressBar()
        self.progress.set_margin_start(60)
        self.progress.set_margin_end(60)
        self.progress.set_margin_top(20)
        overlay.pack_start(self.progress, False, False, 0)

        # Alt boşluk
        overlay.pack_start(Gtk.Label(label=""), True, True, 0)

        self.show_all()
        self._tick = 0
        GLib.timeout_add(20, self._animate)  # 20ms * 100 ≈ 2s

    def _animate(self):
        self._tick += 1
        self.progress.set_fraction(self._tick / 100.0)
        if self._tick >= 100:
            self.destroy()
            self.on_finished_cb()
            return False
        return True


# ════════════════════════════════════════════════
#  DIAGNOSTIC CARD
# ════════════════════════════════════════════════
class DiagnosticCard(Gtk.Box):
    """Tek bir tanılama kartı."""

    def __init__(self, icon_text, title, init_msg, check_func,
                 fix_command, log_callback, fix_label="Düzelt"):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        self.get_style_context().add_class("card")
        self.get_style_context().add_class("card-wait")

        self.title_text = title
        self.icon_text = icon_text
        self.check_func = check_func
        self.fix_command = fix_command
        self.log_callback = log_callback
        self.last_is_ok = None
        self.last_msg = init_msg

        # Sol: İkon
        self.icon_label = Gtk.Label(label=icon_text)
        self.icon_label.set_size_request(36, -1)
        self.pack_start(self.icon_label, False, False, 0)

        # Orta: Başlık + bilgi
        mid = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        self.title_label = Gtk.Label(label=title)
        self.title_label.set_halign(Gtk.Align.START)
        self.title_label.get_style_context().add_class("card-title")
        mid.pack_start(self.title_label, False, False, 0)

        self.info_label = Gtk.Label(label=init_msg)
        self.info_label.set_halign(Gtk.Align.START)
        self.info_label.set_line_wrap(True)
        self.info_label.get_style_context().add_class("card-info")
        mid.pack_start(self.info_label, False, False, 0)
        self.pack_start(mid, True, True, 0)

        # Spinner
        self.spinner = Gtk.Spinner()
        self.pack_start(self.spinner, False, False, 0)

        # Sağ: Durum ikonu
        self.status_label = Gtk.Label(label="⏳")
        self.status_label.get_style_context().add_class("status-icon")
        self.pack_start(self.status_label, False, False, 0)

        # Düzelt butonu
        self.fix_btn = Gtk.Button(label=fix_label)
        self.fix_btn.get_style_context().add_class("fix-button")
        self.fix_btn.set_no_show_all(True)
        self.fix_btn.set_visible(False)
        if self.fix_command:
            self.fix_btn.connect("clicked", self.on_fix_clicked)
        self.pack_start(self.fix_btn, False, False, 0)

    # ---- border renk yardımcıları ----
    def _set_border_class(self, cls):
        ctx = self.get_style_context()
        for c in ("card-ok", "card-warn", "card-fail", "card-wait"):
            ctx.remove_class(c)
        ctx.add_class(cls)

    # ---- check ----
    def run_check(self):
        self.status_label.set_label("⏳")
        self.info_label.set_label("Kontrol ediliyor...")
        self._set_border_class("card-wait")
        self.spinner.start()
        self.fix_btn.set_visible(False)
        thread = threading.Thread(target=self._run_check_thread, daemon=True)
        thread.start()

    def _run_check_thread(self):
        result = self.check_func()
        # result = (status, msg)  status: True / False / "warn"
        GLib.idle_add(self._update_ui, result[0], result[1])

    def _update_ui(self, status, msg):
        self.spinner.stop()
        self.info_label.set_label(msg)
        self.last_msg = msg

        if status is True:
            self.last_is_ok = True
            self.status_label.set_label("✅")
            self._set_border_class("card-ok")
            self.fix_btn.set_visible(False)
        elif status == "warn":
            self.last_is_ok = None  # uyarı
            self.status_label.set_label("⚠️")
            self._set_border_class("card-warn")
            self.fix_btn.set_visible(False)
        else:
            self.last_is_ok = False
            self.status_label.set_label("❌")
            self._set_border_class("card-fail")
            if self.fix_command:
                self.fix_btn.set_visible(True)

    # ---- fix ----
    def on_fix_clicked(self, widget):
        if not self.fix_command:
            return
        self.fix_btn.set_sensitive(False)
        self.log_callback(f"──▶ Çalıştırılıyor: {self.fix_command}")
        thread = threading.Thread(target=self._run_fix_thread, daemon=True)
        thread.start()

    def _run_fix_thread(self):
        try:
            proc = subprocess.Popen(
                self.fix_command, shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            for line in iter(proc.stdout.readline, ''):
                if line:
                    GLib.idle_add(self.log_callback, line.strip())
            proc.stdout.close()
            proc.wait()
            GLib.idle_add(self.log_callback,
                          f"İşlem tamamlandı (çıkış kodu: {proc.returncode})\n")
            GLib.idle_add(self.run_check)
        except Exception as e:
            GLib.idle_add(self.log_callback, f"Hata: {e}\n")
        finally:
            GLib.idle_add(self.fix_btn.set_sensitive, True)


# ════════════════════════════════════════════════
#  MAIN WINDOW
# ════════════════════════════════════════════════
class HealerApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Pardus Healer")
        self.set_default_size(1200, 800)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.maximize()

        self.dark_mode = False
        self.auto_interval = 0       # dakika (0 = kapalı)
        self._auto_timer_id = None

        # CSS uygula
        self.css_provider = Gtk.CssProvider()
        self._apply_css(CSS_LIGHT)

        # Ana kutu  =  sidebar | sağ içerik
        root_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.add(root_hbox)

        # ── Sidebar ──
        self.sidebar = self._build_sidebar()
        root_hbox.pack_start(self.sidebar, False, False, 0)

        # ── Sağ taraf (stack) ──
        self.right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.right_box.get_style_context().add_class("main-area")
        root_hbox.pack_start(self.right_box, True, True, 0)

        # APT bannerı (başlangıçta gizli)
        self.apt_banner = Gtk.Label(
            label="⚠  APT kontrolü için lütfen terminalde 'sudo' şifrenizi girin")
        self.apt_banner.get_style_context().add_class("apt-banner")
        self.apt_banner.set_no_show_all(True)
        self.apt_banner.set_visible(False)
        self.right_box.pack_start(self.apt_banner, False, False, 0)

        # Sayfa stack'i
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(200)
        self.right_box.pack_start(self.stack, True, True, 0)

        # Sayfa 1: Kontroller
        self.stack.add_named(self._build_checks_page(), "checks")
        # Sayfa 2: Ayarlar
        self.stack.add_named(self._build_settings_page(), "settings")

        self.stack.set_visible_child_name("checks")
        self.show_all()
        self.apt_banner.set_visible(False)

        # İlk kontrolü başlat
        self.on_refresh_all(None)

    # ───────── CSS ─────────
    def _apply_css(self, css_bytes):
        self.css_provider.load_from_data(css_bytes)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    # ───────── SIDEBAR ─────────
    def _build_sidebar(self):
        sb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        sb.get_style_context().add_class("sidebar")
        sb.set_size_request(210, -1)
        sb.set_margin_top(18)
        sb.set_margin_bottom(18)

        # Marka
        brand_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        brand_box.set_margin_start(18)
        brand_box.set_margin_end(18)
        brand_box.set_margin_bottom(6)

        logo_path = "/usr/share/pixmaps/pardus-logo.png"
        if os.path.exists(logo_path):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(logo_path, 28, 28, True)
                brand_box.pack_start(Gtk.Image.new_from_pixbuf(pixbuf), False, False, 0)
            except Exception:
                pass

        brand = Gtk.Label(label="Pardus Healer")
        brand.get_style_context().add_class("sidebar-brand")
        brand.set_halign(Gtk.Align.START)
        brand_box.pack_start(brand, False, False, 0)
        sb.pack_start(brand_box, False, False, 0)

        sep = Gtk.Separator()
        sep.get_style_context().add_class("sidebar-sep")
        sep.set_margin_start(14)
        sep.set_margin_end(14)
        sep.set_margin_top(4)
        sep.set_margin_bottom(4)
        sb.pack_start(sep, False, False, 0)

        # Menü butonları
        self.btn_checks = Gtk.Button(label="🩺  Kontroller")
        self.btn_checks.get_style_context().add_class("sidebar-btn-active")
        self.btn_checks.set_relief(Gtk.ReliefStyle.NONE)
        self.btn_checks.connect("clicked", self._on_nav, "checks")
        sb.pack_start(self.btn_checks, False, False, 0)

        self.btn_settings = Gtk.Button(label="⚙️  Ayarlar")
        self.btn_settings.get_style_context().add_class("sidebar-btn")
        self.btn_settings.set_relief(Gtk.ReliefStyle.NONE)
        self.btn_settings.connect("clicked", self._on_nav, "settings")
        sb.pack_start(self.btn_settings, False, False, 0)

        sb.pack_start(Gtk.Label(label=""), True, True, 0)  # spacer
        return sb

    def _on_nav(self, btn, page_name):
        self.stack.set_visible_child_name(page_name)
        # Active stilini değiştir
        for b, name in [(self.btn_checks, "checks"), (self.btn_settings, "settings")]:
            ctx = b.get_style_context()
            ctx.remove_class("sidebar-btn-active")
            ctx.remove_class("sidebar-btn")
            if name == page_name:
                ctx.add_class("sidebar-btn-active")
            else:
                ctx.add_class("sidebar-btn")

    # ───────── KONTROLLER SAYFASI ─────────
    def _build_checks_page(self):
        # Paned: üst = kartlar, alt = terminal
        paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)

        # --- Üst panel: kart listesi ---
        upper = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        upper.set_margin_start(24)
        upper.set_margin_end(24)
        upper.set_margin_top(18)
        upper.set_margin_bottom(8)

        title = Gtk.Label(label="Sistem Kontrolleri")
        title.set_halign(Gtk.Align.START)
        title.get_style_context().add_class("page-title")
        upper.pack_start(title, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.cards_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        scroll.add(self.cards_vbox)
        upper.pack_start(scroll, True, True, 0)

        # Alt butonlar
        btn_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        report_btn = Gtk.Button(label="📄  Sistem Raporu Oluştur")
        report_btn.get_style_context().add_class("report-button")
        report_btn.connect("clicked", self.on_generate_report)
        btn_bar.pack_start(report_btn, False, False, 0)

        refresh_btn = Gtk.Button(label="🔄  Tümünü Yeniden Kontrol Et")
        refresh_btn.get_style_context().add_class("fix-button")
        refresh_btn.connect("clicked", self.on_refresh_all)
        btn_bar.pack_end(refresh_btn, False, False, 0)
        upper.pack_start(btn_bar, False, False, 0)

        paned.pack1(upper, resize=True, shrink=False)

        # --- Alt panel: terminal ---
        lower = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        lower.set_margin_start(24)
        lower.set_margin_end(24)
        lower.set_margin_top(6)
        lower.set_margin_bottom(12)

        tlabel = Gtk.Label(label="Terminal Çıktısı")
        tlabel.set_halign(Gtk.Align.START)
        tlabel.get_style_context().add_class("terminal-title")
        lower.pack_start(tlabel, False, False, 0)

        term_scroll = Gtk.ScrolledWindow()
        term_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.terminal_view = Gtk.TextView()
        self.terminal_view.set_editable(False)
        self.terminal_view.set_cursor_visible(False)
        self.terminal_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.terminal_view.get_style_context().add_class("terminal-view")
        self.text_buffer = self.terminal_view.get_buffer()
        term_scroll.add(self.terminal_view)
        self.terminal_scroll = term_scroll
        lower.pack_start(term_scroll, True, True, 0)

        paned.pack2(lower, resize=True, shrink=False)
        paned.set_position(480)

        # Kartları oluştur
        self.cards = []
        self._create_cards()

        return paned

    # ───────── AYARLAR SAYFASI ─────────
    def _build_settings_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        page.set_margin_start(32)
        page.set_margin_end(32)
        page.set_margin_top(24)

        title = Gtk.Label(label="Ayarlar")
        title.set_halign(Gtk.Align.START)
        title.get_style_context().add_class("page-title")
        page.pack_start(title, False, False, 0)

        # ── Koyu / Açık mod ──
        sec1 = Gtk.Label(label="Görünüm")
        sec1.set_halign(Gtk.Align.START)
        sec1.get_style_context().add_class("settings-section-title")
        page.pack_start(sec1, False, False, 0)

        dark_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        dark_lbl = Gtk.Label(label="Koyu Mod")
        dark_lbl.get_style_context().add_class("settings-label")
        dark_row.pack_start(dark_lbl, False, False, 0)
        self.dark_switch = Gtk.Switch()
        self.dark_switch.set_active(False)
        self.dark_switch.connect("notify::active", self._on_dark_toggle)
        dark_row.pack_start(self.dark_switch, False, False, 0)
        page.pack_start(dark_row, False, False, 0)

        # ── Otomatik kontrol aralığı ──
        sep = Gtk.Separator()
        page.pack_start(sep, False, False, 6)

        sec2 = Gtk.Label(label="Otomatik Kontrol")
        sec2.set_halign(Gtk.Align.START)
        sec2.get_style_context().add_class("settings-section-title")
        page.pack_start(sec2, False, False, 0)

        intv_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        intv_lbl = Gtk.Label(label="Kontrol Aralığı")
        intv_lbl.get_style_context().add_class("settings-label")
        intv_row.pack_start(intv_lbl, False, False, 0)

        self.interval_combo = Gtk.ComboBoxText()
        self.interval_combo.append("0", "Kapalı")
        self.interval_combo.append("5", "5 Dakika")
        self.interval_combo.append("10", "10 Dakika")
        self.interval_combo.append("30", "30 Dakika")
        self.interval_combo.set_active_id("0")
        self.interval_combo.connect("changed", self._on_interval_changed)
        intv_row.pack_start(self.interval_combo, False, False, 0)
        page.pack_start(intv_row, False, False, 0)

        page.pack_start(Gtk.Label(label=""), True, True, 0)
        return page

    # ── Ayar callback'leri ──
    def _on_dark_toggle(self, switch, _pspec):
        self.dark_mode = switch.get_active()
        self._apply_css(CSS_DARK if self.dark_mode else CSS_LIGHT)

    def _on_interval_changed(self, combo):
        val = int(combo.get_active_id())
        self.auto_interval = val
        if self._auto_timer_id:
            GLib.source_remove(self._auto_timer_id)
            self._auto_timer_id = None
        if val > 0:
            self._auto_timer_id = GLib.timeout_add_seconds(
                val * 60, self._auto_refresh)
            self.log_terminal(f"Otomatik kontrol aralığı: {val} dakika olarak ayarlandı.")
        else:
            self.log_terminal("Otomatik kontrol kapatıldı.")

    def _auto_refresh(self):
        self.log_terminal("── Otomatik kontrol başlatıldı ──")
        self.on_refresh_all(None)
        return True  # tekrarla

    # ───────── KARTLAR ─────────
    def _create_cards(self):
        defs = [
            ("🌐", "İnternet Bağlantısı", "Bağlantı kontrol ediliyor...",
             self.check_internet,
             "pkexec systemctl restart NetworkManager", "Düzelt"),
            ("📦", "APT Depo Sağlığı", "Depolar kontrol ediliyor...",
             self.check_apt_health,
             "pkexec apt-get update && pkexec dpkg --configure -a", "Düzelt"),
            ("🔧", "Bozuk Paketler", "Paketler kontrol ediliyor...",
             self.check_broken_packages,
             "pkexec apt-get install -f -y", "Düzelt"),
            ("🔄", "Bekleyen Güncellemeler", "Güncellemeler kontrol ediliyor...",
             self.check_updates,
             "pkexec apt-get upgrade -y", "Güncelle"),
            ("💾", "Disk Doluluk Durumu", "Disk alanı kontrol ediliyor...",
             self.check_disk_space,
             "pkexec apt-get clean && pkexec apt-get autoremove -y", "Temizle"),
            ("🧠", "RAM Kullanımı", "Bellek bilgisi alınıyor...",
             self.check_ram_usage, None, ""),
            ("🌡️", "CPU Sıcaklığı", "Sıcaklık kontrol ediliyor...",
             self.check_cpu_temp, None, ""),
        ]
        for icon, title, msg, func, cmd, flbl in defs:
            card = DiagnosticCard(
                icon, title, msg, func, cmd, self.log_terminal, fix_label=flbl)
            self.cards_vbox.pack_start(card, False, False, 0)
            self.cards.append(card)

    # ───────── TERMINAL ─────────
    def log_terminal(self, text):
        end = self.text_buffer.get_end_iter()
        self.text_buffer.insert(end, text + "\n")
        adj = self.terminal_scroll.get_vadjustment()
        GLib.idle_add(lambda: adj.set_value(adj.get_upper() - adj.get_page_size()))

    # ───────── BUTONLAR ─────────
    def on_refresh_all(self, widget):
        self.log_terminal("── Tüm kontroller yeniden başlatılıyor ──")
        for card in self.cards:
            card.run_check()

    def on_generate_report(self, widget):
        home = os.path.expanduser("~")
        path = os.path.join(home, "pardus-healer-rapor.txt")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("=" * 54 + "\n")
                f.write("  PARDUS HEALER SİSTEM RAPORU\n")
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"  Tarih / Saat : {now}\n")
                f.write("=" * 54 + "\n\n")
                for c in self.cards:
                    if c.last_is_ok is True:
                        tag = "TAMAM"
                    elif c.last_is_ok is False:
                        tag = "SORUNLU"
                    else:
                        tag = "UYARI"
                    f.write(f"[{tag}]  {c.title_text}\n")
                    f.write(f"         {c.last_msg}\n\n")
            self.log_terminal(f"Rapor kaydedildi → {path}")
            dlg = Gtk.MessageDialog(
                transient_for=self, flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Rapor Oluşturuldu")
            dlg.format_secondary_text(f"Dosya: {path}")
            dlg.run()
            dlg.destroy()
        except Exception as e:
            self.log_terminal(f"Rapor hatası: {e}")

    # ═══════════════════════════════════════
    #  KONTROL FONKSİYONLARI
    # ═══════════════════════════════════════
    def check_internet(self):
        try:
            socket.setdefaulttimeout(3)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("8.8.8.8", 53))
            s.close()
            return True, "İnternet bağlantısı aktif."
        except socket.error:
            return False, "İnternet bağlantısı yok!"

    def check_apt_health(self):
        GLib.idle_add(self.apt_banner.set_visible, True)
        try:
            result = subprocess.run(
                ["sudo", "apt-get", "check"],
                capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return True, "APT depoları sağlıklı çalışıyor."
            else:
                return False, "APT depolarında sorun var!"
        except FileNotFoundError:
            return False, "apt-get komutu bulunamadı."
        except subprocess.TimeoutExpired:
            return False, "APT kontrolü zaman aşımına uğradı."
        finally:
            GLib.idle_add(self.apt_banner.set_visible, False)

    def check_broken_packages(self):
        try:
            result = subprocess.run(
                ["dpkg", "--audit"], capture_output=True, text=True)
            if not result.stdout.strip() and result.returncode == 0:
                return True, "Bozuk paket bulunamadı."
            else:
                return False, "Bozuk paketler tespit edildi!"
        except FileNotFoundError:
            return False, "dpkg komutu bulunamadı."

    def check_updates(self):
        try:
            result = subprocess.run(
                ["apt-get", "-s", "upgrade"],
                capture_output=True, text=True,
                env={**os.environ, "LANG": "C"})
            if "0 upgraded, 0 newly installed" in result.stdout:
                return True, "Sisteminiz güncel, bekleyen güncelleme yok."
            lines = result.stdout.split('\n')
            info = next((l for l in lines if "upgraded" in l), "")
            return False, f"Güncelleme var: {info}"
        except FileNotFoundError:
            return False, "apt-get komutu yok."

    def check_disk_space(self):
        try:
            st = os.statvfs("/")
            total = st.f_frsize * st.f_blocks
            free = st.f_frsize * st.f_bfree
            used = total - free
            pct = int(used / total * 100)
            avail_gb = free / (1024 ** 3)
            msg = f"Boş Alan: {avail_gb:.1f} GB  (Kullanım: %{pct})"
            if pct > 90:
                return False, f"Disk kritik seviyede dolu! {msg}"
            elif pct > 80:
                return "warn", f"Disk dolmak üzere. {msg}"
            return True, f"Disk durumu normal. {msg}"
        except Exception:
            return False, "Disk bilgisi alınamadı."

    def check_ram_usage(self):
        try:
            total = avail = 0
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        total = int(line.split()[1])
                    elif line.startswith("MemAvailable:"):
                        avail = int(line.split()[1])
            if total == 0:
                return False, "RAM bilgisi okunamadı."
            used = total - avail
            pct = int(used / total * 100)
            used_gb = used / (1024 * 1024)
            total_gb = total / (1024 * 1024)
            msg = f"{used_gb:.1f} GB / {total_gb:.1f} GB  (%{pct})"
            if pct > 90:
                return False, f"RAM kritik! {msg}"
            elif pct > 70:
                return "warn", f"RAM yüksek. {msg}"
            return True, f"RAM normal. {msg}"
        except Exception:
            return False, "RAM bilgisi alınamadı."

    def check_cpu_temp(self):
        # 1) sensors
        try:
            r = subprocess.run(["sensors"], capture_output=True, text=True)
            if r.returncode == 0:
                mx = 0.0
                for line in r.stdout.split('\n'):
                    if '°C' in line:
                        for p in line.split():
                            if '°C' in p:
                                try:
                                    v = float(p.replace('+', '').replace('°C', ''))
                                    if 0 < v < 150 and v > mx:
                                        mx = v
                                except ValueError:
                                    pass
                if mx > 0:
                    return self._temp_status(mx)
        except FileNotFoundError:
            pass

        # 2) sysfs
        try:
            with open("/sys/class/thermal/thermal_zone0/temp") as f:
                return self._temp_status(int(f.read().strip()) / 1000.0)
        except Exception:
            # VM veya sensör yok
            return "warn", "Sanal makine — sensör mevcut değil."

    @staticmethod
    def _temp_status(t):
        msg = f"Sıcaklık: {t:.1f} °C"
        if t > 80:
            return False, f"CPU aşırı ısınıyor! {msg}"
        if t > 60:
            return "warn", f"CPU sıcaklığı yüksek. {msg}"
        return True, f"CPU sıcaklığı normal. {msg}"


# ════════════════════════════════════════════════
#  ENTRY POINT
# ════════════════════════════════════════════════
def main():
    # Splash → ardından ana pencere
    def show_app():
        app = HealerApp()
        app.connect("destroy", Gtk.main_quit)

    splash = SplashScreen(on_finished_cb=show_app)
    splash.connect("destroy", lambda *_: None)   # splash kapanınca quit etme
    Gtk.main()


if __name__ == "__main__":
    main()
