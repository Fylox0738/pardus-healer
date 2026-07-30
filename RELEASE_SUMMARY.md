# Sürüm Özeti — 1.0.0 Release Candidate (2026-07-30)

Bu belge, teslim öncesi son turda yapılan tüm çalışmanın alan-alan özetidir.
Her bölüm: **özet → bulunan sorunlar → yapılan değişiklikler → nasıl test edilir.**
Ayrıntılı tarihçe: [[CHANGELOG.md]], bulgu kaynağı: [[TECHNICAL_AUDIT.md]] + [[FIX_DECISION_MATRIX.md]].

---

## 1 · Statik Analiz / Kod Kalitesi

**Özet:** Tüm `.py` dosyaları sözdizimi denetiminden geçti; mimari kurallar doğrulandı.

- **Sorunlar:** `core/shell.run()` string girdide `shell=True`'ya düşen gizli bir yol içeriyordu (hiçbir çağıran kullanmıyordu ama açık kapıydı); `network.py` süreç-geneli `socket.setdefaulttimeout()` kullanıyordu (paralel tarama ile yarış riski).
- **Değişiklikler:** `core/shell.py` — string girdi artık `shlex.split` → argv; `shell=True` kod tabanında sıfır kullanım. `checks/network.py` — soket-başına `settimeout()`; DNS tarafında işlevsiz global timeout kaldırıldı. `core/` içinde `gi`/GTK importu: **0** (kural korunuyor).
- **Test:** `python3 -m compileall -q pardus_healer pardus_doctor` + `grep -rn "shell=True" --include="*.py"` → yalnızca yorum satırları.

## 2 · Testler / Çalışma Zamanı

**Özet:** Sıfırdan 57 testlik stdlib-only birim test paketi + CI eklendi; motor uçtan uca doğrulandı.

- **Sorunlar:** Depoda hiç otomatik test yoktu; `healer_rescue.py` minimal yerel ayarlı (LANG=C) gerçek bir TTY'de emoji basarken **çökebiliyordu** (bizzat test paketinin yakaladığı hata).
- **Değişiklikler:** `tests/` (boot ayrıştırma, fix-sentinel, Swarm HMAC, Doctor güvenlik katmanı, Rescue ayrıştırma+koruma, port/direktif regex'leri, atomik yazma, Config, motor smoke). `healer_rescue.py` — `sys.stdout.reconfigure(errors="replace")`; `parse_history()` test edilebilir hale getirildi; `apt-get -s` **simülasyon** seçeneği eklendi. `.github/workflows/ci.yml` + `make test`.
- **Test:** `make test` → 57/57 OK. `python3 run.py --cli` → 25 kontrol, çökme yok.

## 3 · Güvenlik İncelemesi

**Özet:** Önceki turda kapatılan kritik açıklar bağımsız olarak yeniden doğrulandı; kalanlar kapatıldı.

- **Sorunlar (tümü kapalı):** Polkit parolasız root (`allow_active=yes`); HMAC imzasının uç nokta bağlamını kapsamaması (cross-endpoint replay); "Düzelt" butonunun `pkexec` silmesi; demo verinin gerçek veriyle karışması; Rescue'nun temel paketleri geri alma listesine sokması.
- **Değişiklikler:** Bu turda ek olarak: `shell=True` yolunun tamamen kapatılması (§1), Rescue simülasyon modu (§2), e-İmza fix komutunun paket adının depo doğrulaması (aşağıda §6).
- **Test:** `tests/test_swarm_auth.py` (replay/nonce/timestamp), `tests/test_doctor_safety.py` (rm -rf, zincirleme, komut ikamesi), `tests/test_rescue_parse.py` (koruma listesi + enjeksiyon süzme).

## 4 · Paketleme / Polkit / systemd

**Özet:** `.deb` üretimini durduracak üç ayrı bloker statik olarak kapatıldı; kurulum/kaldırma yaşam döngüsü tamamlandı.

- **Sorunlar:** `debian/source/format` yoktu ve sürüm `1.0.0-1` (revizyonlu) — native formatla çelişip derlemeyi durdururdu; `Makefile` `/usr/local/bin`'e kuruyordu (`dh_usrlocal` hatası); `postrm` yoktu; `postinst/prerm` systemd'siz ortamda kurulumu düşürebilirdi.
- **Değişiklikler:** `debian/source/format` = `3.0 (native)`; sürüm `1.0.0`; Makefile → `/usr/bin/healer-rescue`; `debian/postrm` (watchdog bayrak temizliği); `command -v systemctl` korumaları; `make deb` hedefi; `.gitattributes` ile kabuk/debian dosyalarına LF garantisi. Servis/desktop `Exec` yolları ↔ `/opt/pardus-suite` yerleşimi ↔ `cli.py` bayrakları (`--daemon/--server/--tray`) uçtan uca tutarlı doğrulandı.
- **Test:** Statik doğrulama tamam; **gerçek `dpkg-buildpackage` çalıştırması bir Debian/Pardus makinesinde yapılmalı** (`make deb`) — bu ortamda (Windows) mümkün değildi.

## 5 · UX / README / Demo

**Özet:** Jüri akışı tek komuta indirildi; dokümantasyon kod gerçeğiyle eşitlendi.

- **Sorunlar:** README kurulum satırında GUI'nin gerçekte istediği iki paket eksikti (`python3-gi-cairo` olmadan dashboard, `gir1.2-appindicator3-0.1` olmadan tepsi açılmaz); yol haritası yapılmış işleri "yapılacak" gösteriyordu; jüri için çalıştırma kılavuzu yoktu.
- **Değişiklikler:** `demo.sh` (5 adımlı, sistemi değiştirmeyen demo), `HOW_TO_RUN_FOR_JURY.md` (tek sayfa), README: doğru bağımlılıklar + demo bölümü + "Bilinen Kısıtlar" (Swarm'da TLS yok — dürüst beyan), `CHANGELOG.md`.
- **Test:** `bash demo.sh` Pardus'ta adım adım; README komutları birebir çalışır durumda.

## 6 · Pardus Entegrasyon Araştırması

**Özet:** Kontrollerimizin hedeflediği sorunların gerçek/kaynak gösterilebilir Pardus şikayetleri olduğu belgelendi.

- **Bulgular:** e-İmza (forum #27051 — çözümsüz kapanmış, #32457 — Pardus 25'te sürüyor), GRUB/dual-boot (#26469), güncelleme sonrası açılmama (#10535), 3-7 dk açılış (#9708), yazıcı (#8781); Pardus'un ayrı bir `pardus-boot-repair` aracı tutması GRUB/APT kapsamımızı doğruluyor. **`icedtea-netx` paketinin Pardus depolarında (21/23/25 tabanları) mevcut olduğu doğrulandı** — e-İmza fix komutu topluluk çözümüyle birebir örtüşüyor.
- **Değişiklikler:** Kanıt tablosu `HOW_TO_RUN_FOR_JURY.md`'ye eklendi; e-İmza kontrolünün önerisine OpenWebStart alternatifi eklendi. Gelecek iş (kapsam dışı): oturum açma döngüsü tanısı, UYAP Editör entegrasyonu, üretici yazıcı sürücüsü önerisi.

## 7 · Sürüm / CI

**Özet:** Sürüm 1.0.0 olarak sabitlendi; her push'ta otomatik doğrulama.

- **Değişiklikler:** `CHANGELOG.md`, `debian/changelog` senkron; GitHub Actions CI (derleme + 57 test + CLI smoke); `make test` / `make deb` hedefleri; `rc/fix-for-competition` dalı.
- **Test:** Push sonrası Actions sekmesinde yeşil koşu; yerelde `make test`.

---

## Teslim öncesi gerçek Pardus makinesinde yapılması gerekenler

1. `make deb` ile gerçek `.deb` üretimi (statik olarak hazır, canlı doğrulanmadı).
2. GUI'nin görsel turu (pencere/tepsi ikonları, klavye erişimi) — kod düzeyinde doğru, ekranda teyit edilmeli.
3. İki makineli Swarm demosu (aynı ağ anahtarıyla).
4. `sudo bash demo.sh` değil, normal kullanıcıyla `bash demo.sh` (pkexec penceresini jüriye göstermek için).
