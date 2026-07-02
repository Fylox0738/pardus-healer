"""Tüm kontrol sınıflarının kayıt merkezi."""

from __future__ import annotations

from .check import BaseCheck


def get_all_checks() -> list[BaseCheck]:
    """Kayıtlı tüm kontrollerin birer örneğini döndürür.

    İçe aktarma burada yapılır ki ``checks`` paketi ``core``'a bağımlı
    olsun, tersi değil (döngüsel bağımlılığı önler).
    """
    from ..checks import ALL_CHECK_CLASSES

    return [cls() for cls in ALL_CHECK_CLASSES]
