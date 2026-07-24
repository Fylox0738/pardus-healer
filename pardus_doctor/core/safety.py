"""Copilot'un ürettiği bash komutlarını çalıştırmadan önce denetleyen güvenlik katmanı.

Önceden (bkz. git geçmişi) ``translate_to_bash()`` çıktısı hiçbir kontrolden
geçmeden ``shell=True`` ile doğrudan çalıştırılıyordu. Bu modül iki savunma
hattı sunar:

1. ``check_command_safety`` — bilinen derecede yıkıcı komut kalıplarını reddeder.
2. ``to_argv`` — onaylanan komutu ``shell=True`` KULLANMADAN çalıştırmak için
   argv listesine çevirir; asıl enjeksiyon kapısını (kabuk yorumlaması) bu kapatır.

Bu tam bir allowlist değildir (bkz. yol haritasındaki SafeExecutor aşaması),
ama iki hattın birleşimi bilinen "rm -rf /", "dd ... of=/dev/sda", zincirleme
(``;``, ``&&``, ``|``) gibi saldırıları kapsar.
"""

from __future__ import annotations

import re
import shlex

# Kabuk zincirleme/yönlendirme karakterleri: bunlara izin verilirse denylist
# kolayca atlatılabilir (örn. "ls; rm -rf ~" hiçbir DANGEROUS_PATTERNS'e
# uymaz ama shell=True ile ikinci komutu da çalıştırır). Biz shell=True zaten
# kullanmıyoruz (to_argv), ama bu kontrol yine de erken ve net bir ret verir.
SHELL_METACHARACTERS = re.compile(r"[;&|`\n<>]|\$\(")

_ROOT_LIKE_PATHS = {"/", "~", "$home", "/*", "~/*", "./*", "."}

DANGEROUS_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bdd\s+.*of=/dev/[sh]d"), "disk imajlama/üzerine yazma"),
    (re.compile(r"\bmkfs\b"), "disk biçimlendirme"),
    (re.compile(r">\s*/etc/(passwd|shadow)\b"), "kritik sistem dosyasının üzerine yazma"),
    (re.compile(r"\bchmod\s+-R?\s*777\s+/"), "kök dizin izinlerini açma"),
    (re.compile(r":\(\)\s*\{\s*:\|:\s*&\s*\}\s*;"), "fork bomb"),
    (re.compile(r"\b(shutdown|reboot|poweroff|halt)\b"), "sistemi kapatma/yeniden başlatma"),
]


def _is_recursive_force_delete(tokens: list[str]) -> str | None:
    """tokens 'rm' (opsiyonel 'sudo' önekiyle) + -r/-f + kök-benzeri hedef içeriyorsa gerekçe döndürür."""
    idx = 0
    if tokens and tokens[0] == "sudo":
        idx = 1
    if idx >= len(tokens) or tokens[idx] != "rm":
        return None

    rest = tokens[idx + 1:]
    flags = [t for t in rest if t.startswith("-")]
    targets = [t for t in rest if not t.startswith("-")]
    combined_flags = "".join(flags)
    has_recursive = "r" in combined_flags or "R" in combined_flags or "--recursive" in flags
    has_force = "f" in combined_flags or "--force" in flags
    if not (has_recursive and has_force):
        return None

    for target in targets:
        normalized = target.strip().lower()
        if normalized in _ROOT_LIKE_PATHS or re.fullmatch(r"/+", normalized):
            return "kök/ev dizinini zorla ve özyinelemeli silme"
    return None


def check_command_safety(command: str) -> tuple[bool, str | None]:
    """Komutu bilinen tehlikeli kalıplara karşı denetler.

    Dönüş: (güvenli_mi, ret_gerekçesi). Güvenliyse ikinci eleman None olur.
    """
    if not command or not command.strip():
        return False, "boş komut"
    if SHELL_METACHARACTERS.search(command):
        return False, "kabuk zincirleme/yönlendirme karakteri (;, |, &, `, $(), >, <)"

    tokens = to_argv(command)
    if tokens is None:
        return False, "komut ayrıştırılamadı (eşleşmeyen tırnak vb.)"
    if not tokens:
        return False, "boş komut"

    rm_reason = _is_recursive_force_delete(tokens)
    if rm_reason:
        return False, rm_reason

    for pattern, reason in DANGEROUS_PATTERNS:
        if pattern.search(command):
            return False, reason
    return True, None


def to_argv(command: str) -> list[str] | None:
    """Komutu shell=True kullanmadan çalıştırmak için argv listesine çevirir."""
    try:
        return shlex.split(command)
    except ValueError:
        return None
