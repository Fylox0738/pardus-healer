"""Filo (Swarm) Yönetimi Arayüzü."""

import threading
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk, GLib

from pardus_healer.config import Config
from pardus_healer.swarm.client import discover_nodes, get_node_health, heal_node

class SwarmPage(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.set_margin_top(24)
        self.set_margin_bottom(24)
        self.set_margin_start(32)
        self.set_margin_end(32)

        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        title = Gtk.Label(label="Filo (Swarm) Yöneticisi")
        title.set_halign(Gtk.Align.START)
        title.get_style_context().add_class("page-title")
        header_box.pack_start(title, True, True, 0)

        self.refresh_btn = Gtk.Button(label="Ağı Tara")
        self.refresh_btn.get_style_context().add_class("btn-action")
        self.refresh_btn.connect("clicked", self.on_refresh_clicked)
        header_box.pack_start(self.refresh_btn, False, False, 0)

        self.heal_all_btn = Gtk.Button(label="Tüm Ağı Onar")
        self.heal_all_btn.get_style_context().add_class("btn-danger")
        self.heal_all_btn.connect("clicked", self.on_heal_all_clicked)
        self.heal_all_btn.set_sensitive(False)
        header_box.pack_start(self.heal_all_btn, False, False, 10)

        self.pack_start(header_box, False, False, 0)

        # Ağ anahtarı (swarm_token) her makinede rastgele ve BAĞIMSIZ
        # üretiliyordu; hiçbir arayüz onu göstermiyor/eşleştirmiyordu.
        # Sonuç: filodaki cihazlar birbirini asla doğrulayamıyordu (403) —
        # özellik arayüz düzeyinde fiilen çalışamaz durumdaydı (bkz.
        # TECHNICAL_AUDIT.md / DEVELOPMENT_OPPORTUNITIES.md).
        self._config = Config()
        token_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        token_lbl = Gtk.Label(label="Ağ Anahtarı:")
        token_lbl.set_halign(Gtk.Align.START)
        token_box.pack_start(token_lbl, False, False, 0)

        self.token_entry = Gtk.Entry()
        self.token_entry.set_text(self._config.swarm_token)
        self.token_entry.set_width_chars(34)
        token_box.pack_start(self.token_entry, True, True, 0)

        apply_btn = Gtk.Button(label="Uygula")
        apply_btn.connect("clicked", self.on_apply_token)
        token_box.pack_start(apply_btn, False, False, 0)

        copy_btn = Gtk.Button(label="Kopyala")
        copy_btn.connect("clicked", self.on_copy_token)
        token_box.pack_start(copy_btn, False, False, 0)
        self.pack_start(token_box, False, False, 0)

        token_hint = Gtk.Label(
            label="Filodaki tüm bilgisayarlarda AYNI anahtar olmalı; aksi "
            "halde cihazlar birbirini doğrulayamaz (403 Yetkisiz Erişim)."
        )
        token_hint.set_halign(Gtk.Align.START)
        token_hint.set_line_wrap(True)
        token_hint.get_style_context().add_class("card-info")
        self.pack_start(token_hint, False, False, 0)

        # Liste Görüntüsü
        self.store = Gtk.ListStore(str, str, str, str) # IP, Hostname, Skor, Durum
        self.treeview = Gtk.TreeView(model=self.store)
        
        for i, column_title in enumerate(["IP Adresi", "Bilgisayar Adı", "Sağlık Skoru", "Ağ Durumu"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            self.treeview.append_column(column)
            
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.add(self.treeview)
        scroll.set_vexpand(True)
        self.pack_start(scroll, True, True, 0)

        # Log
        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.log_view.get_style_context().add_class("terminal-log")
        scroll_log = Gtk.ScrolledWindow()
        scroll_log.add(self.log_view)
        scroll_log.set_size_request(-1, 150)
        self.pack_start(scroll_log, False, False, 0)
        
        # Sağ tık menüsü (Context Menu)
        self.menu = Gtk.Menu()
        item_heal = Gtk.MenuItem(label="Sadece Bu Cihazı Onar")
        item_heal.connect("activate", self.on_heal_single)
        self.menu.append(item_heal)
        self.menu.show_all()
        
        self.treeview.connect("button-press-event", self.on_treeview_button_press)
        
        self.nodes = []

    def on_apply_token(self, _btn):
        value = self.token_entry.get_text().strip()
        if value:
            self._config.swarm_token = value
            self.log("Ağ anahtarı güncellendi. Aynı anahtarı diğer tüm cihazlara da girin.")

    def on_copy_token(self, _btn):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(self.token_entry.get_text(), -1)
        self.log("Ağ anahtarı panoya kopyalandı.")

    def on_treeview_button_press(self, widget, event):
        # Sağ tıklamayı yakala
        if event.button == 3:
            path_info = self.treeview.get_path_at_pos(int(event.x), int(event.y))
            if path_info:
                path, col, cell_x, cell_y = path_info
                self.treeview.set_cursor(path, col, 0)
                self.menu.popup(None, None, None, None, event.button, event.time)
            return True
        return False

    def on_heal_single(self, widget):
        selection = self.treeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is not None:
            ip = model[treeiter][0]
            hostname = model[treeiter][1]
            
            # Seçili düğümün portunu bul
            port = "4243"
            for node in self.nodes:
                if node['ip'] == ip:
                    port = node['port']
                    break
                    
            self.log(f"Özel Onarım: {hostname} ({ip}) cihazına komut gönderiliyor...")
            threading.Thread(target=self._heal_single_worker, args=(ip, port), daemon=True).start()

    def _heal_single_worker(self, ip, port):
        success = heal_node(ip, port)
        if success:
            GLib.idle_add(self.log, f"✓ {ip} onarımı başlattı.")
        else:
            GLib.idle_add(self.log, f"✗ {ip} yanıt vermedi veya token geçersiz.")

    def log(self, text: str):
        buf = self.log_view.get_buffer()
        it = buf.get_end_iter()
        buf.insert(it, text + "\n")
        
        # Otomatik kaydırma
        adj = self.log_view.get_vadjustment()
        adj.set_value(adj.get_upper())

    def on_refresh_clicked(self, _btn):
        self.refresh_btn.set_sensitive(False)
        self.store.clear()
        self.nodes = []
        self.log("Ağdaki Pardus Healer (Swarm) düğümleri aranıyor...")
        threading.Thread(target=self._refresh_worker, daemon=True).start()

    def _refresh_worker(self):
        try:
            discovered = discover_nodes(timeout=3.0)
            if not discovered:
                GLib.idle_add(self.log, "Ağda başka bir düğüm bulunamadı.")
            else:
                for node in discovered:
                    ip = node['ip']
                    hostname = node['hostname']
                    port = node['port']
                    GLib.idle_add(self.log, f"Bulundu: {hostname} ({ip})")
                    
                    health = get_node_health(ip, port)
                    if health:
                        score = f"{health['health_score']}/100 ({health['grade']})"
                        status = "Bağlantı Kuruldu"
                    else:
                        score = "Bilinmiyor"
                        status = "Erişim Yok"
                        
                    self.nodes.append({"ip": ip, "port": port})
                    GLib.idle_add(self.store.append, [ip, hostname, score, status])
                    
                if self.nodes:
                    GLib.idle_add(self.heal_all_btn.set_sensitive, True)
        except Exception as e:
            GLib.idle_add(self.log, f"Hata: {e}")
        finally:
            GLib.idle_add(self.refresh_btn.set_sensitive, True)

    def on_heal_all_clicked(self, _btn):
        if not self.nodes:
            return
            
        dlg = Gtk.MessageDialog(
            transient_for=self.get_toplevel(), flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Ağdaki {len(self.nodes)} bilgisayara onarım komutu gönderilecek. Onaylıyor musunuz?",
        )
        response = dlg.run()
        dlg.destroy()
        
        if response == Gtk.ResponseType.YES:
            self.heal_all_btn.set_sensitive(False)
            self.log("Tüm ağa onarım komutu gönderiliyor...")
            threading.Thread(target=self._heal_all_worker, daemon=True).start()

    def _heal_all_worker(self):
        for node in self.nodes:
            ip = node['ip']
            port = node['port']
            GLib.idle_add(self.log, f"Komut gönderiliyor -> {ip}...")
            
            success = heal_node(ip, port)
            if success:
                GLib.idle_add(self.log, f"✓ {ip} onarımı başlattı.")
            else:
                GLib.idle_add(self.log, f"✗ {ip} yanıt vermedi.")
                
        GLib.idle_add(self.heal_all_btn.set_sensitive, True)
        GLib.idle_add(self.log, "Ağ onarımı komutları tamamlandı. Düğümler kendi kendini iyileştirecektir.")
