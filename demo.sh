#!/bin/bash
# ================================================================
#  PARDUS HEALER — Jüri Demo Betiği
#
#  Kullanım:  bash demo.sh        (repo kök dizininden)
#  Gereksinim: python3 + python3-gi (yalnızca son GUI adımı için)
#
#  Betik hiçbir sistem ayarını DEĞİŞTİRMEZ; yalnızca tanı çalıştırır
#  ve rapor üretir. Onarım adımları GUI içinden, kullanıcı onayı ve
#  pkexec (Polkit) ile yapılır.
# ================================================================

cd "$(dirname "$0")" || exit 1
PY=python3

adim() {
    echo
    echo "════════════════════════════════════════════════════════════"
    echo "  $1"
    echo "════════════════════════════════════════════════════════════"
}

devam() {
    echo
    read -r -p "Devam etmek için Enter'a basın... " _
}

adim "1/5 · Çekirdek motor tek satırda test ediliyor (GTK'sız kanıt)"
$PY -c "from pardus_healer.core.engine import DiagnosisEngine; \
r = DiagnosisEngine().run_all(); \
print('Skor:', r.health_score, '·', 'Not:', r.grade, '·', len(r.results), 'kontrol çalıştı')"
devam

adim "2/5 · Birim testleri (stdlib-only — 3. parti bağımlılık yok)"
$PY -m unittest discover -s tests
devam

adim "3/5 · Komut satırı tam tanı (renkli rapor + içgörüler)"
$PY run.py --cli
echo
echo "(Çıkış kodu: 0=temiz · 1=uyarı var · 2=sorun bulundu — betikler için anlamlı)"
devam

adim "4/5 · HTML + JSON rapor üretimi"
$PY run.py --cli --quiet --html demo_rapor.html --json demo_rapor.json
echo "Üretilen dosyalar: demo_rapor.html · demo_rapor.json"
if command -v xdg-open >/dev/null 2>&1; then
    xdg-open demo_rapor.html >/dev/null 2>&1 &
fi
devam

adim "5/5 · Grafik arayüz başlatılıyor (pencereyi kapatınca demo biter)"
echo "GUI'de gösterilecekler: Sağlık skoru göstergesi · canlı CPU/RAM/Disk ·"
echo "Kontroller sayfasında 'Düzelt' (pkexec) · SOS Kartı · Pardus Nabız ·"
echo "Filo (Swarm) sekmesinde ağ anahtarı eşleştirme."
$PY run.py
