# 🩺 Pardus Healer

**Akıllı sistem tanılama ve iyileştirme aracı** — Pardus / Debian tabanlı
sistemler için.

Pardus Healer, bilgisayarınızı tarar, sorunları tespit eder, **sorunların
kök nedenini** bulur, önceliklendirir ve tek tıkla çözüm sunar. İnternet
gerektirmeyen, cihazda çalışan bir **kural tabanlı teşhis motoru** kullanır.

---

## ✨ Öne Çıkan Özellikler

| Özellik | Açıklama |
|--------|----------|
| 🧠 **Akıllı Teşhis Motoru** | Tekil sonuçlara değil, aralarındaki neden-sonuç ilişkisine bakar. Örn: "Disk dolu olduğu için APT başarısız oluyor" — asıl çözülmesi gerekeni söyler. |
| 📊 **Sağlık Skoru (0–100)** | Sistemin genel sağlığını ağırlıklı bir skor ve harf notu (A–F) ile özetleyen görsel dashboard. |
| 📈 **Geçmiş & Trend** | Her tarama kaydedilir; skorun zaman içindeki değişimi cairo grafikle gösterilir. |
| ⚡ **Paralel Tarama** | Kontroller aynı anda çalışır; tam tanı saniyeler yerine milisaniyeler sürer. |
| 🖥️ **CLI Modu** | `--cli` ile arayüzsüz tanı; sunucular ve otomasyon için renkli terminal çıktısı. |
| ⚡ **Önceliklendirilmiş İçgörüler** | Ne önce yapılmalı? Güvenlik yamaları, kök nedenler ve riskler önem sırasına göre listelenir. |
| 🔧 **Tek Tıkla Onarım** | Her sorun için güvenli, hazır `pkexec` komutları. Çıktı canlı terminalde akar. |
| 🛡️ **19 Kontrol** | Ağ, DNS, APT, bozuk paketler, güvenlik güncellemeleri, disk, RAM, swap, CPU yükü/sıcaklığı, pil sağlığı, systemd servisleri, güvenlik duvarı, açık portlar, SSH güvenliği, otomatik güncelleme, günlük hataları... |
| 📄 **HTML + JSON Rapor** | Yazdırılabilir/PDF'lenebilir şık HTML; otomasyon için makine-okur JSON. |
| 🔔 **Masaüstü Bildirimi** | Kritik sorunlarda `notify-send` ile uyarı. |
| 🌙 **Koyu/Açık Tema + Otomatik Kontrol** | Ayarlar kalıcı saklanır; belirlenen aralıkta otomatik tarama. |
| 🔌 **İnternetsiz Çalışır** | Teşhis motoru yalnızca yerel sistem bilgisini kullanır; buluta veri göndermez. |

---

## 🏗️ Mimari

Proje modüler bir Python paketidir. Çekirdek mantık GTK'dan **tamamen
bağımsızdır**, bu sayede tek başına test edilebilir:

```
pardus_healer/
├── core/            # GTK'sız saf çekirdek
│   ├── models.py    # Status, CheckResult, Fix, Insight, DiagnosisReport
│   ├── check.py     # BaseCheck — yeni kontrol yazmanın temeli
│   ├── shell.py     # güvenli komut çalıştırma
│   ├── engine.py    # tanı motoru + sağlık skoru (paralel)
│   ├── rules.py     # ⭐ kural (korelasyon) motoru — "akıllı" çekirdek
│   ├── history.py   # skor geçmişi / trend
│   ├── sysinfo.py   # sistem kimlik bilgileri
│   └── notify.py    # masaüstü bildirimleri
├── checks/          # tekil tanı modülleri (kolayca genişletilebilir)
│   ├── network.py  apt.py  packages.py  updates.py
│   ├── disk.py  memory.py  cpu.py  hardware.py
│   └── services.py  security.py  security_extra.py  logs.py
├── report/          # HTML + JSON + metin rapor üreticileri
├── cli.py           # komut satırı arayüzü
└── ui/              # GTK3 arayüz (dashboard, kartlar, ayarlar)
```

### Yeni bir kontrol eklemek ne kadar kolay?

```python
from ..core.check import BaseCheck

class MyCheck(BaseCheck):
    id = "my_check"
    title = "Benim Kontrolüm"
    icon = "🔎"
    category = "Sistem"

    def run(self):
        if some_problem:
            return self.fail("Sorun var!", recommendation="Şunu yapın...")
        return self.ok("Her şey yolunda.")
```

Sınıfı `checks/__init__.py` içindeki listeye eklemek onu dashboard'a,
skora ve rapora otomatik dahil eder.

---

## 🚀 Kurulum ve Çalıştırma

Pardus / Debian / Ubuntu üzerinde:

```bash
# Bağımlılıklar (yalnızca GTK — ek Python paketi gerekmez)
sudo apt-get install python3-gi gir1.2-gtk-3.0

# İsteğe bağlı (daha zengin bilgi)
sudo apt-get install lm-sensors ufw

# Grafik arayüz
python3 run.py

# Komut satırı (arayüzsüz) tanı
python3 run.py --cli
python3 run.py --cli --html rapor.html --json rapor.json
python3 run.py --cli --quiet          # yalnızca skor (betikler için)
```

---

## 🧪 Test

Çekirdek mantık GTK gerektirmediği için herhangi bir makinede test edilebilir:

```bash
python3 -c "from pardus_healer.core.engine import DiagnosisEngine; \
            r=DiagnosisEngine().run_all(); \
            print('Skor:', r.health_score, r.grade)"
```

---

## 📌 Yol Haritası

- [ ] Geçmiş takibi (skorun zaman içindeki değişimi)
- [ ] Daha fazla güvenlik kontrolü (açık portlar, başarısız girişler)
- [ ] Sürücü / donanım uyumluluk taraması
- [ ] Çoklu dil desteği (i18n)

---

*Pardus Healer — sisteminizi anlayan, sadece rapor etmeyen bir araç.*
