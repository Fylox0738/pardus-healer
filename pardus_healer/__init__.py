"""Pardus Healer — akıllı sistem tanılama ve iyileştirme aracı.

Modüler mimari:
    core/    → veri modelleri, tanı motoru, kural (korelasyon) motoru
    checks/  → tekil tanı modülleri (ağ, apt, disk, güvenlik, servisler...)
    report/  → rapor üreticiler (HTML)
    ui/      → GTK3 arayüz katmanı
"""

__version__ = "3.1.0"
__app_name__ = "Pardus Healer"
