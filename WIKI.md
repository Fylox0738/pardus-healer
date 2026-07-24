# 📚 Pardus Suite — Geliştirici ve Kullanıcı Wiki'si

Pardus Suite projesi, temel olarak bilgisayar donanımından sistem loglarına, servislerinden çekirdek (kernel) modüllerine kadar müdahale edebilen devasa bir entegrasyondur.
Bu doküman, projeyi GitHub'da yayınlarken hem kullanıcılara hem de kodu forklayacak geliştiricilere rehberlik etmesi için tasarlanmıştır.

---

## 🏗️ 1. Mimari Genel Bakış
Proje 3 ana koldan (üründen) oluşur:
1. **Pardus Healer (GUI):** Olası sistem arızalarını önceden tarayan ve 9 farklı modülle onaran kalkan.
2. **Pardus Doctor (GUI + NLP):** Sorun çoktan yaşandığında (çökme vb.) kullanılan olay yeri inceleme ekibi ve Doğal Dil Terminali (AI).
3. **Healer Rescue (CLI):** Kritik çöküşlerde, simsiyah ekranda tek komutla (`sudo healer-rescue`) geçmişi Geri Alan (Undo) son kale.

---

## 🛠️ 2. Modüller ve Senaryolar (Ne Zaman, Ne Yapmalı?)

### 🩺 Modül 1: Sistem Sağlık Kontrolleri (`pardus_healer/core/logic.py`)
Bu modül Pardus Healer'ın ana ekranında otomatik çalışır.

| Problem (Senaryo) | Hangi Fonksiyon Tetiklenir? | Healer Tarafından Önerilen Çözüm (Otomatik) |
|---|---|---|
| İnternet kopukluğu veya DNS hatası var. | `check_internet()` | Ağ kartı ve `NetworkManager` servisi baştan başlatılır. |
| "Failed to fetch" (Depo Listesi) hataları alınmaya başlandı. | `check_apt_health()` | `apt-get update` ve kesintili/bozuk paketler için `dpkg --configure -a` çalıştırılır. |
| "Kırık/Bozuk Paketler" (Broken packages) uyarısı alınıyor. | `check_broken_packages()` | Eksik paket bağımlılıkları `apt-get install -f -y` ile onarılır. |
| Root dizini (`/`) veya hafıza doldu. | `check_disk_space()` | APT önbelleği tamamen temizlenir (`clean`, `autoremove`). |
| Cihazda eksik sürücü/firmware var (örn: Wi-Fi bağlanmıyor). | `check_missing_firmware()` | `firmware-linux-nonfree` gibi kapalı kaynak sürücü depoları kurulur. |

### ⚙️ Modül 2: Servis ve Başlangıç Yöneticisi (`pardus_healer/ui/...`)
| Karşılaşılan Durum | Kullanıcının Yapması Gereken | Arka Plandaki Kod Çalışma Mantığı |
|---|---|---|
| Bilgisayar çok yavaş açılıyor. Boot süresi uzadı. | Healer -> **"Başlangıç Uygulamaları"** sekmesine girip gereksiz uygulamaları kapatın. | `~/.config/autostart/` altındaki `.desktop` dosyaları tespit edilir ve `X-GNOME-Autostart-enabled=false` yapılarak pasifize edilir. |
| Bluetooth servisi veya yazıcı tepki vermiyor. | Healer -> **"Servis Yöneticisi"** sekmesinden ilgili servisi (ör: `bluetooth`) bulup "Yeniden Başlat" iconuna tıklayın. | GTK üzerinden root yetkisiyle `systemctl restart <servis>` tetiklenir. |

### 🧠 Modül 3: Olay Yeri İnceleme (`pardus_doctor/core/log_reader.py`)
| Karşılaşılan Durum | Kullanıcının Yapması Gereken | Arka Plandaki Kod Çalışma Mantığı |
|---|---|---|
| Bilgisayar aniden kapandı veya kilitlendi (Kernel Panic / Out of Memory). | Bilgisayar yeniden açıldığında Pardus Doctor'u başlatıp "Logları Tara" deyin. | Program `journalctl -p 0..3 -b -1` komutu ile bir önceki çökme loglarını çeker ve yapay zekaya yorumlatır. |
| Yaptığınız bir kod veya Git commit'i sonrasında uygulama ardışık hatalar ("segfault") vermeye başladı. | Doctor penceresinde sol üstteki "Git Repo" yoluna kendi projenizi yazın ve taratın. | `dmesg` ve `syslog` çıktıları ile sizin Github commit tarihinizi üst üste koyarak hangi kodun sistemi bozduğunu eşleştirir. |

### 🤖 Modül 4: Pardus Copilot NLP (`pardus_doctor/core/ai_engine.py`)
Yapay zeka (Copilot), işletim sisteminizin masaüstü arayüzünü karıştırmaz. Arka planda `get_system_context()` sayesinde Kernel, İşletim Sistemi ve Masaüstü Ortamı (KDE, XFCE, GNOME) bilgilerinizi okuyup AI Prompt'una gizlice ekler. Ainsi KDE kullanan birine GNOME paketleri yüklemez!

| Ne İstiyorsunuz? (Kullanıcı Cümlesi) | Ollama AI Tarafından Çevrilen Bash Komutu |
|---|---|
| *"Lütfen dışarıdan gelen 22 portuna erişimi kapa"* | `sudo ufw deny 22/tcp` |
| *"Chrome tarayıcıyı zorla kapat"* | `killall -9 chrome` veya `pkill chrome` |

### 💀 Modül 5: Siyah Ekran Kurtarması (`healer_rescue.py`)
**En kritik kriz (Disaster) senaryosudur.** Arayüz (GTK/GNOME) çökerse kullanılır.

| Kriz Senaryosu | Ne Yapılmalı? | Arka Plandaki Kod / Çözüm Algoritması |
|---|---|---|
| Nvidia Sürücüsü (veya çekirdek) güncellediniz. Bilgisayarı yeniden başlattığınızda arayüz gelmiyor, sadece siyah ekranda (TTY) yazıp yanıp sönen bir imleç var! | Ekrandayken doğrudan `sudo healer-rescue` yazıp Enter'a basın. Karşınıza Terminal Zaman Makinesi çıkacak. | `/var/log/apt/history.log` dosyası Python tarafından reverse parsing (ters işlem) ile okunur. Yüklemeler (`install`), silme komutuna (`remove`) çevrilerek size liste sunulur. |
| Ekranda son yüklediğiniz (sistemi çökerten) hatalı paketi gördünüz ve ID numarasını (Örn: 1) seçtiniz. | Seçip onaylayın. Sistem o sürücüyü silecek. Sonra `sudo reboot` atın. | Komut terminalde onaylanarak çalıştırılır ve sistem eski temiz haline (rollback) döner. Arayüzünüz geri gelir! |

---

## 🚨 Sıkça Sorulan Sorular (SSS - Troubleshooting)

**S: Doctor çalışıyor ancak Yapay Zeka Raporu yerine "Akıllı Kural Motoru Raporu" veriyor? Neden?**
C: Program, bilgisayarınızda yerel Ollama AI (`localhost:11434`) kurulu olmadığını tespit ederek "Offline Fallback" (internetsiz ağ bağlantısız statik yedek plan) moduna geçer. Full yapay zeka deneyimi (NLP) için `curl -fsSL https://ollama.com/install.sh | sh` komutuyla Ollama kurmanız gerekir.

**S: Zaman Makinesi sekmesinde "Geçmiş Bulunamadı" diyor?**
C: Sistem çok taze kurulmuş olabilir ya da `/var/log/apt/history.log` dosyası sistem tarafından silinmiş olabilir.

**S: Healer "Tümünü Onar" butonuna basınca bazı onarımlar başarısız uyarısı veriyor?**
C: `dpkg` sistemi kilitli (lock) kalmış olabilir. Arka planda başka bir paket yöneticisi (örneğin Pardus Mağaza veya terminalde `apt upgrade`) açıkken Healer'da düzelt tuşuna basarsanız güvenlik gereği kilitlenir. Diğerlerini kapatıp tekrar deneyin.

**S: Sistem güvenliği sekmesinde Güvenlik Duvarı (Firewall) devredışı görünüyor?**
C: UFW (Uncomplicated Firewall) Pardus'ta varsayılan yüklü gelse de enerjisi kesiktir (pasiftir). Bunu tespit etmesi zaten sistemin doğru çalıştığını gösterir!

---

## 👨‍💻 Geliştiriciler İçin Extensibility (Yeni Özellik Ekleme Rehberi)

Kodu fork'ladıktan sonra yeni bir modül (örneğin VPN Kontrolcüsü) eklemek inanılmaz kolaydır! Tüm mimari **Modüler Kart** sistemine dayanır.

`pardus_healer/core/logic.py` dizinine gidip özelliğinizi yazın:
```python
def check_vpn_durumu(self):
    # Kendi tespit mantığını buraya yaz
    if vpn_kapali_ise:
        return False # Kırmızı kart uyarısı
    return True # Yeşil kart
```

Sonra bu mantığı `pardus_healer/app.py` içerisindeki `self._create_cards()` listesinin en altına tek bir satır olarak ekleyin:
```python
("🔒", "VPN Kontrolü", "Gizlilik denetleniyor...", self.logic.check_vpn_durumu, "sudo openvpn --start", "VPN Aç")
```
Herhangi bir ekstra buton, frame, CSS veya GTK3 UI kodu yazmanıza gerek yoktur! Healer, o satırı okur okumaz arayüze animasyonlu, pırıl pırıl yeni bir kart tasarlayıp otonom olarak sisteme bağlar.

**Dünyanın en otonom ve kullanıcı dostu Pardus Ekosistemini inşa etmeye (veya katkıda bulunmaya) hoş geldiniz!**
