# Pardus Healer — Jüri Değerlendirme Kılavuzu (Tek Sayfa)

**Pardus Healer**, Pardus/Debian sistemler için üç üründen oluşan bir tanı ve
onarım paketidir: **Healer** (proaktif tarama + tek tıkla onarım, GTK3),
**Doctor** (çökme sonrası log analizi + isteğe bağlı yerel AI) ve
**Rescue** (siyah ekran/TTY durumunda APT geri alma). İnternetsiz çalışır,
hiçbir buluta veri göndermez, tek pip bağımlılığı yoktur.

## Kurulum (Pardus / Debian / Ubuntu)

```bash
sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-appindicator3-0.1
# isteğe bağlı, daha zengin tanı: lm-sensors ufw smartmontools
```

## 5 Dakikalık Demo — tek komut

```bash
bash demo.sh
```

Betik sırasıyla gösterir: **(1)** çekirdek motorun GTK'sız tek satırda
çalıştığı, **(2)** 57 birim testinin geçtiği, **(3)** renkli CLI tanı raporu
ve kök-neden içgörüleri, **(4)** HTML/JSON rapor üretimi, **(5)** grafik
arayüz. Betik hiçbir sistem ayarını değiştirmez.

## GUI'de bakılmaya değer noktalar

- **Genel Bakış**: 0-100 sağlık skoru, canlı CPU/RAM/Disk, skor trendi.
- **Kontroller**: 25 kart; sorunlu kartta **Düzelt** → komut `pkexec` ile
  (grafik parola penceresi) çalışır, çıktısı canlı akar. **Tümünü Onar**
  önce listeyi gösterip onay ister; varsa Timeshift ile ön yedek alır.
- **SOS Kartı**: teknik olmayan kullanıcının BT sorumlusuna göndereceği
  hazır arıza metni. **Pardus Nabız**: birikmiş SOS olayları (demo veri
  ayrı dosyada, "DEMO" etiketiyle — gerçek veriyle asla karışmaz).
- **Filo (Swarm)**: iki makinede aynı **Ağ Anahtarı** girilince ağdaki
  düğümler keşfedilir; skorları görülür, tek tık uzak onarım. API,
  HMAC+nonce imzalıdır (uç nokta bağlamı dahil — replay koruması).
- **Rescue**: `sudo healer-rescue` → son APT işlemleri listelenir; temel
  sistem paketleri korunur; **S** seçeneği uygulamadan önce simülasyon
  (`apt-get -s`) gösterir.

## Bu proje gerçek Pardus sorunlarını çözüyor (kaynaklar)

| Sorun | Kanıt | İlgili kontrol |
|---|---|---|
| e-İmza/e-Devlet çalışmıyor (Pardus 23.2, çözümsüz kapanan konu) | forum.pardus.org.tr/t/27051 | e-İmza kontrolü |
| JNLP/e-imza sorunu Pardus 25'te de sürüyor | forum.pardus.org.tr/t/32457 | e-İmza kontrolü |
| Resmî e-imza kurulumu 6 ayrı elle komut istiyor | gonullu.pardus.org.tr (e-imza kılavuzu) | tek-tık kurulum fix'i |
| GRUB gelmiyor / Windows girişi kayboluyor | forum.pardus.org.tr/t/26469 | GRUB kontrolü |
| Depo güncellemesi sonrası sistem açılmıyor | forum.pardus.org.tr/t/10535 | Rescue geri alma |
| 3-7 dakikalık açılış şikayetleri | forum.pardus.org.tr/t/9708 | açılış süresi kontrolü |
| Yazıcı görünüyor ama yazdırmıyor | forum.pardus.org.tr/t/8781 | yazıcı/CUPS kontrolü |
| Pardus'un ayrı bir "boot repair" aracı tutması | github.com/pardus/pardus-boot-repair | GRUB + APT kontrolleri |

## Doğrulama komutları

```bash
make test                          # sözdizimi + 57 birim testi
python3 run.py --cli               # tam tanı (çıkış kodu 0/1/2)
python3 run.py --cli --quiet       # yalnızca skor (otomasyon)
make deb                           # .deb paketi üretimi (dpkg-buildpackage)
```

## Bilinen kısıtlar (bilinçli kapsam kararı)

Swarm API'sinde TLS yok (paylaşılan anahtar + HMAC + nonce; güvenilir yerel
ağ hedefi), i18n yok (TR öncelikli). Ayrıntı: README "Bilinen Kısıtlar".
