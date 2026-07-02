"""Açılış (splash) ekranı."""

from __future__ import annotations

import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GdkPixbuf, GLib, Gtk  # noqa: E402


class SplashScreen(Gtk.Window):
    def __init__(self, on_finished_cb):
        super().__init__(title="Pardus Healer")
        self.set_default_size(480, 300)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_decorated(False)
        self.set_resizable(False)
        self.on_finished_cb = on_finished_cb

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.get_style_context().add_class("splash-bg")
        self.add(box)

        box.pack_start(Gtk.Label(label=""), True, True, 0)

        logo_path = "/usr/share/pixmaps/pardus-logo.png"
        if os.path.exists(logo_path):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    logo_path, 80, 80, True)
                box.pack_start(Gtk.Image.new_from_pixbuf(pixbuf), False, False, 0)
            except Exception:
                pass

        title = Gtk.Label(label="Pardus Healer")
        title.get_style_context().add_class("splash-title")
        box.pack_start(title, False, False, 10)

        sub = Gtk.Label(label="Akıllı sistem tanılaması başlatılıyor...")
        sub.get_style_context().add_class("splash-sub")
        box.pack_start(sub, False, False, 0)

        self.progress = Gtk.ProgressBar()
        self.progress.set_margin_start(60)
        self.progress.set_margin_end(60)
        self.progress.set_margin_top(20)
        box.pack_start(self.progress, False, False, 0)

        box.pack_start(Gtk.Label(label=""), True, True, 0)

        self.show_all()
        self._tick = 0
        GLib.timeout_add(18, self._animate)

    def _animate(self):
        self._tick += 1
        self.progress.set_fraction(self._tick / 100.0)
        if self._tick >= 100:
            self.destroy()
            self.on_finished_cb()
            return False
        return True
