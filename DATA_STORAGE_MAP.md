# Veri Depolama Haritası

> Proje bir SQL veritabanı **kullanmaz**. Tüm kalıcı durum, kullanıcının kendi `$HOME` dizini altında düz JSON/JSONL dosyaları olarak tutulur. Mimari genel bakış için [[ARCHITECTURE_MAP.md]].

## Kalıcı dosyalar

| Yol | Yazan modül | İçerik | Notlar |
|---|---|---|---|
| `~/.config/pardus-healer/settings.json` | `pardus_healer/config.py` | `dark_mode`, `auto_interval_min`, `first_run`, `advisor_mode`, `ollama_model`, `swarm_token` | Dizin `0o700`, dosya `0o600` ile korunur (`swarm_token` hassas — ağ içi filo kimlik doğrulaması). Şifrelenmez; düz metin JSON. Okuma/yazma hatası **sessizce yutulur**. |
| `~/.config/pardus-healer/history.json` | `pardus_healer/core/history.py` | Son 60 taramanın `timestamp, score, grade, fail, warn, ok` özeti | Dashboard trend grafiğinin veri kaynağı. Sabit boyutlu (60 kayıt) — daha eski geçmiş sessizce silinir. |
| `~/.local/share/pardus-healer/pulse.jsonl` | `pardus_healer/core/pulse.py` | Her satır bir SOS olayı: `{ts, issue, region}` | **Opt-in** olmalı (kullanıcı onayıyla `record_event()` çağrılır). ⚠️ `seed_demo_data()` da AYNI dosyaya uydurma satırlar yazar — gerçek/demo veri dosya seviyesinde ayrılmıyor. Bkz.. |
| `/var/log/apt/history.log` | (yazan: `apt`, sistem) | APT işlem geçmişi | Yalnızca **okunur** — `healer_rescue.py` bunu ters parse ederek rollback listesi çıkarır. Healer bu dosyaya yazmaz. |
| `journalctl` (systemd log) | (yazan: systemd) | Sistem/çökme logları | Yalnızca **okunur** — `pardus_doctor/core/log_reader.py` tarafından `journalctl -p 0..3 -b -1` ile sorgulanır, diske ayrıca kaydedilmez. |
| HTML/JSON rapor çıktıları | `pardus_healer/report/*.py` | Tam `DiagnosisReport` dökümü | Varsayılan bir konuma yazılmaz — yalnızca kullanıcı `--html`/`--json` ile CLI'de hedef yol verdiğinde üretilir. |

## Ağ üzerinden veri

| Kanal | Modül | Notlar |
|---|---|---|
| Swarm (yerel ağ) | `pardus_healer/swarm/{server,client,auth}.py` | Diğer Healer örnekleriyle ağ içi iletişim; `config.swarm_token` ile "Zero-Trust" iddia edilen kimlik doğrulama — gerçek güvenlik seviyesi için'ye bakın. |
| Ollama (`localhost:11434`) | `pardus_doctor/core/ai_engine.py`, `pardus_healer/core/advisor.py` | Yalnızca **yerel** loopback; dışarıya veri göndermez. |
| Bulut / uzak sunucu | — | **Yok.** Proje tasarım gereği hiçbir veriyi bir buluta göndermez; bu README'de de vurgulanan bir satış noktasıdır. |

## Gizlilik/güvenlik notları

- Hiçbir dosya şifrelenmiyor; tehdit modeli "aynı makineye fiziksel/hesap erişimi olan biri" değilse yeterli.
- `swarm_token`, dosya izinleriyle (`0o600`) korunuyor ama düz metin — disk şifrelemesi yoksa yedeklerde/imajlarda sızabilir.
- `pulse.jsonl` "kişisel veri içermez" diye belgelenmiş (yalnızca sorun başlığı + serbest metin bölge) ama serbest metin alanı kullanıcı tarafından doldurulduğu için kötüye kullanım/kişisel veri girme riski teknik olarak engellenmemiş.
