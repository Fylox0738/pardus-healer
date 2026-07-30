# Geliştirme Fırsatları — Yeni Özellik Önerileri

> [[TECHNICAL_AUDIT.md]] Kol 4'teki araştırmaya dayanır. Bunlar **düzeltme değil, yeni kapsam** — [[FIX_DECISION_MATRIX.md]]'deki P0/P1'den sonra, zaman bütçesi varsa değerlendirilmeli. Her madde için gerçekçi bir efor tahmini ve **doğrulama kısıtı** var: bu depo üzerinde çalışan ajan bir Windows makinesinde çalışıyor, gerçek bir Pardus/Linux/GTK ortamı yok — yani hiçbir yeni modül gerçek donanım/gerçek Pardus kurulumunda elle test edilmeden "bitti" sayılmamalı.

## Neden bu liste böyle?

Pardus forumlarında (bkz. TECHNICAL_AUDIT Kol 4) en çok tekrarlanan şikayetler **donanım/entegrasyon** katmanında (yazıcı, ekran kartı, ses, GRUB, USB, çoklu monitör, e-imza), ama healer'ın mevcut 21 kontrolü tamamen **sistem sağlığı** katmanında (disk, servis, güvenlik, APT). Bu, jüri karşısında "gerçek kullanıcı sorununu çözüyor muyuz?" sorusuna verilecek en zayıf cevap. Aşağıdaki öneriler bu boşluğu, mevcut mimariye (`BaseCheck` alt sınıfı yazıp `checks/__init__.py`'ye eklemek) hiçbir yapısal değişiklik yapmadan kapatacak şekilde tasarlandı.

## Öncelik sırasıyla öneriler

### 1. e-İmza / e-Devlet Uyumluluk Kontrolcüsü — **en yüksek etki, Pardus'a özgü**
Java/JNLP çalışma zamanının (`icedtea-netx`/`openwebstart`), kart okuyucu sürücüsünün ve tarayıcı PKCS11 modülünün kurulu/etkin olup olmadığını denetleyen bir `BaseCheck`. Kamu personelinin günlük işini doğrudan durduran, Pardus'a özgü, "yerli/milli" anlatısına en çok uyan özellik. **Efor: M** (kontrol mantığı basit — dosya/paket varlığı kontrolü; asıl risk gerçek bir e-imza ortamında test edilememesi).

### 2. Yazıcı/CUPS Tanı Modülü
`cups` servis durumu, spool tıkanıklığı, `lpstat -p` çıktısı, kullanıcının `lpadmin` grubunda olup olmadığı. Forumlardaki en sık tekrarlanan kategorilerden biri, mevcut `services.py` desenine kolayca oturur. **Efor: S/M.**

### 3. GRUB / Önyükleyici Onarım Sihirbazı
Dual-boot/BIOS güncellemesi sonrası GRUB kaybı çok sık şikayet ediliyor. `update-grub`/`grub-install` tetikleyen, EFI girişini kontrol eden bir kontrol+fix çifti; `healer_rescue.py`'nin "geri al" felsefesine paralel. **Efor: M** — kök dosya sistemi/EFI ile uğraştığı için diğerlerinden daha riskli, iyi test edilmeden `default_fix` olarak otomatik çalıştırılmamalı (yalnızca *tanı*, düzeltme adımı elle onaylı ve son derece açık uyarılı olmalı).

### 4. GPU Sürücü Asistanı (NVIDIA/AMD)
Mevcut genel "sürücü/firmware eksikliği" kontrolünü, bilinen somut Pardus hatalarına (AMD kurucusunun "unrecognized OS" hatası, NVIDIA+HDMI algılanmama) bağlayan özel bir kontrol. **Efor: M** — donanım-spesifik olduğundan gerçek donanımda doğrulanmadan güvenilir olduğu iddia edilemez; MVP olarak yalnızca "hangi GPU var, hangi sürücü paketi önerilir" bilgilendirmesiyle sınırlı tutulmalı (otomatik kurulum riskli).

### 5. Ses Alt Sistemi Tanısı
PulseAudio/PipeWire servis durumu, mute/route durumu, codec algılama. Mevcut `journalctl`/servis tanı altyapısına doğal bir ek. **Efor: S/M.**

### 6. USB/Donanım Tanıma Raporu
`lsusb`/`lspci` taraması + "bağlı ama sürücüsüz" cihaz tespiti. Salt-okunur bir bilgilendirme kartı olarak düşük riskli. **Efor: S.**

### 7. Kurumsal/Okul Modu (AD/LDAP + ETAP akıllı tahta)
`realmd`/`sssd` domain bağlantı sağlığı ve dokunmatik ekran kalibrasyon durumu. MEB'in okullara Pardus'u genişletme sürecine doğrudan hitap eder — TEKNOFEST'in "yaygın etki/sosyal fayda" kriteri için güçlü. **Efor: L** — niş donanım/servisler, gerçek bir okul/ETAP ortamı olmadan doğrulanması en zor madde.

### 8. Tam Sistem/Kullanıcı Verisi Yedekleme-Geri Yükleme
Şu anki rollback yalnızca APT paket geçmişini kapsıyor. Timeshift entegrasyonu zaten `daemon.py` içinde kısmen var (pre-fix snapshot) — bunu kullanıcının manuel tetikleyebileceği bir "Yedekle/Geri Yükle" ekranına genişletmek. **Efor: M/L.**

## Önerilen yaklaşım (zaman kısıtlı olduğu için)

Hepsini aynı anda yapmaya çalışmak, hiçbirini gerçek bir Pardus makinesinde test edememe riskiyle birleşince tehlikeli — yarım/test edilmemiş bir "GRUB onarıcı" kötü giderse gerçek bir kullanıcının sistemini bozar. Gerçekçi öneri:

- **1 tanesini** (muhtemelen **#1 e-İmza kontrolcüsü** — en özgün, en Pardus'a-özgü, en düşük riskli çünkü yalnızca *tespit*, otomatik geri dönüşü olmayan bir işlem yapmıyor) uçtan uca, iyi test edilmiş şekilde ekleyip demo/sunumda öne çıkarmak, 8 tanesini yarım bırakmaktan çok daha güçlü bir jüri izlenimi bırakır.
- #2 (yazıcı) ve #6 (USB/donanım raporu) da düşük riskli, salt tanı ağırlıklı — zaman kalırsa ikinci/üçüncü sıra adaylar.
- #3 (GRUB) ve #7 (kurumsal/okul) yüksek etkili ama yüksek riskli/yüksek efor — bu round'da yalnızca *tasarım notu* olarak bırakılıp bir sonraki sürüme (README yol haritasına) eklenmesi daha güvenli olabilir.

Nihai kapsam kararı kullanıcı ile birlikte, kalan zaman bütçesine göre verilecek.
