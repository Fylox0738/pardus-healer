# Mimari Haritası

> Bu doküman Pardus Healer suit'inin genel mimarisini tanımlar. Tekil dosya/ekran envanteri için [[MODULE_MAP.md]], kalıcı veri için [[DATA_STORAGE_MAP.md]] dosyasına bakın.

## Üç ürün, tek repo

```
pardus-healer/
├── pardus_healer/     ── Ürün 1: proaktif tarama + onarım (GTK3 + CLI)
├── pardus_doctor/      ── Ürün 2: reaktif olay yeri incelemesi (GTK3 + NLP)
├── healer_rescue.py    ── Ürün 3: TTY kurtarma CLI (bağımsız tek dosya)
├── main.py / run.py / main_doctor.py  ── ürünlerin başlatıcı script'leri
└── debian/, *.desktop, *.service, *.policy  ── sistem paketleme/entegrasyon
```

## Ürün 1: Pardus Healer (`pardus_healer/`)

Katmanlı, GTK-bağımsız çekirdek üzerine kurulu klasik bir "engine + checks + ui" mimarisi:

```
pardus_healer/
├── core/                  # GTK'sız saf mantık — tek başına test edilebilir
│   ├── models.py          #   Status / Fix / Metric / CheckResult / Insight / DiagnosisReport (dataclass'lar)
│   ├── check.py           #   BaseCheck — her kontrolün türediği taban sınıf
│   ├── registry.py        #   checks/ paketindeki tüm sınıfları toplar (lazy import, döngüsel bağımlılığı önler)
│   ├── engine.py          #   DiagnosisEngine — kontrolleri PARALEL çalıştırır, health_score hesaplar
│   ├── rules.py           #   ⭐ korelasyon motoru — çoklu CheckResult'tan Insight (kök neden) üretir
│   ├── shell.py           #   subprocess sarmalayıcı — pkexec yükseltme, shell=True KULLANILMAZ
│   ├── history.py         #   skor geçmişi (bkz. DATA_STORAGE_MAP)
│   ├── sysinfo.py         #   sistem kimlik bilgisi (dağıtım, çekirdek, masaüstü ortamı)
│   ├── notify.py          #   notify-send masaüstü bildirimi
│   ├── advisor.py         #   çift modlu özet: kural tabanlı metin ÜRETİCİ | Ollama'ya devreden köprü
│   ├── live.py             #   canlı CPU/RAM/Disk örnekleme (dashboard mini görev yöneticisi)
│   ├── pulse.py           #   "Pardus Nabız" — yerel/opt-in SOS olay birikimi (demo verisi ayrı dosyada tutulur)
│   └── bug_report.py      #   "SOS Kartı" — DiagnosisReport'u talep-formu şablonuna çevirir
├── checks/                # tekil tanı modülleri — her biri BaseCheck alt sınıfı
│   ├── network.py  apt.py  packages.py  updates.py
│   ├── disk.py  memory.py  cpu.py  hardware.py  boot.py  maintenance.py
│   ├── services.py  security.py  security_extra.py  logs.py
│   └── bootloader.py  esignature.py  printer.py  # Pardus'a özgü kontroller
│   └── __init__.py        #   ALL_CHECK_CLASSES — yeni kontrol eklemenin tek adımı
├── report/                # DiagnosisReport → çıktı formatları
│   ├── html_report.py  json_report.py  text_report.py
├── swarm/                 # ağ içi filo (fleet) yönetimi — "Zero-Trust" iddia edilen katman
│   ├── auth.py  client.py  server.py
├── daemon.py              # arka planda otonom/periyodik tarama süreci (systemd servisi ile çalışır)
├── config.py              # ayarlar (bkz. DATA_STORAGE_MAP)
├── cli.py                 # --cli modu; engine'i doğrudan kullanır (GUI ile aynı motor)
├── entry.py               # argv'ye göre cli.py veya ui/main_entry.py'ye yönlendirir
└── ui/                    # GTK3 arayüz — bkz. MODULE_MAP.md
```

**Veri akışı (bir tarama turu):**
`entry.py` → `cli.py` veya `ui/main_entry.py` → `core/engine.py:DiagnosisEngine.run_all()` → `registry.py` üzerinden `checks/*` sınıfları paralel çalışır → her biri bir `CheckResult` döndürür → `core/rules.py` sonuçları ilişkilendirip `Insight` (kök neden) üretir → toplam `health_score`/`grade` hesaplanır → `DiagnosisReport` döner → GUI'de `ui/dashboard.py` + `ui/card.py` ile gösterilir, CLI'de `report/text_report.py` ile yazdırılır, isteğe bağlı `report/html_report.py` / `json_report.py` dosyaya yazılır, `core/history.py` skor kaydını ekler.

**Onarım akışı:** Bir `CheckResult.fix` (bir `Fix` nesnesi) varsa, kullanıcı "Onar" butonuna basar → `core/shell.py` komutu `needs_root` ise `pkexec` ile yükseltir → çıktı canlı terminale akar.

## Ürün 2: Pardus Doctor (`pardus_doctor/`)

Daha küçük, reaktif bir araç:

```
pardus_doctor/
├── core/
│   ├── log_reader.py      # journalctl -p 0..3 -b -1 (önceki çökme logları)
│   ├── ai_engine.py        # Ollama entegrasyonu + get_system_context() (dağıtım/DE farkındalığı)
│   ├── git_analyzer.py     # kullanıcı repo'sunun commit geçmişini çökme zamanıyla eşleştirir
│   └── safety.py           # AI'nin ürettiği komutları çalıştırmadan önce güvenlik kontrolü
└── ui/app.py               # tek pencereli GTK arayüz (log analizi + doğal dil terminali)
```

`main_doctor.py` bu ürünün başlatıcısıdır; `pardus_healer` ile kod paylaşımı **yoktur** (ayrı bir GTK uygulaması).

## Ürün 3: Healer Rescue (`healer_rescue.py`)

Tek dosyalık, bağımsız CLI. GTK'ya bağımlı değildir — GUI çökmüşse TTY'den `sudo healer-rescue` ile çalışır. `/var/log/apt/history.log` dosyasını ters (reverse) parse ederek son `install` işlemlerini `remove` komutlarına çevirir ve kullanıcıya onaylatıp uygular.

## Sistem entegrasyonu

| Dosya | Amaç |
|---|---|
| `org.pardus.healer.policy` | Polkit — hangi eylemlerin `pkexec` ile hangi yetki seviyesinde (auth_admin/yes) çalışacağını tanımlar |
| `pardus-healer-daemon.service` | `daemon.py`'yi arka planda otonom tarama için systemd üzerinden ayakta tutar |
| `pardus-healer-swarm.service` | `swarm/server.py`'yi ayakta tutar (ağ içi filo dinleyicisi) |
| `pardus-healer-tray.desktop` | `ui/tray.py`'yi oturum açılışında otomatik başlatır (autostart) |
| `pardus-healer.desktop` / `pardus-doctor.desktop` | uygulama menüsü girişleri |
| `debian/`, `Makefile`, `install.sh` | `.deb` paketleme ve manuel kurulum yolu |

## Bilinçli mimari kısıtlar

- Çekirdek motor **internet gerektirmez** ve **hiçbir buluta veri göndermez** — bu bir özellik, kısıt değil (okul/kamu kullanım senaryosu).
- Ek pip bağımlılığı yok; yalnızca `apt` ile kurulabilen paketlere güvenilir.
- `core/` ↔ `ui/` ayrımı kesindir; bu ayrımı bozan bir katkı (örn. `core/` içine `Gtk` import etmek) mimariyi ihlal eder.
