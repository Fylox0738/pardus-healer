import gi
import subprocess
import threading
import socket
import os

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango

# Pardus stili modern ve temiz CSS (Pardus Turkuazı)
CSS = """
window {
    background-color: #f4f6f9;
}

.header-title {
    font-weight: 800;
    font-size: 24pt;
    color: #00a79d; /* Pardus Turkuazı */
    margin-bottom: 5px;
}

.card {
    background-color: #ffffff;
    border-radius: 12px;
    padding: 20px 24px;
    margin: 8px 4px;
    border: 1px solid #e1e8ed;
    box-shadow: 0px 4px 16px rgba(26, 43, 76, 0.05); /* Yumuşak ve modern gölge */
}

.card-title {
    font-weight: 800;
    font-size: 15pt;
    color: #1a2b4c; /* Koyu lacivert */
}

.card-info {
    font-size: 11pt;
    color: #4a5568; /* Okunabilir gri/mavi */
    margin-top: 4px;
}

.status-icon {
    font-size: 24pt;
}

/* Buton Tasarımı */
.fix-button {
    background: #00a79d;
    color: white;
    font-weight: bold;
    border-radius: 6px;
    padding: 8px 20px;
    border: none;
}

.terminal-title {
    font-weight: bold;
    font-size: 14pt;
    color: #1a2b4c;
    margin-top: 15px;
    margin-bottom: 5px;
}

.terminal-view {
    background-color: #1e2124;
    color: #d4d4d4;
    font-family: monospace;
    font-size: 11.5pt;
    padding: 18px;
    border-radius: 8px;
    border-left: 4px solid #00a79d;
}
""".encode('utf-8')

class HealerApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Pardus Healer")
        self.set_default_size(1200, 800)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # CSS Yükleme
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        self.main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.main_vbox.set_margin_start(20)
        self.main_vbox.set_margin_end(20)
        self.main_vbox.set_margin_top(20)
        self.main_vbox.set_margin_bottom(20)
        self.add(self.main_vbox)

        # Başlık
        header_label = Gtk.Label(label="Sistem Tanılama ve Onarım")
        header_label.set_halign(Gtk.Align.START)
        header_label.get_style_context().add_class("header-title")
        self.main_vbox.pack_start(header_label, False, False, 10)

        # Kartlar için kaydırılabilir alan
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.cards_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.scroll.add(self.cards_vbox)
        self.main_vbox.pack_start(self.scroll, True, True, 0)
        
        # Terminal çıktısı alanı
        terminal_label = Gtk.Label(label="Terminal Çıktısı")
        terminal_label.set_halign(Gtk.Align.START)
        terminal_label.get_style_context().add_class("terminal-title")
        self.main_vbox.pack_start(terminal_label, False, False, 0)

        self.terminal_scroll = Gtk.ScrolledWindow()
        self.terminal_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.terminal_scroll.set_size_request(-1, 200)
        self.terminal_view = Gtk.TextView()
        self.terminal_view.set_editable(False)
        self.terminal_view.set_cursor_visible(False)
        self.terminal_view.get_style_context().add_class("terminal-view")
        self.text_buffer = self.terminal_view.get_buffer()
        self.terminal_scroll.add(self.terminal_view)
        self.main_vbox.pack_start(self.terminal_scroll, False, False, 0)

        # Tümünü Yenile Butonu
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        refresh_btn = Gtk.Button(label="Tümünü Yeniden Kontrol Et")
        refresh_btn.get_style_context().add_class("fix-button")
        refresh_btn.connect("clicked", self.on_refresh_all)
        btn_box.pack_end(refresh_btn, False, False, 0)
        self.main_vbox.pack_end(btn_box, False, False, 0)

        self.cards = []
        self.create_cards()
        self.show_all()
        self.on_refresh_all(None)

    def log_terminal(self, text):
        end_iter = self.text_buffer.get_end_iter()
        self.text_buffer.insert(end_iter, text + "\n")
        
        # Otomatik en alta kaydır
        adj = self.terminal_scroll.get_vadjustment()
        GLib.idle_add(lambda: adj.set_value(adj.get_upper() - adj.get_page_size()))

    def create_cards(self):
        # 1. İnternet Bağlantısı
        card1 = DiagnosticCard(
            "İnternet Bağlantısı", 
            "Bağlantı kontrol ediliyor...",
            self.check_internet,
            "pkexec systemctl restart NetworkManager",
            self.log_terminal
        )
        self.cards_vbox.pack_start(card1, False, False, 0)
        self.cards.append(card1)

        # 2. APT Depo Sağlığı (apt-get check)
        card2 = DiagnosticCard(
            "APT Depo Sağlığı", 
            "Depolar kontrol ediliyor...",
            self.check_apt_health,
            "pkexec apt-get update && pkexec dpkg --configure -a",
            self.log_terminal
        )
        self.cards_vbox.pack_start(card2, False, False, 0)
        self.cards.append(card2)

        # 3. Bozuk Paketler (dpkg --audit)
        card3 = DiagnosticCard(
            "Bozuk Paketler", 
            "Paketler kontrol ediliyor...",
            self.check_broken_packages,
            "pkexec apt-get install -f -y",
            self.log_terminal
        )
        self.cards_vbox.pack_start(card3, False, False, 0)
        self.cards.append(card3)

        # 4. Bekleyen Güncellemeler
        card4 = DiagnosticCard(
            "Bekleyen Güncellemeler", 
            "Güncellemeler kontrol ediliyor...",
            self.check_updates,
            "pkexec apt-get upgrade -y",
            self.log_terminal
        )
        self.cards_vbox.pack_start(card4, False, False, 0)
        self.cards.append(card4)

        # 5. Disk Doluluk Durumu
        card5 = DiagnosticCard(
            "Disk Doluluk Durumu", 
            "Disk alanı kontrol ediliyor...",
            self.check_disk_space,
            "pkexec apt-get clean && pkexec apt-get autoremove -y",
            self.log_terminal,
            fix_label="Temizle"
        )
        self.cards_vbox.pack_start(card5, False, False, 0)
        self.cards.append(card5)

    def on_refresh_all(self, widget):
        for card in self.cards:
            card.run_check()

    # --- Kontrol Fonksiyonları ---
    def check_internet(self):
        try:
            socket.setdefaulttimeout(3)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            return True, "İnternet bağlantısı aktif."
        except socket.error:
            return False, "İnternet bağlantısı yok!"

    def check_apt_health(self):
        try:
            result = subprocess.run(["sudo", "apt-get", "check"], capture_output=True, text=True)
            if result.returncode == 0:
                return True, "APT depoları sağlıklı çalışıyor."
            else:
                return False, "APT depolarında sorun var!"
        except FileNotFoundError:
            return False, "apt-get komutu bulunamadı (Pardus / Debian tabanlı sistem gerektirir)."

    def check_broken_packages(self):
        try:
            result = subprocess.run(["dpkg", "--audit"], capture_output=True, text=True)
            if not result.stdout.strip() and result.returncode == 0:
                return True, "Bozuk paket bulunamadı."
            else:
                return False, "Bozuk paketler tespit edildi!"
        except FileNotFoundError:
            return False, "dpkg komutu bulunamadı."

    def check_updates(self):
        try:
            # -s parametresi simüle eder
            result = subprocess.run(["apt-get", "-s", "upgrade"], capture_output=True, text=True, env=dict(os.environ, LANG="C"))
            if "0 upgraded, 0 newly installed" in result.stdout:
                return True, "Sisteminiz güncel, bekleyen güncelleme yok."
            else:
                lines = result.stdout.split('\\n')
                upgradable = next((line for line in lines if "upgraded" in line), "")
                return False, f"Güncelleme var: {upgradable}"
        except FileNotFoundError:
            return False, "Kontrol edilemedi, apt-get komutu yok."

    def check_disk_space(self):
        try:
            stat_info = os.statvfs("/")
            total_bytes = stat_info.f_frsize * stat_info.f_blocks
            free_bytes = stat_info.f_frsize * stat_info.f_bfree
            used_bytes = total_bytes - free_bytes
            
            use_percent = int((used_bytes / total_bytes) * 100)
            avail_gb = free_bytes / (1024**3)
            
            msg = f"Boş Alan: {avail_gb:.1f} GB (Kullanım: %{use_percent})"
            if use_percent > 90:
                return False, f"Disk kritik seviyede dolu! {msg}"
            elif use_percent > 80:
                return False, f"Disk dolmak üzere! {msg}"
            else:
                return True, f"Disk durumu normal. {msg}"
        except Exception:
            return False, "Disk bilgisi alınırken hata oluştu."


class DiagnosticCard(Gtk.Box):
    def __init__(self, title, init_msg, check_func, fix_command, log_callback, fix_label="Düzelt"):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        self.get_style_context().add_class("card")
        
        self.check_func = check_func
        self.fix_command = fix_command
        self.log_callback = log_callback

        # Durum İkonu
        self.status_label = Gtk.Label(label="⏳")
        self.status_label.get_style_context().add_class("status-icon")
        self.pack_start(self.status_label, False, False, 0)

        # Başlık ve Bilgi Metni
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.title_label = Gtk.Label(label=title)
        self.title_label.set_halign(Gtk.Align.START)
        self.title_label.get_style_context().add_class("card-title")
        vbox.pack_start(self.title_label, False, False, 0)

        self.info_label = Gtk.Label(label=init_msg)
        self.info_label.set_halign(Gtk.Align.START)
        self.info_label.get_style_context().add_class("card-info")
        vbox.pack_start(self.info_label, False, False, 0)
        
        self.pack_start(vbox, True, True, 0)

        # Yükleme Animatörü
        self.spinner = Gtk.Spinner()
        self.pack_start(self.spinner, False, False, 0)

        # Düzelt Butonu
        self.fix_btn = Gtk.Button(label=fix_label)
        self.fix_btn.get_style_context().add_class("fix-button")
        self.fix_btn.set_visible(False)
        self.fix_btn.connect("clicked", self.on_fix_clicked)
        self.pack_start(self.fix_btn, False, False, 0)

    def run_check(self):
        self.status_label.set_label("⏳")
        self.info_label.set_label("Kontrol ediliyor...")
        self.spinner.start()
        self.fix_btn.set_visible(False)
        
        # Arayüzün donmaması için thread kullanıyoruz
        thread = threading.Thread(target=self._run_check_thread)
        thread.daemon = True
        thread.start()

    def _run_check_thread(self):
        is_ok, msg = self.check_func()
        GLib.idle_add(self._update_ui, is_ok, msg)

    def _update_ui(self, is_ok, msg):
        self.spinner.stop()
        self.info_label.set_label(msg)
        if is_ok:
            self.status_label.set_label("✅")
            self.fix_btn.set_visible(False)
        else:
            self.status_label.set_label("❌")
            if self.fix_command:
                self.fix_btn.set_visible(True)

    def on_fix_clicked(self, widget):
        self.fix_btn.set_sensitive(False)
        self.log_callback(f"--> Çalıştırılıyor: {self.fix_command}")
        
        thread = threading.Thread(target=self._run_fix_thread)
        thread.daemon = True
        thread.start()

    def _run_fix_thread(self):
        try:
            # pkexec komutu arka planda terminali veya GUİ polkit auth arayüzünü tetikler 
            process = subprocess.Popen(
                self.fix_command, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True
            )
            # Terminal çıktısını canlı oku
            for line in iter(process.stdout.readline, ''):
                if line:
                    GLib.idle_add(self.log_callback, line.strip())
            process.stdout.close()
            process.wait()
            
            GLib.idle_add(self.log_callback, f"İşlem tamamlandı (Çıkış kodu: {process.returncode})\\n")
            
            # İşlem bitince kartı tekrar kontrol et
            GLib.idle_add(self.run_check)
            
        except Exception as e:
            GLib.idle_add(self.log_callback, f"Hata: {str(e)}\\n")
        finally:
            GLib.idle_add(self.fix_btn.set_sensitive, True)


if __name__ == "__main__":
    app = HealerApp()
    app.connect("destroy", Gtk.main_quit)
    Gtk.main()
