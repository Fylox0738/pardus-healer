"""SOS Kartı diyaloğu — "Yardım İste" butonuna basınca açılır.

Healer'ın son tanı sonucunu yarışma talep formuna (Başlık / Hata türü /
Önem derecesi / Adım adım senaryo / Gerçekleşen-Olması gereken sonuç)
oturan bir metne çevirir; panoya kopyalama, e-posta ile gönderme,
ekran görüntüsü alma ve isteğe bağlı "Pardus Nabız" katkısı sunar.
"""

from __future__ import annotations

import os

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gtk  # noqa: E402

from ..core import pulse
from ..core.bug_report import SosReport, build_mailto_url, format_ticket_text
from .pulse_dialog import PulseDialog


class SosDialog(Gtk.Dialog):
    def __init__(self, parent: Gtk.Window, sos: SosReport):
        super().__init__(title="🆘 SOS Kartı — Yardım İste", transient_for=parent, modal=True)
        self.sos = sos
        self.set_default_size(640, 580)
        self.add_button("Kapat", Gtk.ResponseType.CLOSE)

        box = self.get_content_area()
        box.set_spacing(10)
        box.set_margin_start(18)
        box.set_margin_end(18)
        box.set_margin_top(14)
        box.set_margin_bottom(10)

        summary_lbl = Gtk.Label(label=sos.plain_summary)
        summary_lbl.set_line_wrap(True)
        summary_lbl.set_xalign(0.0)
        summary_lbl.get_style_context().add_class("assessment-box")
        box.pack_start(summary_lbl, False, False, 0)

        ticket_title = Gtk.Label(
            label="Yarışma formatına hazır rapor (kopyalayıp yapıştırabilirsiniz):"
        )
        ticket_title.set_halign(Gtk.Align.START)
        ticket_title.get_style_context().add_class("settings-section-title")
        box.pack_start(ticket_title, False, False, 4)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        self.text_view = Gtk.TextView()
        self.text_view.set_editable(False)
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text_view.get_buffer().set_text(format_ticket_text(sos))
        scroll.add(self.text_view)
        box.pack_start(scroll, True, True, 0)

        # ---- bölge girişi (yalnızca Pardus Nabız için, opsiyonel) ----
        region_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        region_lbl = Gtk.Label(label="İlçe/Bölge (opsiyonel):")
        region_box.pack_start(region_lbl, False, False, 0)
        self.region_entry = Gtk.Entry()
        self.region_entry.set_placeholder_text("örn. Kadıköy")
        region_box.pack_start(self.region_entry, True, True, 0)
        box.pack_start(region_box, False, False, 0)

        self.pulse_check = Gtk.CheckButton(
            label="Pardus Nabız'a anonim katkı sağla (yalnızca sorun adı + bölge; kişisel veri yok)"
        )
        self.pulse_check.set_active(True)
        box.pack_start(self.pulse_check, False, False, 0)

        # ---- aksiyonlar ----
        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        copy_btn = Gtk.Button(label="📋 Panoya Kopyala")
        copy_btn.get_style_context().add_class("fix-button")
        copy_btn.connect("clicked", self._on_copy)
        actions.pack_start(copy_btn, False, False, 0)

        mail_btn = Gtk.Button(label="✉️ Formatör Öğretmene Gönder")
        mail_btn.get_style_context().add_class("fix-button")
        mail_btn.connect("clicked", self._on_mail)
        actions.pack_start(mail_btn, False, False, 0)

        shot_btn = Gtk.Button(label="📸 Ekran Görüntüsü Al")
        shot_btn.get_style_context().add_class("fix-button")
        shot_btn.connect("clicked", self._on_screenshot)
        actions.pack_start(shot_btn, False, False, 0)

        pulse_btn = Gtk.Button(label="📡 Pardus Nabız'ı Gör")
        pulse_btn.connect("clicked", self._on_view_pulse)
        actions.pack_start(pulse_btn, False, False, 0)

        box.pack_start(actions, False, False, 6)

        self.status_lbl = Gtk.Label(label="")
        self.status_lbl.set_halign(Gtk.Align.START)
        self.status_lbl.set_line_wrap(True)
        box.pack_start(self.status_lbl, False, False, 0)

        self.connect("response", self._on_response)
        self.show_all()

    def _on_copy(self, _btn):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(format_ticket_text(self.sos), -1)
        clipboard.store()
        self.status_lbl.set_text("✅ Rapor panoya kopyalandı.")

    def _on_mail(self, _btn):
        url = build_mailto_url(self.sos)
        try:
            Gtk.show_uri_on_window(self, url, Gdk.CURRENT_TIME)
            self.status_lbl.set_text("✅ E-posta istemciniz açıldı.")
        except Exception as exc:
            self._on_copy(_btn)
            self.status_lbl.set_text(
                f"⚠️ E-posta istemcisi açılamadı ({exc}); rapor bunun yerine panoya kopyalandı."
            )

    def _on_screenshot(self, _btn):
        target = self.get_transient_for() or self
        gdk_window = target.get_window()
        if gdk_window is None:
            self.status_lbl.set_text("⚠️ Ekran görüntüsü alınamadı (pencere hazır değil).")
            return
        width, height = gdk_window.get_width(), gdk_window.get_height()
        pixbuf = Gdk.pixbuf_get_from_window(gdk_window, 0, 0, width, height)
        if pixbuf is None:
            self.status_lbl.set_text("⚠️ Ekran görüntüsü alınamadı.")
            return
        out_dir = os.path.expanduser("~/Pictures")
        os.makedirs(out_dir, exist_ok=True)
        safe_ts = self.sos.generated_at.replace(":", "-").replace(" ", "_")
        path = os.path.join(out_dir, f"pardus-sos-{safe_ts}.png")
        pixbuf.savev(path, "png", [], [])
        self.status_lbl.set_text(f"✅ Ekran görüntüsü kaydedildi: {path}")

    def _on_view_pulse(self, _btn):
        dlg = PulseDialog(self)
        dlg.run()
        dlg.destroy()

    def _on_response(self, _dialog, _response):
        if self.pulse_check.get_active():
            pulse.record_event(self.sos.primary_issue, self.region_entry.get_text())
        self.destroy()
