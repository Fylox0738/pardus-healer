"""Pardus Nabız görünümü: yerel SOS Kartı olaylarının basit, sıralı bir
özetini gösterir ("bu hafta hangi sorun, kaç bölgede görüldü?").

Gerçek bir sunucu/toplama altyapısı yoktur — bu tamamen yerel, opt-in
verilerin (bkz. ``core/pulse.py``) bir görünümüdür. Demo amaçlı örnek
veri ayrı bir dosyada tutulur, "Demo Verisi Göster" ile açıkça
görünür kılınır ve her zaman 🧪 etiketiyle gerçek veriden ayrı gösterilir.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from ..core import pulse


class PulseDialog(Gtk.Dialog):
    def __init__(self, parent: Gtk.Window):
        super().__init__(title="📡 Pardus Nabız", transient_for=parent, modal=True)
        self.set_default_size(480, 420)
        self.add_button("Kapat", Gtk.ResponseType.CLOSE)

        box = self.get_content_area()
        box.set_spacing(10)
        box.set_margin_start(18)
        box.set_margin_end(18)
        box.set_margin_top(14)
        box.set_margin_bottom(10)

        intro = Gtk.Label(
            label=(
                "Farklı Pardus kurulumlarından, kullanıcı onayıyla paylaşılan "
                "anonim SOS Kartı olaylarının yerel özeti. Aynı sorun birden "
                "fazla yerde tekrarlanıyorsa burada görünür."
            )
        )
        intro.set_line_wrap(True)
        intro.set_xalign(0.0)
        box.pack_start(intro, False, False, 0)

        self._show_demo = False

        self.list_box = Gtk.ListBox()
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        scroll.add(self.list_box)
        box.pack_start(scroll, True, True, 0)

        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.demo_toggle = Gtk.CheckButton(label="🧪 Demo verisini göster")
        self.demo_toggle.connect("toggled", self._on_toggle_demo)
        btn_row.pack_start(self.demo_toggle, False, False, 0)
        demo_seed_btn = Gtk.Button(label="Demo Verisi Ekle")
        demo_seed_btn.connect("clicked", self._on_load_demo)
        btn_row.pack_start(demo_seed_btn, False, False, 0)
        demo_clear_btn = Gtk.Button(label="Demo Verisini Temizle")
        demo_clear_btn.connect("clicked", self._on_clear_demo)
        btn_row.pack_start(demo_clear_btn, False, False, 0)
        refresh_btn = Gtk.Button(label="🔄 Yenile")
        refresh_btn.connect("clicked", lambda _b: self.refresh())
        btn_row.pack_start(refresh_btn, False, False, 0)
        box.pack_start(btn_row, False, False, 4)

        self.refresh()
        self.show_all()

    def _on_load_demo(self, _btn):
        pulse.seed_demo_data()
        self.demo_toggle.set_active(True)
        self.refresh()

    def _on_clear_demo(self, _btn):
        pulse.clear_demo_data()
        self.refresh()

    def _on_toggle_demo(self, btn):
        self._show_demo = btn.get_active()
        self.refresh()

    def refresh(self):
        for child in self.list_box.get_children():
            self.list_box.remove(child)

        events = pulse.load_events(include_demo=self._show_demo)
        if not events:
            row = Gtk.ListBoxRow()
            lbl = Gtk.Label(
                label="Henüz gerçek veri yok. \"Demo Verisi Ekle\" ve "
                "\"Demo verisini göster\" ile örnek görebilirsiniz."
            )
            lbl.set_margin_top(8)
            lbl.set_margin_bottom(8)
            row.add(lbl)
            self.list_box.add(row)
            self.list_box.show_all()
            return

        for issue, real_count, demo_count, regions in pulse.top_issues(events):
            row = Gtk.ListBoxRow()
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            vbox.set_margin_top(8)
            vbox.set_margin_bottom(8)
            vbox.set_margin_start(6)
            vbox.set_margin_end(6)

            if demo_count and real_count:
                count_text = f"{real_count} gerçek + 🧪 {demo_count} demo bölgede görüldü"
            elif demo_count:
                count_text = f"🧪 {demo_count} demo bölgede görüldü (gerçek veri yok)"
            else:
                count_text = f"{real_count} bölgede görüldü"
            head = Gtk.Label(label=f"⚠️ {issue} — {count_text}")
            head.set_xalign(0.0)
            head.get_style_context().add_class("insight-title")
            vbox.pack_start(head, False, False, 0)

            region_lbl = Gtk.Label(label="Bölgeler: " + ", ".join(regions))
            region_lbl.set_xalign(0.0)
            region_lbl.set_line_wrap(True)
            vbox.pack_start(region_lbl, False, False, 0)

            row.add(vbox)
            self.list_box.add(row)
        self.list_box.show_all()
