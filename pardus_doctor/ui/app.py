import gi
import threading
import os
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk

from pardus_doctor.core.log_reader import LogReader
from pardus_doctor.core.git_analyzer import GitAnalyzer
from pardus_doctor.core.ai_engine import AIEngine
from pardus_doctor.core.safety import check_command_safety
from pardus_healer.ui import theme

class DoctorApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Pardus Doctor - Akıllı Hata Dedektifi")
        self.set_default_size(1000, 650)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # İkon yükleme
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "doctor.svg")
        if not os.path.exists(icon_path): icon_path = "/usr/share/pardus-suite/assets/doctor.svg"
        if os.path.exists(icon_path): self.set_icon_from_file(icon_path)
        
        provider = Gtk.CssProvider()
        provider.load_from_data(theme.get_css(dark=True))
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_vbox)
        
        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header.get_style_context().add_class("sidebar")
        header.set_margin_all(20)
        
        title = Gtk.Label()
        title.set_markup("<span size='18000' weight='heavy' color='white'>🩺 Pardus Doctor</span>")
        header.pack_start(title, False, False, 0)
        main_vbox.pack_start(header, False, False, 0)
        
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        main_vbox.pack_start(paned, True, True, 0)
        
        # Left Panel (Controls)
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        left_box.set_margin_all(20)
        paned.pack1(left_box, resize=False, shrink=False)
        paned.set_position(320)
        
        lbl_repo = Gtk.Label(label="Proje Git Klasörü (Opsiyonel):")
        lbl_repo.set_halign(Gtk.Align.START)
        left_box.pack_start(lbl_repo, False, False, 0)
        
        # Varsayılan olarak bulunduğu dizini koysun (gerçek bir kullanıcı repoda olabilir)
        self.entry_repo = Gtk.Entry(text=os.getcwd())
        left_box.pack_start(self.entry_repo, False, False, 0)
        
        lbl_model = Gtk.Label(label="Yapay Zeka (LLM) Modeli:")
        lbl_model.set_halign(Gtk.Align.START)
        left_box.pack_start(lbl_model, False, False, 0)
        
        self.combo_model = Gtk.ComboBoxText()
        self.combo_model.append("llama3.2", "Llama 3.2 (3B - Standart)")
        self.combo_model.append("mistral", "Mistral (7B - Güçlü PC)")
        self.combo_model.append("gemma2:2b", "Gemma 2 (2B - Eski PC)")
        self.combo_model.append("qwen2.5:7b", "Qwen 2.5 (7B - Gelişmiş)")
        self.combo_model.set_active_id("llama3.2")
        self.combo_model.connect("changed", self._on_model_changed)
        left_box.pack_start(self.combo_model, False, False, 0)
        
        btn_scan = Gtk.Button(label="🔍 Logları ve Kodu Tara")
        btn_scan.get_style_context().add_class("fix-button")
        btn_scan.connect("clicked", self.on_start_scan)
        left_box.pack_start(btn_scan, False, False, 10)
        
        self.status_lbl = Gtk.Label(label="Hazır.")
        self.status_lbl.set_halign(Gtk.Align.START)
        left_box.pack_start(self.status_lbl, False, False, 0)
        
        info_frame = Gtk.Frame()
        info_frame.get_style_context().add_class("card")
        i_lbl = Gtk.Label(label="Pardus Doctor arka planda sisteminizin 'journalctl', 'dmesg' ve 'syslog' bileşenlerini tarar.\n\nEğer yukarıda bir Git klasörü belirtirseniz, sistem analizinde bulduğu çökmeleri Git tarihçesindeki (commit) değişikliklerle eşleştirerek sorunun temel kaynağını yapay zeka yardımıyla raporlar.")
        i_lbl.set_line_wrap(True)
        info_frame.add(i_lbl)
        i_lbl.set_margin_all(14)
        left_box.pack_end(info_frame, False, False, 0)

        # Right Panel (Terminal / Report)
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        right_box.set_margin_all(20)
        paned.pack2(right_box, resize=True, shrink=False)
        
        title_rep = Gtk.Label()
        title_rep.set_markup("<span size='14000' weight='bold'>Teşhis Raporu</span>")
        title_rep.set_halign(Gtk.Align.START)
        right_box.pack_start(title_rep, False, False, 0)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.text_view = Gtk.TextView()
        self.text_view.set_editable(False)
        self.text_view.set_cursor_visible(False)
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text_view.get_style_context().add_class("terminal-view")
        scroll.add(self.text_view)
        right_box.pack_start(scroll, True, True, 0)
        
        self.text_buffer = self.text_view.get_buffer()
        self.text_buffer.create_tag("bold", weight=700, foreground="#22c55e")
        self.text_buffer.create_tag("header", weight=700, foreground="#00a79d")
        
        # Copilot (Doğal Dil Terminali)
        copilot_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        right_box.pack_end(copilot_box, False, False, 10)
        
        lbl_ai = Gtk.Label()
        lbl_ai.set_markup("<b>🤖 Copilot NLP:</b>")
        copilot_box.pack_start(lbl_ai, False, False, 0)
        
        self.entry_copilot = Gtk.Entry()
        self.entry_copilot.set_placeholder_text("Örn: WiFi kartını kapatıp aç veya 80 portunu aç...")
        self.entry_copilot.connect("activate", self.on_copilot_submit)
        copilot_box.pack_start(self.entry_copilot, True, True, 0)
        
        self.btn_copilot = Gtk.Button(label="Çevir ve Çalıştır")
        self.btn_copilot.get_style_context().add_class("fix-button")
        self.btn_copilot.connect("clicked", self.on_copilot_submit)
        copilot_box.pack_start(self.btn_copilot, False, False, 0)

        self.ai = AIEngine()
        
    def write_report(self, text, tag=""):
        end = self.text_buffer.get_end_iter()
        if tag:
            self.text_buffer.insert_with_tags_by_name(end, text + "\n", tag)
        else:
            self.text_buffer.insert(end, text + "\n")
        
        # Otomatik scroll
        adj = scroll = self.text_view.get_parent().get_vadjustment()
        adj.set_value(adj.get_upper())

    def _on_model_changed(self, combo):
        model_id = combo.get_active_id()
        if model_id and hasattr(self, 'ai'):
            self.ai.set_model_name(model_id)
            self.write_report(f"⚙️ Aktif Yapay Zeka Motoru değiştirildi: {model_id}", "cmd")

    def on_start_scan(self, btn):
        btn.set_sensitive(False)
        self.text_buffer.set_text("")
        self.status_lbl.set_text("Analiz yapılıyor... Lütfen bekleyin.")
        self.write_report("── Çekirdek ve Sistem Günlükleri Okunuyor ──", "header")
        
        repo_path = self.entry_repo.get_text()
        
        def run():
            logs = LogReader.get_critical_logs(100)
            dmesg = LogReader.get_dmesg_errors()
            all_logs = logs + dmesg
            
            git = GitAnalyzer(repo_path)
            commits = git.get_recent_commits(30)
            matches = git.match_logs_to_commits(all_logs, commits)
            
            GLib.idle_add(self.write_report, f"✔ Toplam {len(all_logs)} kritik donanım/çekirdek logu hafızaya alındı.")
            if commits:
                GLib.idle_add(self.write_report, f"✔ Seçili Git dizininde {len(commits)} değişiklik (commit) taraması yapıldı.")
            
            if matches:
                GLib.idle_add(self.write_report, "\n--- Şüpheli Yazılım Geliştirme Eşleşmeleri ---", "bold")
                for m in matches:
                    c = m['commit']
                    GLib.idle_add(self.write_report, f"Commit Hash : {c['hash']} ({c['date_iso']})")
                    GLib.idle_add(self.write_report, f"Açıklaması  : {c['message']} - {c['author']}")
                    GLib.idle_add(self.write_report, f"Kanıt İzi   : Tam bu değişiklikle aynı gün {len(m['logs'])} kez çökme/panik raporlanmış!\n")
            
            GLib.idle_add(self.write_report, "\n── Yapay Zeka & Kural Raporu Hazırlanıyor ──", "header")
            
            # Yerel Ollama AI cagrisi yapiliyor (internetsiz)
            report = self.ai.generate_report(all_logs, matches)
            
            GLib.idle_add(self.write_report, report + "\n", "bold")
            GLib.idle_add(self.status_lbl.set_text, "Analiz Tamamlandı.")
            GLib.idle_add(btn.set_sensitive, True)

        threading.Thread(target=run, daemon=True).start()

    def on_copilot_submit(self, widget):
        text = self.entry_copilot.get_text().strip()
        if not text: return
        
        self.write_report(f"\n👤 Seni Anlıyorum: '{text}'...", "header")
        self.entry_copilot.set_sensitive(False)
        self.btn_copilot.set_sensitive(False)
        
        def run_copilot():
            cmd = self.ai.translate_to_bash(text)
            if cmd.startswith("HATA"):
                GLib.idle_add(self.write_report, cmd, "bold")
            else:
                GLib.idle_add(self.confirm_and_run_bash, cmd)
                
            GLib.idle_add(self.entry_copilot.set_sensitive, True)
            GLib.idle_add(self.btn_copilot.set_sensitive, True)
            GLib.idle_add(self.entry_copilot.set_text, "")
            
        threading.Thread(target=run_copilot, daemon=True).start()
        
    def confirm_and_run_bash(self, cmd):
        safe, reason = check_command_safety(cmd)
        if not safe:
            self.write_report(f"⚙️ Önerilen Komut: {cmd}", "bold")
            self.write_report(
                f"🛑 Bu komut güvenlik nedeniyle ÇALIŞTIRILMADI: {reason} riski tespit edildi.",
                "bold",
            )
            return

        self.write_report(f"⚙️ Önerilen Komut: {cmd}", "bold")
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Copilot Komut Çalıştırma Onayı"
        )
        dialog.format_secondary_text(f"Pardus Yapay Zeka Copilot aşağıdaki Bash komutunu üretip, senin yerine çalıştırmak istiyor:\n\n{cmd}\n\nEmin misiniz?")
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            self.write_report("▶ Komut çalıştırılıyor...", "header")
            try:
                import subprocess
                p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if p.stdout: self.write_report(p.stdout)
                if p.stderr: self.write_report("Hata Çıktısı:\n" + p.stderr)
                self.write_report(f"✅ Çıkış Kodu: {p.returncode}", "bold")
            except Exception as e:
                self.write_report(f"❌ Çalıştırma hatası: {e}", "bold")
        else:
            self.write_report("🚫 İşlem İptal Edildi.", "bold")
