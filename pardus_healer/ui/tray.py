"""Görev Çubuğu (System Tray) Uygulaması.

Arka planda çalışır, sistem durumuna göre ikonu değiştirir.
Tıklanınca ana pencereyi açar.
"""

from __future__ import annotations

import threading
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, GLib, AppIndicator3

from pardus_healer.core.engine import DiagnosisEngine
from pardus_healer.core.models import Status
from pardus_healer.ui.main_entry import launch

class HealerTray:
    def __init__(self):
        self.indicator = AppIndicator3.Indicator.new(
            "pardus-healer-tray",
            "security-high", # Varsayılan ikon
            AppIndicator3.IndicatorCategory.SYSTEM_SERVICES
        )
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
        threading.Thread(target=self._worker, daemon=True).start()
        return True

    def _worker(self):
        report = self.engine.run_all(concurrent=True)
        GLib.idle_add(self._update_ui, report)

    def _update_ui(self, report):
        if report.health_score >= 80:
            self.indicator.set_icon_full("security-high", "Sistem Sağlıklı")
            self.status_item.set_label(f"Durum: Sağlıklı (Skor: {report.health_score})")
        elif report.health_score >= 50:
            self.indicator.set_icon_full("security-medium", "Sistem Uyarısı")
            self.status_item.set_label(f"Durum: Uyarılar Var (Skor: {report.health_score})")
        else:
            self.indicator.set_icon_full("security-low", "Kritik Durum")
            self.status_item.set_label(f"Durum: Kritik Arızalar! (Skor: {report.health_score})")

def run_tray():
    HealerTray()
    Gtk.main()

if __name__ == "__main__":
    run_tray()
