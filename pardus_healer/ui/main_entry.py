"""Uygulama giriş akışı: splash → ana pencere."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from .app import HealerApp
from .splash import SplashScreen


def launch() -> None:
    holder = {}

    def show_app():
        app = HealerApp()
        app.connect("destroy", Gtk.main_quit)
        holder["app"] = app

    splash = SplashScreen(on_finished_cb=show_app)
    splash.connect("destroy", lambda *_: None)
    Gtk.main()
