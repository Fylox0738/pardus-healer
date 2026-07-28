"""Filo (Swarm) Yönetimi Arayüzü."""

import threading
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

from pardus_healer.swarm.client import discover_nodes, get_node_health, heal_node

class SwarmPage(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.set_margin_top(24)
        self.set_margin_bottom(24)
        self.set_margin_start(32)
        self.set_margin_end(32)

        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        title = Gtk.Label(label="<span font='18' weight='bold'>Filo (Swarm) Yöneticisi</span>")
        title.set_use_markup(True)
        title.set_halign(Gtk.Align.START)
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
