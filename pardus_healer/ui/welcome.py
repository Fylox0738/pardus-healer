"""İlk açılış tanıtım turu.

Teknik olmayan kullanıcılara (ör. okuldaki öğretmenlere) uygulamanın ne işe
yaradığını birkaç adımda anlatır. İlk çalıştırmada otomatik açılır; ayrıca
kenar çubuğundaki '?' düğmesiyle tekrar açılabilir.
"""

from __future__ import annotations

from typing import Callable, Optional

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

_STEPS = [
    ("🩺", "Pardus Healer'a Hoş Geldiniz",
     "Bu araç bilgisayarınızı sizin yerinize kontrol eder: yavaşlama, "
     "donma, dolu disk, güncelleme ve güvenlik gibi sorunları bulur.\n\n"
     "Hiçbir teknik bilgi ya da terminal gerektirmez."),
    ("🔍", "1. Tara",
     "Uygulama açılır açılmaz sisteminizi otomatik tarar. İsterseniz "
     "“Tümünü Yeniden Kontrol Et” ile istediğiniz an yeniden tarayabilirsiniz.\n\n"
     "Sonuçlar renkli kartlarda görünür: ✅ iyi, ⚠️ dikkat, ❌ sorun."),
    ("🧠", "2. Anla",
     "“Genel Bakış” ekranı size bir sağlık puanı (0–100) verir ve "
     "sorunların GERÇEK nedenini açıklar.\n\n"
     "Örneğin: “Disk dolu olduğu için güncellemeler başarısız oluyor — "
     "önce diski temizleyin.”"),
    ("⚡", "3. Tek Tıkla Düzelt",
     "Bir sorunun yanındaki “Düzelt” düğmesine ya da “Otomatik Onar” "
     "düğmesine basmanız yeter. Gerekirse yönetici parolası bir pencerede "
     "istenir.\n\n"
     "Bittiğinde isterseniz şık bir rapor da oluşturabilirsiniz."),
    ("✅", "Hazırsınız!",
     "Artık sisteminizi tek bir yerden sağlıklı tutabilirsiniz.\n\n"
     "Bu turu istediğiniz zaman sol menüdeki “?” düğmesinden yeniden "
     "açabilirsiniz. İyi kullanımlar!"),
]


class WelcomeDialog(Gtk.Window):
    def __init__(self, parent: Optional[Gtk.Window], on_done: Callable[[], None]):
        super().__init__(title="Tanıtım")
        self.on_done = on_done
        self._index = 0
        self.set_default_size(560, 420)
        self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        self.set_modal(True)
        if parent is not None:
            self.set_transient_for(parent)
        self.set_resizable(False)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        root.get_style_context().add_class("welcome-bg")
        self.add(root)

        # içerik
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        content.set_margin_top(36)
        content.set_margin_bottom(20)
        content.set_margin_start(40)
        content.set_margin_end(40)
        content.set_valign(Gtk.Align.CENTER)
        root.pack_start(content, True, True, 0)

        self.icon_lbl = Gtk.Label()
        self.icon_lbl.get_style_context().add_class("welcome-icon")
        content.pack_start(self.icon_lbl, False, False, 0)

        self.title_lbl = Gtk.Label()
        self.title_lbl.get_style_context().add_class("welcome-title")
        self.title_lbl.set_line_wrap(True)
        self.title_lbl.set_justify(Gtk.Justification.CENTER)
        content.pack_start(self.title_lbl, False, False, 0)

        self.body_lbl = Gtk.Label()
        self.body_lbl.get_style_context().add_class("welcome-body")
        self.body_lbl.set_line_wrap(True)
        self.body_lbl.set_justify(Gtk.Justification.CENTER)
        self.body_lbl.set_max_width_chars(52)
        content.pack_start(self.body_lbl, False, False, 0)

        # adım göstergesi (noktalar)
        self.dots = Gtk.Label()
        self.dots.get_style_context().add_class("welcome-dots")
        content.pack_start(self.dots, False, False, 0)

        # alt buton çubuğu
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        bar.set_margin_bottom(18)
        bar.set_margin_start(24)
        bar.set_margin_end(24)
        self.skip_btn = Gtk.Button(label="Geç")
        self.skip_btn.get_style_context().add_class("report-button")
        self.skip_btn.connect("clicked", lambda _b: self._finish())
        bar.pack_start(self.skip_btn, False, False, 0)

        bar.pack_start(Gtk.Label(label=""), True, True, 0)

        self.next_btn = Gtk.Button(label="İleri  ›")
        self.next_btn.get_style_context().add_class("fix-button")
        self.next_btn.connect("clicked", lambda _b: self._next())
        bar.pack_end(self.next_btn, False, False, 0)
        root.pack_start(bar, False, False, 0)

        self._render()

    def _render(self):
        icon, title, body = _STEPS[self._index]
        self.icon_lbl.set_label(icon)
        self.title_lbl.set_label(title)
        self.body_lbl.set_label(body)
        self.dots.set_label(
            "  ".join("●" if i == self._index else "○"
                      for i in range(len(_STEPS))))
        last = self._index == len(_STEPS) - 1
        self.next_btn.set_label("Başla  ✓" if last else "İleri  ›")
        self.skip_btn.set_visible(not last)

    def _next(self):
        if self._index >= len(_STEPS) - 1:
            self._finish()
        else:
            self._index += 1
            self._render()

    def _finish(self):
        self.on_done()
        self.destroy()
