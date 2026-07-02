"""Kabuk / komut çalıştırma yardımcıları.

Tüm alt süreç çağrıları buradan geçer; böylece zaman aşımı, hata yakalama
ve platform kontrolü tek yerde toplanır.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass


IS_LINUX = os.name == "posix"


@dataclass
class CmdResult:
    returncode: int
    stdout: str
    stderr: str
    ok: bool
    timed_out: bool = False
    not_found: bool = False

    @property
    def out(self) -> str:
        """stdout + stderr birleşik, boşlukları kırpılmış."""
        return (self.stdout + self.stderr).strip()


def which(cmd: str) -> bool:
    """Komut PATH'te var mı?"""
    return shutil.which(cmd) is not None


def run(
    args,
    timeout: int = 20,
    env_c_locale: bool = True,
) -> CmdResult:
    """Bir komutu güvenli biçimde çalıştırır.

    args : liste (tercih edilen, shell=False) veya string (shell=True).
    Hiçbir zaman exception fırlatmaz; her durumu CmdResult ile bildirir.
    """
    shell = isinstance(args, str)
    env = dict(os.environ)
    if env_c_locale:
        # Çıktı ayrıştırması dilden bağımsız olsun (İngilizce anahtar kelimeler).
        env["LANG"] = "C"
        env["LC_ALL"] = "C"

    try:
        proc = subprocess.run(
            args,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        return CmdResult(
            returncode=proc.returncode,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            ok=proc.returncode == 0,
        )
    except FileNotFoundError:
        return CmdResult(127, "", "komut bulunamadı", ok=False, not_found=True)
    except subprocess.TimeoutExpired:
        return CmdResult(-1, "", "zaman aşımı", ok=False, timed_out=True)
    except Exception as exc:  # beklenmedik her şey
        return CmdResult(-1, "", str(exc), ok=False)


def read_file(path: str) -> str | None:
    """Bir dosyayı güvenle okur; yoksa/okunamazsa None döner."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return None
