# Düzeltme Önceliklendirme Matrisi

> **Durum (2026-07-29): P0 (11/11), P1 (8/8) ve P2 (9/9) maddelerinin
> tamamı uygulandı**, ayrıca [[DEVELOPMENT_OPPORTUNITIES.md]] #1-#3 (e-imza,
> yazıcı, GRUB) yeni kontrol olarak eklendi. Bu dosya, neyin neden
> önceliklendirildiğine dair tarihsel gerekçe olarak korunuyor. P3 kapsam
> dışı kararları hâlâ geçerlidir.
>
> **Bağımsız doğrulama (2026-07-30):** Yukarıdaki P0/P1/P2 iddiaları kaynak
> kod okunarak ve motor gerçekten çalıştırılarak (`DiagnosisEngine.run_all()`,
> `run.py --cli`) tek tek teyit edildi — tamamı doğru çıktı, tek istisna
> **madde 21** idi ("Fix çalıştırma" mantığının ortak yardımcıya taşınması):
> kod hâlâ `card.py`/`app.py` içinde üç kopya hâlindeydi. Bu oturumda
> gerçekten `ui/fix_runner.py`'ye taşındı; bu sırada "Otomatik Onar"ın çıkış
> kodundan bağımsız her zaman ✓ gösterdiği ayrı bir kozmetik hata da
> düzeltildi. Ayrıca README.md'deki "Yol Haritası" bu tabloyla çelişen iki
> eskimiş madde (geçmiş takibi, açık port/SSH kontrolü — ikisi de zaten
> yapılmıştı) güncellendi, `debian/postinst`/`prerm` systemctl'siz ortamda
> paket kurulumunu tamamen düşürmeyecek şekilde korumaya alındı ve eksik
> olan `debian/postrm` eklendi (watchdog flag temizliği).

> [[TECHNICAL_AUDIT.md]]'deki bulguların uygulama sırası. **Öncelik** jüri görünürlüğü + risk + efora göre belirlendi. Efor tahminleri: **S** (birkaç satır/dakikalar), **M** (bir dosya, yeni küçük mantık/UI, saatler), **L** (yeni modül/mimari parça, çok daha uzun).

## P0 — Demo güvenliği için şart (tümü S/M efor, hepsi bu oturumda yapılabilir)

| # | Kol | Bulgu | Dosya | Ciddiyet | Efor |
|---|---|---|---|---|---|
| 1 | 2 | "Düzelt" butonu `pkexec`'i siliyor → ana özellik çalışmıyor | `ui/card.py:186-187` | Kritik | S |
| 2 | 3 | Pardus Doctor'da olmayan `set_margin_all()` → muhtemel açılış çökmesi | `pardus_doctor/ui/app.py:34,46,85,90` | Kritik | S |
| 3 | 1 | Açılış süresi 60sn+ yanlış hesaplanıyor (regex) | `checks/boot.py:16-17,70-82` | Kritik | S |
| 4 | 1 | `FAIL_SEC` eşiği hiç kullanılmıyor | `checks/boot.py:50-57` | Kritik | S |
| 5 | 1 | Açık port kontrolü localhost-only servisleri "dışa açık" sayıyor | `checks/security_extra.py:43` | Kritik | S |
| 6 | 1 | Kapalı oto-güncelleme "etkin" gösteriliyor | `checks/security_extra.py:137-138` | Kritik | S |
| 7 | 2 | Polkit parolasız root yetkisi veriyor | `org.pardus.healer.policy:17` | Kritik | S |
| 8 | 2 | Debian paket adı changelog↔control uyuşmuyor, paket derlenmiyor | `debian/changelog:1` | Kritik | S |
| 9 | 3 | Ana pencerede görev çubuğu ikonu yok | `ui/app.py` | Yüksek | S |
| 10 | 1/2/3 | Demo veri gerçek veriyle ayrım yapılmadan karışıyor | `core/pulse.py`, `ui/pulse_dialog.py` | Kritik | M |
| 11 | 2 | Watchdog dosyası hiç okunmuyor, iddia sahte | `daemon.py:38-51` | Kritik | M |

## P1 — Demodan önce yapılmalı (gerçek ama biraz daha efor)

| # | Kol | Bulgu | Dosya | Ciddiyet | Efor |
|---|---|---|---|---|---|
| 12 | 1 | `ok/info/unknown()` fix-sıfırlama mantığı çalışmıyor (sentinel eksik) | `core/check.py:68,72-79` | Yüksek | S |
| 13 | 1 | `history.json`/`settings.json` atomik yazılmıyor (race condition) | `core/history.py`, `config.py` | Yüksek | S |
| 14 | 2 | HMAC imzası path/method'u kapsamıyor (cross-endpoint replay) | `swarm/auth.py:13,45` | Yüksek | S |
| 15 | 1 | CPU sıcaklığı yanlış sensörden okunabiliyor | `checks/cpu.py:92-109` | Yüksek | S/M |
| 16 | 1 | S.M.A.R.T. kontrolü VM'lerde/LVM'de atlanıyor, ortak shell yardımcısını kullanmıyor | `checks/hardware.py:87-117` | Yüksek | S/M |
| 17 | 2 | `healer_rescue.py` temel paketleri koruma altına almıyor | `healer_rescue.py:106-120` | Yüksek | M |
| 18 | 3 | Kart genişletme klavye ile erişilemiyor | `ui/card.py:93-96` | Yüksek | M |
| 19 | 3 | Tepsi/`.desktop` ikonları jenerik, marka taşımıyor | `tray.py`, `*.desktop` | Yüksek | S/M |

## P2 — Zaman kalırsa (tutarlılık/cila, jüri demoyu doğrudan bozmaz)

| # | Kol | Bulgu | Efor |
|---|---|---|---|
| 20 | 3 | Durum renkleri 3 yerde tekrar tanımlı, tek kaynağa taşınmalı (`theme.py`↔`widgets.py`↔`dashboard.py`) | M |
| 21 | 3 | "Fix çalıştırma" mantığı 3 yerde kopya — `core/shell.py`'de ortak yardımcıya taşı | M |
| 22 | 3 | Healer/Doctor SVG ve UX iskeleti tutarsız | M |
| 23 | 2 | Swarm token görüntüleme/eşleştirme UI'si yok | M/L |
| 24 | 1 | `text_report.py` ölü kod — CLI'ye bağla ya da kaldır | S |
| 25 | 1 | DNS kontrolü tek sabit alan adına bağımlı | S |
| 26 | 1 | Disk kontrolü yalnızca `/`'e bakıyor | S |
| 27 | 2 | `debian/control` eksik bağımlılıklar (`libnotify-bin`, `iproute2`, `ufw`) | S |
| 28 | 2 | Otonom onarım "sunum modu" tespiti dar (yalnızca 4 süreç) | S |

## P3 — Bilinen kısıt olarak dokümante edilecek, bu round'da uygulanmayacak

- Swarm/HTTP servisinde TLS yok (yalnızca HMAC+nonce) — gerçek çok-makineli üretim dağıtımı için gerekli ama bu round'un kapsamı dışında; TECHNICAL_AUDIT'te ve README'de açıkça "bilinen kısıt" olarak belirtilecek.
- Gerçek Pardus marka renk paletiyle tam örtüşme — resmi marka kılavuzu doğrulanmadan tahmini bir renk değişikliği önerilmeyecek; en azından turkuazın *tutarlı* kullanılması (madde 20) yapılacak.
- i18n/gettext altyapısı — proje zaten kendi yol haritasında bunu biliyor, TR-öncelikli olduğu için bu round dışında.
- Kol 4'te tespit edilen tüm yeni tanı modülleri (yazıcı, GPU, ses, GRUB, e-imza vb.) — bunlar "düzeltme" değil "yeni özellik"; bkz. [[DEVELOPMENT_OPPORTUNITIES.md]], ayrı bir kapsam kararı gerektiriyor.

---

**Öneri:** P0'daki 11 madde tek oturumda bitirilebilir boyutta ve hepsi jüri karşısında doğrudan görünür/utandırıcı olabilecek türden — bunlar tartışmasız yapılmalı. P1 de makul bir ek efor karşılığında gerçek güvenilirlik kazandırıyor. P2/P3 zaman bütçesine bağlı.
