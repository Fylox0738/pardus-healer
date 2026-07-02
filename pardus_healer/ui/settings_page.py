"""Ayarlar sayfası: görünüm (koyu mod) ve otomatik kontrol aralığı."""

from __future__ import annotations

from typing import Callable

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from .. import __version__


class SettingsPage(Gtk.Box):
    def __init__(
        self,
        dark_mode: bool,
        auto_interval: int,
        advisor_mode: str,
        ollama_available: bool,
        on_dark_toggle: Callable[[bool], None],
        on_interval_change: Callable[[int], None],
        on_advisor_change: Callable[[str], None],
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.set_margin_start(32)
        self.set_margin_end(32)
        self.set_margin_top(24)
        self._on_dark_toggle = on_dark_toggle
        self._on_interval_change = on_interval_change
        self._on_advisor_change = on_advisor_change

        title = Gtk.Label(label="Ayarlar")
        title.set_halign(Gtk.Align.START)
        title.get_style_context().add_class("page-title")
        self.pack_start(title, False, False, 0)

        # ── Görünüm ──
        sec1 = Gtk.Label(label="Görünüm")
        sec1.set_halign(Gtk.Align.START)
        sec1.get_style_context().add_class("settings-section-title")
        self.pack_start(sec1, False, False, 0)

        dark_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        dark_lbl = Gtk.Label(label="Koyu Mod")
        dark_lbl.get_style_context().add_class("settings-label")
        dark_row.pack_start(dark_lbl, False, False, 0)
        self.dark_switch = Gtk.Switch()
        self.dark_switch.set_active(dark_mode)
        self.dark_switch.set_valign(Gtk.Align.CENTER)
        self.dark_switch.connect("notify::active", self._dark_changed)
        dark_row.pack_start(self.dark_switch, False, False, 0)
        self.pack_start(dark_row, False, False, 0)

        self.pack_start(Gtk.Separator(), False, False, 6)

        # ── Otomatik kontrol ──
        sec2 = Gtk.Label(label="Otomatik Kontrol")
        sec2.set_halign(Gtk.Align.START)
        sec2.get_style_context().add_class("settings-section-title")
        self.pack_start(sec2, False, False, 0)

        intv_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        intv_lbl = Gtk.Label(label="Kontrol Aralığı")
        intv_lbl.get_style_context().add_class("settings-label")
        intv_row.pack_start(intv_lbl, False, False, 0)

        self.interval_combo = Gtk.ComboBoxText()
        for value, label in [
            ("0", "Kapalı"), ("5", "5 Dakika"),
            ("10", "10 Dakika"), ("30", "30 Dakika"), ("60", "1 Saat"),
        ]:
            self.interval_combo.append(value, label)
        self.interval_combo.set_active_id(str(auto_interval))
        self.interval_combo.connect("changed", self._interval_changed)
        intv_row.pack_start(self.interval_combo, False, False, 0)
        self.pack_start(intv_row, False, False, 0)

        self.pack_start(Gtk.Separator(), False, False, 6)

        # ── Akıllı öneri motoru ──
        sec3 = Gtk.Label(label="Akıllı Öneri Motoru")
        sec3.set_halign(Gtk.Align.START)
        sec3.get_style_context().add_class("settings-section-title")
        self.pack_start(sec3, False, False, 0)

        adv_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        adv_lbl = Gtk.Label(label="Değerlendirme Motoru")
        adv_lbl.get_style_context().add_class("settings-label")
        adv_row.pack_start(adv_lbl, False, False, 0)
        self.advisor_combo = Gtk.ComboBoxText()
        self.advisor_combo.append("rule", "Kural Tabanlı (önerilen, hızlı)")
        self.advisor_combo.append("ollama", "Yerel Yapay Zekâ (Ollama)")
        self.advisor_combo.set_active_id(
            advisor_mode if advisor_mode in ("rule", "ollama") else "rule")
        self.advisor_combo.connect("changed", self._advisor_changed)
        adv_row.pack_start(self.advisor_combo, False, False, 0)
        self.pack_start(adv_row, False, False, 0)

        note = (
            "Kural Tabanlı motor internet ve güçlü donanım gerektirmez; her "
            "makinede (akıllı tahtalar dâhil) anında çalışır.\n"
            "Yerel Yapay Zekâ, cihazda kurulu Ollama ile daha doğal açıklamalar "
            "üretir; yalnızca gücü yeten makinelerde önerilir.\n"
        )
        note += (
            "Durum: Ollama algılandı ✓" if ollama_available
            else "Durum: Ollama bu cihazda bulunamadı — seçilse bile otomatik "
            "olarak Kural Tabanlı motora düşülür."
        )
        adv_note = Gtk.Label(label=note)
        adv_note.set_halign(Gtk.Align.START)
        adv_note.set_xalign(0.0)
        adv_note.set_line_wrap(True)
        adv_note.get_style_context().add_class("settings-label")
        self.pack_start(adv_note, False, False, 0)

        self.pack_start(Gtk.Separator(), False, False, 6)

        # ── Hakkında ──
        sec3 = Gtk.Label(label="Hakkında")
        sec3.set_halign(Gtk.Align.START)
        sec3.get_style_context().add_class("settings-section-title")
        self.pack_start(sec3, False, False, 0)

        about = Gtk.Label(
            label=f"Pardus Healer v{__version__}\n"
            "Akıllı sistem tanılama ve iyileştirme aracı.\n"
            "İnternetsiz çalışan kural tabanlı teşhis motoru."
        )
        about.set_halign(Gtk.Align.START)
        about.set_xalign(0.0)
        about.get_style_context().add_class("settings-label")
        self.pack_start(about, False, False, 0)

        self.pack_start(Gtk.Label(label=""), True, True, 0)

    def _dark_changed(self, switch, _pspec):
        self._on_dark_toggle(switch.get_active())

    def _interval_changed(self, combo):
        active = combo.get_active_id()
        if active is not None:
            self._on_interval_change(int(active))

    def _advisor_changed(self, combo):
        active = combo.get_active_id()
        if active is not None:
            self._on_advisor_change(active)
