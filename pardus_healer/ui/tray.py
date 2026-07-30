"""Görev Çubuğu (System Tray) Uygulaması.

Arka planda çalışır, sistem durumuna göre ikonu değiştirir.
Tıklanınca ana pencereyi açar.
"""

from __future__ import annotations

import os
import threading
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, GLib, AppIndicator3

from pardus_healer.core.engine import DiagnosisEngine
from pardus_healer.core.models import Status
from pardus_healer.ui.main_entry import launch

# Görev çubuğu jenerik sistem ikonları (security-high/medium/low) kullanıyordu
# — marka taşımıyordu. Artık gerçek Healer ikonu
# kullanılıyor; durum, ikon yerine menü metninde iletiliyor.
_ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "assets",
)
if not os.path.isdir(_ASSETS_DIR):
    _ASSETS_DIR = "/usr/share/pardus-suite/assets"

class HealerTray:
    def __init__(self):
        self.indicator = AppIndicator3.Indicator.new(
            "pardus-healer-tray",
            "healer",
            AppIndicator3.IndicatorCategory.SYSTEM_SERVICES
        )
        if os.path.isdir(_ASSETS_DIR):
            self.indicator.set_icon_theme_path(_ASSETS_DIR)
        self.indicator.set_icon_full("healer", "Pardus Healer")
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        
        self.menu = Gtk.Menu()
        
        self.status_item = Gtk.MenuItem(label="Durum: Hesaplanıyor...")
        self.status_item.set_sensitive(False)
        self.menu.append(self.status_item)
        
        self.menu.append(Gtk.SeparatorMenuItem())
        
        item_open = Gtk.MenuItem(label="Pardus Healer'ı Aç")
        item_open.connect('activate', self.on_open_clicked)
        self.menu.append(item_open)
        
        item_quit = Gtk.MenuItem(label="Çıkış")
        item_quit.connect('activate', self.on_quit_clicked)
        self.menu.append(item_quit)
        
        self.menu.show_all()
        self.indicator.set_menu(self.menu)
        
        self.engine = DiagnosisEngine()
        self._worker_thread = None
        
        # Her 30 dakikada bir arkaplan taraması yapıp ikonu güncelle
        GLib.timeout_add_seconds(1800, self._check_health)
        # İlk kontrolü hemen başlat
        GLib.idle_add(self._check_health)

    def on_open_clicked(self, widget):
        # Arayüzü ayrı bir thread'de açmak yerine GLib main loop içinde başlat
        launch()

    def on_quit_clicked(self, widget):
        Gtk.main_quit()

    def _check_health(self):
        if self._worker_thread and self._worker_thread.is_alive():
            return True # Önceki tarama bitmemişse üst üste yığma (Thread stacking)
            
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()
        return True

    def _worker(self):
        report = self.engine.run_all(concurrent=True)
        GLib.idle_add(self._update_ui, report)

    def _update_ui(self, report):
        self.indicator.set_icon_full("healer", f"Pardus Healer — Skor {report.health_score}")
        if report.health_score >= 80:
            self.status_item.set_label(f"Durum: Sağlıklı (Skor: {report.health_score})")
        elif report.health_score >= 50:
            self.status_item.set_label(f"Durum: Uyarılar Var (Skor: {report.health_score})")
        else:
            self.status_item.set_label(f"Durum: Kritik Arızalar! (Skor: {report.health_score})")

def run_tray():
    HealerTray()
    Gtk.main()

if __name__ == "__main__":
    run_tray()
