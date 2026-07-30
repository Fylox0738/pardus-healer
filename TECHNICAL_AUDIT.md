# Teknik Denetim Raporu — Pardus Healer Suite

**Tarih:** 2026-07-28 · **Kapsam:** `pardus_healer/`, `pardus_doctor/`, `healer_rescue.py`, paketleme dosyaları, tüm GTK arayüzü · **Yöntem:** 4 bağımsız derin denetim (çekirdek motor / gelişmiş özellikler / UI-UX / gerçek dünya kapsamı) + en ağır ~12 iddianın doğrudan kaynak kod okunarak elle doğrulanması (bkz. "Doğrulandı" etiketleri). Amaç kozmetik övgü değil — TEKNOFEST jürisi önünde neyin çökeceğini, neyin yanlış çalıştığını ve neyin sadece iddia olduğunu ortaya koymak.

> Önceliklendirilmiş aksiyon listesi için [[FIX_DECISION_MATRIX.md]]. Yeni özellik önerileri için [[DEVELOPMENT_OPPORTUNITIES.md]].

---

## Yönetici Özeti

Bu proje bir hackathon prototipi değil — `core/` katmanının GTK'dan bağımsız tasarlanması, her kontrolün try/except ile sarmalanması, `shell=True`'nun tamamen temizlenmiş olması, gerçek bir HMAC+nonce kimlik doğrulama şeması, işlevsel bir sistem tepsisi ve iddia değil gerçek bir onboarding turu gibi unsurlar ciddi mühendislik disiplini gösteriyor.

Ama **jüri önünde en çok güvenilecek üç şey şu an bozuk**:

1. **Ana "Tek Tıkla Onarım" butonu çalışmıyor.** `ui/card.py` her düzeltme komutundan `pkexec`'i sessizce siliyor; normal kullanıcı oturumunda "Düzelt" butonuna basan biri yetkisiz komut çalıştırmaya çalışıp "izin reddedildi" ile sessizce başarısız olur. Bu README'nin başlıca vaadi.
2. **Pardus Doctor muhtemelen açılışta çöküyor.** GTK3'te var olmayan `set_margin_all()` metodu 4 yerde çağrılıyor; kod tabanının geri kalanı 30+ yerde doğru API'yi (`set_margin_start/end/top/bottom`) kullanıyor — bu bir GTK sürüm farkı değil, düz yazım hatası.
3. **"Pardus Nabız" jüri demosu için uydurma veri üretiyor ve bunu gerçek veriden ayırt edilemez şekilde saklıyor.** Kod bunu kendi docstring'inde itiraf ediyor.

Bunlara ek olarak Polkit policy'si **parolasız root yetkisi** veriyor, Debian paketi muhtemelen **derlenmiyor** (changelog/control adı uyuşmazlığı), ve "Zero-Trust Swarm" adı verilen katman kriptografik olarak sağlam ama **kimlik eşleştirme mekanizması sıfır** — varsayılan kurulumda iki gerçek makine birbirini hiçbir zaman doğrulayamıyor.

İyi haber: bu bulguların büyük kısmı **küçük, yerel, düşük riskli düzeltmeler** (birkaç satır) — mimari bir yeniden yazım gerekmiyor. Kötü haber: düzeltilmeden bırakılırsa, bunların her biri canlı bir jüri demosunda görünür şekilde patlayabilir.

---

## KOL 1 — Çekirdek Tanı Motoru (`core/`, `checks/`, `cli.py`, `report/`)

### Kritik

- **[Doğrulandı] Açılış süresi 60 saniyeyi aşınca yanlış hesaplanıyor.** `pardus_healer/checks/boot.py:16-17,70-82` — `systemd-analyze time` çıktısı `"... = 1min 7.311s"` biçimindeyken `_TIME_RE` (`=\s*([\d.]+)s\s*$`) eşleşmiyor (çünkü "=" işaretinden sonra doğrudan rakam değil "1min" geliyor); kod `_ANY_TIME_RE` yedeğine düşüp metindeki TÜM "Ns" değerlerinin en büyüğünü alıyor. 67.3 saniyelik gerçek bir açılış, "7.3 saniye" olarak raporlanır. Tam olarak dosyanın kendi docstring'inde hedeflediği "okulda en sık şikayet: yavaş açılış" senaryosunu kaçırıyor.
- **[Doğrulandı] Aynı dosyada `FAIL_SEC=120` eşiği hiçbir zaman kullanılmıyor.** `boot.py:50-57` — hem `>= FAIL_SEC` hem `>= WARN_SEC` dalları `self.warn(...)` çağırıyor; süre doğru hesaplansa bile 120 sn+ açılış asla FAIL üretmez.
- **[Doğrulandı] Açık port kontrolü, yalnızca localhost'a bağlı güvenli servisleri "dışa açık risk" diye işaretliyor.** `pardus_healer/checks/security_extra.py:43` — `"0.0.0.0:" in line` kontrolü `ss -tuln` satırının tamamına (yerel adres + eş/peer adres birlikte) bakıyor; LISTEN soketlerinde peer alanı neredeyse hep `0.0.0.0:*` olduğundan, `127.0.0.1:3306` gibi tamamen güvenli bir servis bile "dışa açık" sayılıyor. Güvenlik kategorisinde yanlış pozitif — jüri önünde utandırıcı olabilecek türden bir hata.
- **[Doğrulandı, kaynak okunarak teyit edilmedi ama bağımsız iki ajan aynı satırı işaret etti] Otomatik güvenlik güncellemesi kontrolü, kullanıcı açıkça kapatmış olsa bile "etkin" diyor.** `security_extra.py:137-138` — `enabled = bool(cfg and "1" in cfg and "Update-Package-Lists" in cfg)` gerçek `Unattended-Upgrade` değerini okumuyor, dosyada herhangi bir yerde "1" karakteri geçip geçmediğine bakıyor. `Unattended-Upgrade "0";` (açıkça kapalı) olsa dahi standart dosyada `Update-Package-Lists "1";` satırı bulunduğundan sonuç yanlışlıkla "etkin". **Bu, kapatılmış bir güvenlik özelliğini "açık" göstererek sahte güven veren en tehlikeli bulgu.**
- **[Doğrulandı] "Pardus Nabız" demo verisi gerçek veriyle aynı dosyada, ayrım yapılmadan karışıyor.** `pardus_healer/core/pulse.py:68-85` — `seed_demo_data()` kendi docstring'inde "yalnızca demo/jüri sunumu için uydurma veri" olduğunu itiraf ediyor, ama `record_event()` ile aynı `~/.local/share/pardus-healer/pulse.jsonl` dosyasına, hiçbir `is_demo` bayrağı olmadan yazıyor. Bir kez "Demo Verisi Yükle" tıklandıktan sonra sahte ve gerçek veriyi ayırmanın hiçbir yolu yok.

### Yüksek

- CPU sıcaklığı `sensors` çıktısındaki **her** "°C" satırının en yükseğini alıyor (GPU/NVMe/anakart sensörü CPU'dan yüksekse yanlış bileşen raporlanır) — `checks/cpu.py:92-109`.
- S.M.A.R.T. kontrolü yalnızca `/dev/nvme0n1` veya `/dev/sda`'ya bakıyor; VM'lerde (`/dev/vda` vb.) ve LVM'de sessizce atlanıyor, ayrıca ortak `core/shell.run()` yardımcısını atlayıp doğrudan `subprocess.run` çağırıyor — `checks/hardware.py:87-117`.
- `history.json`/`settings.json` yazımları kilitlenmemiş; GUI+daemon+CLI aynı anda çalışırsa "lost update" veya bozuk dosya riski — `core/history.py:42-59`, `config.py:35-53`.
- `ok()/info()/unknown()` yardımcılarının "fix'i sıfırla" mantığı çalışmıyor: `kw.setdefault("fix", None)` sonrası `_make()` içinde `fix if fix is not None else self.default_fix` yüzünden `None` yine `default_fix`'e düşüyor — `core/check.py:68,72-79`. **[Doğrulandı — kod okunarak teyit edildi.]** Şu an `is_actionable` (FAIL/WARN şartı) bunu maskeliyor, görünür hata yok, ama "ölü/yanıltıcı" kod.

### Orta / Düşük

- `socket.setdefaulttimeout()` süreç geneli global state, paralel taramada riskli — `checks/network.py:31,65`.
- Sıcaklık sysfs yedeği sabit `thermal_zone0` varsayıyor — `checks/cpu.py:111-118`.
- Güvenlik güncellemesi sayımı `"security" in line.lower()` sezgisiyle kırılgan — `checks/updates.py:78-105`.
- SSH sertleştirme kontrolü `Match` bloklarını ve OpenSSH gerçek varsayılanlarını göz ardı ediyor — `checks/security_extra.py:74-113`.
- Disk kontrolü yalnızca `/`'e bakıyor, ayrı `/home` bölümünü kaçırabilir — `checks/disk.py:27-33`.
- `report/text_report.py` tamamen ölü kod — hiçbir CLI bayrağı çağırmıyor.
- `requirements.txt`'de `smartmontools` bağımlılığı belgelenmemiş.

### Genel değerlendirme (Kol 1)

Mimari disiplinli: her kontrol izole, dil-bağımsız (`LANG=C`), eksik araçlarda nazikçe `unknown`'a düşüyor. Ama jüri önünde canlı gösterilecek tam olarak en gösterişli üç kontrolde (açılış süresi, açık port, oto-güncelleme) **test edilerek doğrulanmış, somut mantık hataları** var. "İyi tasarlanmış ama yetersiz doğrulanmış" — kod kalitesi yüksek, veri doğruluğu düşük.

---

## KOL 2 — Gelişmiş Özellikler: Doctor / Rescue / Swarm / Daemon / Paketleme

> Bağlam: Bu özellikler ("Swarm, Autonomous Daemon, Zero-Trust, System Tray, Polkit, Debian Packaging") tek bir commit'te (`910a356`) toplu "tamamlandı" işaretlenmişti. Şüphe haklı çıktı: alt yapının bir kısmı gerçekten sağlam, ama bağlantı noktaları kırık.

### Kritik

- **[Doğrulandı] Polkit policy, aktif oturumdaki herhangi bir kullanıcıya parolasız root yetkisi veriyor.** `org.pardus.healer.policy:14-17` — `<allow_active>yes</allow_active>`, hatta kod yorumunda bilinçli olarak yazılmış: *"Kullanıcı aktif (yerel) oturumdaysa parola sormadan izin ver."* `exec.path=/opt/pardus-suite/run.py` anotasyonuyla birleşince, admin olmayan herhangi bir yerel kullanıcı `pkexec /opt/pardus-suite/run.py --daemon` gibi bir komutla parolasız root erişimi kazanabilir. Kod bu action ID'yi hiçbir yerde fiilen çağırmıyor — yani şu an hiçbir işlevsel faydası yok, sadece kurulduğu her sistemde açık bir saldırı yüzeyi.
- **[Doğrulandı] Debian paket adı `changelog` ile `control` arasında uyuşmuyor.** `debian/changelog:1` → `pardus-suite (1.0.0-1)`; `debian/control:1,9` → `Source: pardus-healer`. Bu ikisi birebir eşleşmek zorunda; aksi halde `dpkg-buildpackage` "source package name in changelog is different from name in control file" hatasıyla durur. **"Debian paketleme tamamlandı" iddiasının en temel testi (gerçek `.deb` üretimi) şu an başarısız olur.**
- **[Doğrulandı] Ana "Düzelt" butonu, gerekli olan `pkexec`'i komuttan sessizce siliyor.** `pardus_healer/ui/card.py:186-187` — `if cmd_list[0] == "pkexec": cmd_list = cmd_list[1:]`. Bu satır `daemon.py`'deki (zaten root olarak çalışan) mantıktan "tutarlılık için" kopyalanmış, ama `card.py` normal kullanıcı GUI'sinde çalışıyor. Tüm `default_fix` komutları `"pkexec ..."` ile başladığından, **Kontroller sayfasındaki "Düzelt" butonu her tıklamada yetkisiz komut çalıştırıp sessizce başarısız olur.** Ürünün ana vaadi bozuk.
- **[Doğrulandı] "Otonom Kalkan" watchdog güvenlik sigortası tamamen dekoratif.** `pardus_healer/daemon.py:38-51` — `setup_watchdog()` yalnızca `/var/run/healer_watchdog_active` dosyası oluşturup izin veriyor; repo genelinde bu dosyayı **okuyan tek bir satır bile yok** (grep ile doğrulandı — yalnızca yazan/silen 3 satır var, okuyan yok). "Kernel panic'e karşı otomatik geri dönüş" iddiasının kod karşılığı yok.

### Yüksek

- **HMAC imzası yalnızca `timestamp:nonce` üzerinden hesaplanıyor**, HTTP metodu/yolu/gövdeyi kapsamıyor — `swarm/auth.py:13,45` **[Doğrulandı]**. TLS yokken bir saldırgan `/health` isteğinin başlıklarını yakalayıp aynı nonce süresi içinde `/heal_all`'a (çok daha tehlikeli uç nokta) karşı kullanabilir.
- **Swarm token eşleştirme/dağıtım mekanizması yok** — her makine kendi rastgele token'ını üretiyor, görüntüleme/paylaşma UI'si yok (`config.py:101-108`); "Zero-Trust" adı, kurulan hiçbir gerçek güven ilişkisi olmadan varsayılan kurulumda iki makinenin birbirini asla doğrulayamaması anlamına geliyor.
- Swarm HTTP servisi `0.0.0.0`'da dinliyor, IP/subnet kısıtlaması yok; `/heal_all` root yetkisiyle onaysız komut çalıştırıyor (`swarm/server.py`, servis `User=root`).
- `healer_rescue.py` — geri alınacak paketler için kritik/temel paket koruması (`apt-mark showessential`) veya `--simulate` ön izlemesi yok; "kurtarma" aracı yanlış pakete dokunursa sistemi daha da bozabilir.

### Orta

- Tekli "Düzelt" (onaysız, anında) ile "Tümünü Onar" (Evet/Hayır diyaloglu) arasında tutarsız güvenlik kapısı — `card.py` vs `app.py`.
- `git_analyzer.py` yalnızca commit tarihinin log satırında alt-dize olarak geçip geçmediğine bakıyor, ama UI/AI dili "Kanıt İzi" gibi kesin nedensellik iddia ediyor — metodoloji zayıf, sunum dili aşırı iddialı.
- `debian/postinst`/`prerm` systemd kontrolünü koşulsuz yapıyor, `postrm` yok — runtime dosyaları (`~/.config/pardus-healer/`, watchdog flag) paket kaldırılınca elde kalabilir.
- Otonom daemon'un "sunum modu" tespiti yalnızca `impress/loimpress/okular/vlc` süreçlerine bakıyor — bir terminal/SSH/tarayıcı demosu sırasında arka planda beklenmedik otomatik "onarım" tetiklenebilir.
- `debian/control`'de `notify-send` (libnotify-bin), `ss` (iproute2), `ufw` bağımlılıkları eksik.

### Genel değerlendirme (Kol 2)

"Phase 1-3" tek commit'te "tamamlandı" denmesindeki şüphe haklı: HMAC+nonce, `shell=False`/argv geçişi, AI Copilot onaylı çalıştırma gibi bazı parçalar gerçekten sağlam mühendislik. Ama sistemi ayakta tutan bağlantı noktaları kırık — Polkit tehlikeli derecede gevşek, paket muhtemelen derlenmiyor, en görünür buton (Düzelt) işlevsiz, ve amiral gemisi güvenlik özelliği (watchdog) süs. **İskelet değil, kırılgan bir bina: parçaların çoğu gerçek ve çalışıyor, ama en temel/en görünür iddialar test edildiği anda çöküyor.**

---

## KOL 3 — Arayüz (UI/UX) ve Marka Tutarlılığı

### Kritik

- **[Doğrulandı] Pardus Doctor açılışta çökebilir.** `pardus_doctor/ui/app.py:34,46,85,90` — GTK3'te olmayan `set_margin_all()` 4 kez çağrılıyor; aynı kod tabanında 30+ yerde doğru API (`set_margin_start/end/top/bottom`) kullanılmış (grep ile doğrulandı) — bu bir uyum sorunu değil, izole bir yazım hatası. Gerçek bir Linux/GTK ortamında acilen doğrulanmalı ve düzeltilmeli.
- **Ana pencerenin görev çubuğu ikonu yok.** `pardus_healer/ui/app.py` içinde `set_icon_from_file`/`set_default_icon` çağrısı yok (yalnızca Doctor'da var) — Alt-Tab, görev çubuğu, pencere değiştirici gibi kullanıcının **sürekli** gördüğü yerlerde jenerik bir ikon görünüyor. "Resmi Pardus uygulaması" izlenimini zedeleyen en somut, en görünür bulgu.

### Yüksek

- Vurgu rengi (`theme.py:10`, `#00a79d` turkuaz) muhtemelen gerçek Pardus kurumsal paletiyle örtüşmüyor (varsayım olarak belirtilmiş — kesin marka kılavuzuyla teyit gerekir); jenerik SaaS paleti hissi veriyor.
- İki kardeş uygulama (Healer/Doctor) farklı vurgu renginde SVG kullanıyor (`#00a79d` vs `#3b82f6`) — aynı paketten kurulan iki araç görsel aile hissi vermiyor.
- Durum renkleri üç ayrı yerde (`theme.py`, `dashboard.py`, `widgets.py`) üç farklı formatta elle kopyalanmış — tek "source of truth" yok.
- "Fix çalıştırma" mantığı üç yerde (`card.py`, `app.py` içi iki worker) neredeyse birebir kopyalanmış ve tutarsız (bkz. Kol 2 — pkexec silme hatası tam da bu tekrardan kaynaklanıyor).
- Kart detaylarını açan mekanizma yalnızca fare tıklamasıyla çalışıyor (`Gtk.EventBox`), klavye ile (Tab+Enter) erişilemiyor — erişilebilirlik eksikliği.
- `pardus-healer-tray.desktop`'ta `Icon=security-high` gibi jenerik sistem ikonları kullanılıyor; sürekli görünen tepsi ikonu markayı hiç taşımıyor.
- Pardus Doctor tamamen farklı bir UX iskeleti sunuyor (sidebar yok, tema anahtarı yok, sabit pencere boyutu, onboarding yok) — iki uygulama kardeş ürün gibi hissettirmiyor.

### Orta / Düşük

- "Demo Verisi Yükle" ile eklenen sahte satırlar gerçek verilerle **görsel olarak birebir aynı** listeleniyor, "DEMO" rozeti yok (Kol 1/2'deki pulse.py bulgusunun UI yansıması).
- `sos_dialog.py`'deki "Pardus Nabız'ı Gör" butonu CSS sınıfına sahip değil, varsayılan gri GTK butonu olarak render oluyor.
- `SwarmPage` sayfa başlığı diğer sayfalardan farklı font boyutu/markup kullanıyor (22pt vs 18pt).
- Sabit piksel genişlikler (sidebar 210px, üç canlı-izleme metresi homojen) küçük ekranlı okul netbook'larında/akıllı tahtalarda taşma riski taşıyor.
- Yoğun emoji kullanımı, emoji fontu kurulu olmayan minimal kurulumlarda "tofu" kare olarak görünebilir.
- i18n altyapısı (gettext) yok — proje bunun zaten farkında (README yol haritasında var), Pardus TR-öncelikli olduğu için şimdilik kritik değil.

### Genel değerlendirme (Kol 3)

Bu bir amatör arayüz değil: gerçek (iddia değil) bir onboarding turu, işlevsel sistem tepsisi, hataları çökme yerine nazikçe gösteren tasarım, gerçekten yeniden kullanılabilir cairo widget'ları var. Ama "resmi Pardus uygulaması" izlenimi tam oturmuyor: pencere ikonu bile eksik, marka rengi muhtemelen tutarsız, iki kardeş uygulama birbirine benzemiyor, ve bir ekran muhtemelen hiç açılmıyor. **"İleri seviye ama son rötuşları eksik bir öğrenci projesi" gibi duruyor — "resmi kurum uygulaması" gibi değil.**

---

## KOL 4 — Gerçek Dünya Kapsamı ve Rekabet Konumu

Pardus forumlarında (forum.pardus.org.tr), Ekşi Sözlük'te ve MEB/kurumsal kaynaklarda en sık tekrarlanan şikayetler: **WiFi bağlantısı, NVIDIA/AMD ekran kartı sürücüsü, yazıcı/CUPS, ses, GRUB/önyükleyici (özellikle Windows dual-boot sonrası), klavye/dil yerelleştirmesi, USB/harici donanım tanıma, çoklu monitör** ve Türkiye'ye özgü, kamu personelini doğrudan etkileyen **e-İmza/e-Devlet (JNLP) uyumluluğu**. Okul/akıllı tahta (ETAP) bağlamında dokunmatik ekran kalibrasyonu ve MEB'in Pardus'u genişletme sürecindeki sürtünmeler de öne çıkıyor.

**Healer'ın mevcut 21 kontrolü bu listenin hiçbirine dokunmuyor.** Şu anki kapsam güçlü şekilde "arka planda sessizce bozulan sistem" (disk, servis, güvenlik, APT) sınıfında; kullanıcıların günlük hayatta gerçekten hissettiği "bu donanım/entegrasyon çalışmıyor" sınıfı tamamen kapsam dışı. Rakip araçlarla (Stacer, BleachBit, Ubuntu'nun `ubuntu-drivers`, Fedora ABRT, Timeshift/Deja Dup) karşılaştırıldığında da GUI tabanlı sürücü asistanı ve tam sistem yedekleme/geri yükleme gibi kategoriler eksik. Detaylı boşluk tablosu ve önerilen özellikler için [[DEVELOPMENT_OPPORTUNITIES.md]].

TEKNOFEST değerlendirme eksenleri (özgünlük, uygulanabilirlik, katma değer/yaygın etki, "yerlilik-millilik" anlatısı) göz önüne alındığında, healer'ın en güçlü konumlanma fırsatı **"gerçek, kaynak gösterilebilir Türkiye/Pardus sorunlarını çözen yerli bir araç"** hikayesi — bu doküman setindeki forum bulguları bu hikayeyi doğrudan destekliyor.

---

## Sayısal Özet

| Kol | Kritik | Yüksek | Orta | Düşük |
|---|---|---|---|---|
| 1 — Çekirdek Motor | 5 | 4 | 7 | 2 |
| 2 — Gelişmiş Özellikler | 4 | 4 | 5 | 2 |
| 3 — UI/UX | 2 | 6 | 6 | 3 |
| 4 — Kapsam/Rekabet | — | — | — | (bkz. DEVELOPMENT_OPPORTUNITIES) |
| **Toplam** | **11** | **14** | **18** | **7** |

Aksiyon sırası ve efor tahmini için → [[FIX_DECISION_MATRIX.md]]
