# Ekran / Modül Haritası

> Kod dosyası ↔ kullanıcının gördüğü ekran/bileşen eşlemesi. Mimari genel bakış için [[ARCHITECTURE_MAP.md]].

## Pardus Healer arayüzü (`pardus_healer/ui/`)

| Dosya | Satır | Ekran/Bileşen | Sorumluluk |
|---|---|---|---|
| `main_entry.py` | 24 | — (giriş noktası) | GTK uygulamasını başlatır, `app.py`'yi ayağa kaldırır |
| `splash.py` | 64 | Açılış ekranı | Uygulama yüklenirken gösterilen splash |
| `welcome.py` | 131 | İlk açılış tanıtım turu | Teknik olmayan kullanıcı (öğretmen/okul) için adım adım anlatım — `config.first_run` bayrağıyla tetiklenir |
| `app.py` | 558 | Ana pencere kabuğu | En büyük dosya; sidebar, sayfa geçişleri, genel pencere durumu |
| `dashboard.py` | 245 | Ana panel | Sağlık skoru göstergesi, canlı CPU/RAM/Disk çubukları (`core/live.py`'yi tüketir), skor trend grafiği (`core/history.py`) |
| `checks_page.py` | 118 | Kontroller sekmesi | Tüm `CheckResult` kartlarının listesi |
| `card.py` | 213 | Kontrol kartı (bileşen) | Tek bir `CheckResult`'ı gösteren, tıklanınca genişleyen animasyonlu kart |
| `fix_runner.py` | — (yardımcı) | Onarım komutu çalıştırma | `card.py` ve `app.py`'nin iki worker'ı arasında paylaşılan ortak `run_fix_command()` — eskiden üç yerde kopyalıydı |
| `settings_page.py` | 150 | Ayarlar sekmesi | Koyu/açık tema, otomatik tarama aralığı, danışman modu (kural/Ollama) |
| `sos_dialog.py` | 150 | "SOS Kartı" diyaloğu | `core/bug_report.py` çıktısını gösterir; okul/İl-İlçe BT formatör öğretmenine gönderilecek metni üretir |
| `pulse_dialog.py` | 101 | "Pardus Nabız" diyaloğu | `core/pulse.py` üzerinden birikmiş SOS olaylarının toplu görünümü; demo verisi ayrı dosyada tutulur ve "DEMO" etiketiyle gösterilir |
| `swarm_page.py` | 186 | Filo (Swarm) sekmesi | Ağdaki diğer Healer örnekleriyle bağlantı/durum listesi |
| `tray.py` | 91 | Sistem tepsisi | Arka planda çalışırken tepsi ikonu + hızlı menü |
| `theme.py` | 205 | — (stil) | CSS string'leri, renk paleti, koyu/açık tema tanımları |
| `widgets.py` | 241 | — (ortak bileşenler) | Kartlar/sayfalar arasında paylaşılan GTK widget yardımcıları |

## Pardus Doctor arayüzü (`pardus_doctor/ui/`)

| Dosya | Satır | Ekran/Bileşen | Sorumluluk |
|---|---|---|---|
| `app.py` | 252 | Tek pencere | Sol: Git repo yolu + log tarama; Sağ: `ai_engine.py` üzerinden doğal dil → bash komut terminali |

## Healer Rescue (`healer_rescue.py`)

TTY tabanlı metin arayüzü (GTK yok). "Zaman Makinesi" ekranı: `/var/log/apt/history.log`'dan çıkarılan işlem listesini numaralandırıp kullanıcıya sunar, seçileni geri alır.

## Masaüstü/sistem giriş noktaları

| Dosya | Tetiklenme |
|---|---|
| `pardus-healer.desktop` | Uygulama menüsünden "Pardus Healer" |
| `pardus-doctor.desktop` | Uygulama menüsünden "Pardus Doctor" |
| `pardus-healer-tray.desktop` | Oturum açılışında otomatik (autostart) |
| `pardus-healer-daemon.service` | systemd, arka plan otonom tarama |
| `pardus-healer-swarm.service` | systemd, filo dinleyicisi |
| `sudo healer-rescue` | Elle, TTY'den (GUI çökünce) |
