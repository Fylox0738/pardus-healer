import json
import urllib.request

class AIEngine:
    def __init__(self, ollama_host="http://localhost:11434"):
        self.host = ollama_host
        self.model_name = "llama3.2" # Standart veya mistral kullanılabilir

    def set_model_name(self, model_name):
        """Ayarlar/Doctor arayüzündeki model seçiciden çağrılır."""
        if model_name:
            self.model_name = model_name

    def check_ollama_available(self):
        try:
            req = urllib.request.Request(f"{self.host}/api/tags")
            with urllib.request.urlopen(req, timeout=1.5) as response:
                return response.status == 200
        except:
            return False

    def generate_report(self, logs, commits_matches):
        if not logs and not commits_matches:
            return "✅ Harika haber! Sistemde analiz edilecek kritik bir hata veya çökme kaydı bulunamadı."
            
        # 1. Kural Bazlı Rapor (Ollama kapalıysa veya hata verirse fallback)
        fallback_report = self._rule_based_analysis(logs, commits_matches)
        
        # 2. Ollama AI Raporlaması
        if self.check_ollama_available():
            try:
                prompt_text = "Sen bir Linux sistem onarım uzmanı 'Pardus Doctor' sun. Sana verilen sistem loglarını Türkçe ve anlaşılır özetle.\nLoglar:\n"
                prompt_text += "\n".join(logs[:20]) # Çok uzun olmasını önlemek için limit
                if commits_matches:
                    prompt_text += "\n\nŞüpheli Git Commitleri (Hatalarla aynı gün atılmış):\n"
                    for match in commits_matches:
                        c = match['commit']
                        prompt_text += f"- {c['hash']}: {c['message']} (Yazan: {c['author']})\n"
                        
                prompt_text += "\nLütfen sistemdeki sorunun ne olduğunu ve nasıl çözülebileceğini 2-3 cümleyle, teknik detaylara boğmadan Türkçe açıkla."
                
                data = json.dumps({
                    "model": self.model_name,
                    "prompt": prompt_text,
                    "stream": False
                }).encode('utf-8')
                
                req = urllib.request.Request(f"{self.host}/api/generate", data=data, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=45) as response:
                    res = json.loads(response.read().decode())
                    return "🤖 [Yapay Zeka (Ollama) Raporu]\n\n" + res.get("response", "").strip()
            except Exception as e:
                return fallback_report + f"\n\n*(Sistem yerel yapay zeka servisine (Ollama) erişemediği için Akıllı Kural Motoru kullanıldı.)*"
                
        return fallback_report

    def _rule_based_analysis(self, logs, commits_matches):
        report = "🔍 [Akıllı Kural Raporu]\nSistem logları taranarak şu eşleşmeler bulundu:\n"
        
        found_issues = []
        log_text = "\n".join(logs).lower()
        
        if "nvidia" in log_text:
            found_issues.append("- 🎮 NVIDIA Ekran Kartı sürücülerinde bir çökme veya modül (dkms) yükleme hatası yaşandı.")
        if "oom-killer" in log_text or "out of memory" in log_text:
            found_issues.append("- 💾 Bellek (RAM) doluluk eşiğini aştığı için bazı programlar sistem çekirdeği tarafından zorla kapatılmış (OOM Killer).")
        if "networkmanager" in log_text and ("fail" in log_text or "error" in log_text):
            found_issues.append("- 🌐 Ağ bağlantısı servisinde (NetworkManager) kopmalar veya yapılandırma hataları algılandı.")
        if "ext4" in log_text and "error" in log_text:
            found_issues.append("- 💽 Disk dosya sisteminde okuma/yazma blok hataları görüldü (ext4 corruption şüphesi). Live USB ile 'fsck' onarımı önerilir.")
        if "segfault" in log_text:
            found_issues.append("- 💥 Bir uygulama bellekte yetkisi olmayan bir alana erişmeye çalışıp çöktü (Segmentation Fault).")
            
        if not found_issues:
            report += "- Genel sistem hizmetlerinde bazı çökme veya uyarı kayıtları var ancak veri tabanımızdaki spesifik bir Linux kuralıyla eşleşmedi.\n"
        else:
            report += "\n".join(found_issues) + "\n"
            
        if commits_matches:
            report += "\n📦 Şüpheli Yazılım Değişiklikleri (Git İzi):\n"
            for match in commits_matches:
                c = match['commit']
                report += f"Bu hata sinyalleri, en yoğun '[{c['hash']}] {c['message']}' kod değişikliğinin/commit'in yapıldığı gün ortaya çıktı. Kaynağı bu kod güncellemesi olabilir.\n"
                
        return report

    def get_system_context(self):
        import os, subprocess
        context = [] # type: list[str]
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        context.append(f"İşletim Sistemi: {line.split('=')[1].strip().strip('\"')}")
        except:
            context.append("İşletim Sistemi: Pardus (Bilinmiyor)")
            
        try:
            kernel = subprocess.check_output(["uname", "-r"], text=True).strip()
            context.append(f"Kernel: {kernel}")
        except:
            pass
            
        de = os.environ.get("XDG_CURRENT_DESKTOP")
        if not de: de = os.environ.get("DESKTOP_SESSION", "Standart TTY/Bilinmeyen")
        context.append(f"Masaüstü Ortamı (DE): {de}")
        
        return " | ".join(context)

    def translate_to_bash(self, user_text):
        if not self.check_ollama_available():
            return "HATA: Yerel yapay zeka (Ollama) bağlantısı kurulamadı. Lütfen localhost:11434 üzerinden çalıştığından emin olun."
            
        sys_info = self.get_system_context()
        
        try:
            prompt = f"Sen bir Linux bash ustasısın. Kullanıcının makinesi şu an tam olarak bu donanımda çalışıyor: [{sys_info}].\nGUI, Paket veya Ağ aracı (VPN vb.) kurarken KESİNLİKLE kullanıcının masaüstü ortamına (KDE Plasma, GNOME, XFCE vb.) özel paketleri ve araçları seçmeye dikkat et.\n\nKullanıcının Türkçe isteğini sadece TEK SATIRLIK GÜVENLİ bir bash komutuna çevir. ASLA açıklama yapma, markdown kullanma. Sadece doğrudan komutu yaz.\n\nKullanıcı İsteği: {user_text}\nBash Komutu:"
            
            data = json.dumps({
                "model": self.model_name,
                "prompt": prompt,
                "stream": False
            }).encode('utf-8')
            
            req = urllib.request.Request(f"{self.host}/api/generate", data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as response:
                res = json.loads(response.read().decode())
                cmd = res.get("response", "").strip()
                # Clean any markdown formatting the LLM might hallucinate
                cmd = cmd.replace("```bash", "").replace("```", "").strip()
                return cmd
        except Exception as e:
            return f"HATA: Doğal dil çevirisi yapılamadı ({e})"
