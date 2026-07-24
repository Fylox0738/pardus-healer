"""Copilot'un ürettiği bash komutlarını çalıştırmadan önce denetleyen güvenlik katmanı.

Önceden (bkz. git geçmişi) ``translate_to_bash()`` çıktısı hiçbir kontrolden
geçmeden ``shell=True`` ile doğrudan çalıştırılıyordu. Bu modül, en azından
bilinen derecede yıkıcı komut kalıplarını reddeden bir ilk savunma hattıdır.
Tam ``SafeExecutor`` (allowlist + dry-run) ayrı bir aşamada genişletilecektir.
"""

from __future__ import annotations

import re

DANGEROUS_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"rm\s+(-\w*r\w*f\w*|-\w*f\w*r\w*)\s+(/|~|\$HOME)\b"), "kök/ev dizinini silme"),
    (re.compile(r"\bdd\s+.*of=/dev/[sh]d"), "disk imajlama/üzerine yazma"),
    (re.compile(r"\bmkfs\b"), "disk biçimlendirme"),
    (re.compile(r">\s*/etc/(passwd|shadow)\b"), "kritik sistem dosyasının üzerine yazma"),
    (re.compile(r"\bchmod\s+-R?\s*777\s+/"), "kök dizin izinlerini açma"),
    (re.compile(r":\(\)\s*\{\s*:\|:\s*&\s*\}\s*;"), "fork bomb"),
    (re.compile(r"\bshutdown\b|\breboot\b|\bpoweroff\b"), "sistemi kapatma/yeniden başlatma"),
]


def check_command_safety(command: str) -> tuple[bool, str | None]:
    """Komutu bilinen tehlikeli kalıplara karşı denetler.

    Dönüş: (güvenli_mi, ret_gerekcesi). Güvenliyse ikinci eleman None olur.
    """
    if not command or not command.strip():
        return False, "boş komut"
    for pattern, reason in DANGEROUS_PATTERNS:
        if pattern.search(command):
            return False, reason
    return True, None
