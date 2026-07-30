# CLAUDE.md

Bu dosya, bu depoda çalışan Claude Code (veya başka bir AI ajanı) oturumları için proje rehberidir. Amaç: her yeni oturumun sıfırdan keşif yapmadan doğru konvansiyonlarla kod yazabilmesi.

## Proje nedir?

**Pardus Healer**, Pardus/Debian tabanlı Linux sistemleri için TEKNOFEST'e sunulan bir sistem tanı/onarım paketidir. Tek bir uygulama değil, 3 ayrı üründen oluşan bir suit:

1. **Pardus Healer (GTK3 GUI + CLI)** — proaktif tarama: sistemi periyodik/isteğe bağlı tarar, kural tabanlı bir motorla kök nedeni bulur, tek tıkla `pkexec` ile onarır. `pardus_healer/`
2. **Pardus Doctor (GTK3 GUI + opsiyonel Ollama NLP)** — reaktif olay yeri incelemesi: çökme sonrası `journalctl` loglarını okur, isteğe bağlı yerel AI (Ollama) ile yorumlar, doğal dil → bash komutu çevirir. `pardus_doctor/`
3. **Healer Rescue (bağımsız CLI)** — GUI/masaüstü tamamen çökmüşse (siyah ekran/TTY) elle çalıştırılan, `/var/log/apt/history.log` üzerinden APT işlemlerini geri alan (rollback) son çare aracı. `healer_rescue.py`

Detaylı mimari için [[ARCHITECTURE_MAP.md]], ekran/dialog envanteri için [[MODULE_MAP.md]], kalıcı veri için [[DATA_STORAGE_MAP.md]] dosyalarına bakın. Güncel bulgular ve öncelikler için [[TECHNICAL_AUDIT.md]] ve [[FIX_DECISION_MATRIX.md]] dosyalarına bakın — bunlar zamanla değişir, kod ile birlikte güncel tutulmalıdır.

## Teknoloji yığını

- **Python 3**, harici pip bağımlılığı **yok** — çekirdek tanı motoru yalnızca standart kütüphaneyi kullanır (`subprocess`, `socket`, `os`, `json`...). Bu bilinçli bir tasarım kararıdır: internetsiz/pip'siz, sadece `apt` ile kurulan sistemlerde çalışabilmek için.
- **GTK3 / PyGObject** (`python3-gi`, `gir1.2-gtk-3.0`) — tüm arayüz katmanı.
- **Opsiyonel**: Ollama (`localhost:11434`) varsa Pardus Doctor daha zengin NLP kullanır; yoksa otomatik olarak kural tabanlı moda düşer. Bu fallback'i asla bozmayın — "internetsiz/AI'sız çalışır" projenin temel satış noktalarından biridir.
- Paketleme: `debian/` (postinst/prerm/control/rules), `Makefile`, `install.sh`, systemd `.service` dosyaları, `org.pardus.healer.policy` (Polkit).

## Mimari kurallar (bunları bozmayın)

- **`core/` GTK'dan tamamen bağımsızdır.** `pardus_healer/core/*.py` içine asla `gi`/`Gtk` import etmeyin — bu, motorun `python3 -c "from pardus_healer.core.engine import DiagnosisEngine; ..."` ile tek satırda test edilebilir kalmasını sağlar (bkz. README "Test" bölümü).
- **`checks/` → `core/`'a bağımlıdır, tersi değil.** Döngüsel bağımlılığı önlemek için `registry.py` içe aktarmayı geç (lazy) yapar — bu deseni koruyun.
- **Yeni bir kontrol eklemek**: `pardus_healer/checks/` altına `BaseCheck`'ten türeyen bir sınıf yazıp `checks/__init__.py::ALL_CHECK_CLASSES` listesine eklemek yeterli; dashboard/skor/rapor otomatik kapsar. Örnek için README'ye bakın.
- **Tüm kalıcı yerel veri sessiz-hata toleranslıdır**: `config.py`, `history.py` gibi dosyalar okuma/yazma hatasında **asla exception fırlatmaz**, varsayılana döner. Yeni depolama kodu yazarken bu deseni koruyun — ayar/geçmiş dosyası bozuksa uygulama çökmemeli.
- **Kök yetki gerektiren her komut `Fix.needs_root=True` ile işaretlenip `pkexec` üzerinden çalıştırılır** (`core/shell.py`). Doğrudan `sudo` veya parola isteyen bir akış eklemeyin — GUI/okul senaryosunda terminal bilgisi varsayılmaz.
- **`shell=True` kullanmayın.** Geçmişte (`4122204`) bir komut enjeksiyonu açığı bu yüzden oluşmuştu ve kapatıldı. Yeni kod, komutları liste (`["cmd", "arg1", "arg2"]`) olarak `subprocess`'e vermeli; kullanıcı girdisi asla doğrudan bir kabuk string'ine enjekte edilmemeli.

## Bilinen riskli/kırılgan alanlar

- `pardus_healer/core/pulse.py::seed_demo_data()` **jüri/demo sunumu için uydurma veri** ekler ve bunu gerçek kullanıcı verisiyle **aynı dosyaya** (`~/.local/share/pardus-healer/pulse.jsonl`) yazar. Demo veri ile gerçek veri hiçbir şekilde ayırt edilemiyor — bkz. [[TECHNICAL_AUDIT.md]].
- "Phase 1-3" özellikleri (Swarm, Autonomous Daemon, Zero-Trust, System Tray, Polkit, Debian Packaging) tek bir commit'te (`910a356`) toplu olarak "tamamlandı" işaretlenmiş; kapsamın genişliğine göre yüzeysel kalmış kısımlar olabilir — bkz. [[TECHNICAL_AUDIT.md]].
- Otomatik test paketi **yok**. Değişiklik yaparken en azından README'deki tek satırlık motor smoke-test'ini ve `python3 run.py --cli` çıktısını elle doğrulayın.

## Dil ve ton

- Kod içi docstring/yorumlar ve kullanıcıya gösterilen tüm metinler **Türkçe**. Pardus resmi/millî bir dağıtım olduğu için bu tutarlılığı bozmayın.
- Commit mesajları bu depoda şimdiye kadar Türkçe/İngilizce karışık kısa `feat:`/`fix:` formatında yazılmış; bu formatı sürdürün.

## Yarışma bağlamı

Bu depo bir TEKNOFEST teslimidir; jüri değerlendirmesi yapacaktır. Kod değişikliği önerirken/yaparken önceliği şuraya verin: (1) gerçek hataların/güvenlik açıklarının kapatılması, (2) "vitrin" özelliklerin (demo verisi, yarım kalan Phase 1-3 modülleri) gerçek/dürüst hale getirilmesi, (3) arayüzün Pardus'un resmi bir uygulaması izlenimi vermesi. Güncel öncelik sırası için [[FIX_DECISION_MATRIX.md]]'ye bakın.
