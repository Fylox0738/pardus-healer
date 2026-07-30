# Değişiklik Günlüğü

Bu dosya projedeki dikkate değer değişiklikleri özetler.
Biçim [Keep a Changelog](https://keepachangelog.com/tr/) esinlidir.

## [1.0.0] — 2026-07-30

İlk kararlı sürüm (TEKNOFEST teslimi).

### Eklendi
- **25 tanı kontrolü** — ağ/DNS, APT, bozuk paketler, güncellemeler, disk
  (kök + /home), RAM/swap, CPU yük/sıcaklık, pil, S.M.A.R.T., açılış süresi,
  systemd servisleri, güvenlik duvarı, açık portlar, SSH, otomatik
  güncelleme, günlük hataları, bakım; ve Pardus kullanıcılarının gerçek
  şikayetlerine karşılık gelen üç yeni kontrol: **yazıcı/CUPS**,
  **GRUB önyükleyici**, **e-İmza/e-Devlet uyumluluğu**.
- **Otonom Kalkan (daemon)** — arka planda periyodik tarama + onaylı
  otomatik onarım; sunum/ders modunda erteleme; yarım kalan onarım turunu
  tespit eden watchdog.
- **Filo (Swarm)** — yerel ağda düğüm keşfi, HMAC+nonce imzalı API,
  arayüzden ağ anahtarı görüntüleme/eşleştirme/kopyalama.
- **Healer Rescue** — TTY'den APT işlem geri alma; temel sistem paketleri
  koruma listesi, `apt-get -s` ile uygulamadan önce simülasyon seçeneği,
  minimal yerel ayarlarda (LANG=C) çökmeyen çıktı.
- **Birim test paketi** — 57 stdlib-only test (`make test` /
  `python3 -m unittest discover -s tests`) + GitHub Actions CI.
- Jüri için `demo.sh`, `HOW_TO_RUN_FOR_JURY.md`, ``.

### Düzeltildi
- "Düzelt" butonu `pkexec`'i komuttan silip sessizce başarısız oluyordu —
  onarım mantığı `ui/fix_runner.py`'de tek kaynağa toplandı.
- Açılış süresi 60 sn üzeri ("1min 7.311s") yanlış ayrıştırılıyordu;
  120 sn üzeri FAIL eşiği hiç tetiklenmiyordu.
- Açık port kontrolü, yalnızca 127.0.0.1'e bağlı servisleri "dışa açık"
  sayıyordu (ss çıktısının peer sütunu yüzünden).
- Kapatılmış otomatik güvenlik güncellemesi "etkin" raporlanıyordu.
- Pardus Doctor, GTK3'te olmayan `set_margin_all()` çağrıları yüzünden
  açılışta çökebiliyordu.
- CPU sıcaklığı GPU/NVMe sensörlerinden okunabiliyordu; S.M.A.R.T.
  kontrolü VM disklerini (vda vb.) atlıyordu.
- "Pardus Nabız" demo verisi gerçek kullanıcı verisiyle aynı dosyaya
  yazılıyordu — artık ayrı dosyada ve `is_demo` etiketli.
- `settings.json`/`history.json` yazımları atomik hale getirildi.
- Debian paketi derlenemiyordu (changelog↔control ad uyuşmazlığı, eksik
  `debian/source/format`, `/usr/local` kurulum hedefi, eksik `postrm`).

### Güvenlik
- Polkit kuralı parolasız root yetkisi veriyordu (`allow_active=yes`) —
  artık her durumda `auth_admin` gerekiyor.
- Swarm HMAC imzası yalnızca `timestamp:nonce` kapsıyordu — artık
  `method+path`'i de kapsıyor (cross-endpoint replay kapatıldı); nonce'lar
  tek kullanımlık.
- `shell=True` kod tabanından tamamen kaldırıldı; `core/shell.run()`
  string girdide bile kabuk yorumlaması yapmaz (shlex → argv).
- Rescue, apt geçmişindeki serbest metni katı paket-adı regex'inden
  geçirir; temel sistem paketlerini geri alma önerisine sokmaz.
