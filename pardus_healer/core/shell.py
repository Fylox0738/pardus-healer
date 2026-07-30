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

    args : liste (tercih edilen). String verilirse ``shlex.split`` ile
    argv listesine çevrilir — ``shell=True`` HİÇBİR koşulda kullanılmaz
    (geçmişte bir komut enjeksiyonu açığı tam bu yüzden oluşmuştu,
    bkz. CLAUDE.md / commit 4122204).
    Hiçbir zaman exception fırlatmaz; her durumu CmdResult ile bildirir.
    """
    if isinstance(args, str):
        import shlex

        try:
            args = shlex.split(args)
        except ValueError:
            return CmdResult(-1, "", "komut ayrıştırılamadı", ok=False)
        if not args:
            return CmdResult(-1, "", "boş komut", ok=False)
    env = dict(os.environ)
    if env_c_locale:
        # Çıktı ayrıştırması dilden bağımsız olsun (İngilizce anahtar kelimeler).
        env["LANG"] = "C"
        env["LC_ALL"] = "C"

    try:
        proc = subprocess.run(
            args,
            shell=False,
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


def write_file_atomic(path: str, data: str) -> bool:
    """Bir dosyayı atomik olarak yazar (geçici dosya + os.replace).

    Yazma sırasında kesilme (çökme/elektrik kesintisi) veya eşzamanlı bir
    okuyucunun yarım/bozuk veri görmesi riskini ortadan kaldırır.
    """
    import tempfile

    directory = os.path.dirname(path) or "."
    try:
        os.makedirs(directory, exist_ok=True)
    except OSError:
        return False
    try:
        fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".tmp-", suffix=".part")
    except OSError:
        return False
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, path)
        return True
    except OSError:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        return False


def run_fix_as_root(command: str, timeout: int = 60) -> CmdResult:
    """Zaten root olarak çalışan bir süreçte (daemon/swarm) bir Fix komutunu
    çalıştırır. ``pkexec`` öneki varsa güvenle çıkarılır (zaten root'uz;
    bırakılırsa parola penceresi açmaya çalışıp arka planda takılır kalır).

    Bu mantık önceden daemon.py ve swarm/server.py'de birbirinden bağımsız
    olarak kopyalanmıştı (bkz. TECHNICAL_AUDIT.md). Kartın (ui/card.py)
    "Düzelt" butonu BUNU kullanmaz — o normal kullanıcı oturumunda çalışır
    ve pkexec'i BİLEREK korur.
    """
    import shlex

    cmd_list = shlex.split(command)
    if cmd_list and cmd_list[0] == "pkexec":
        cmd_list = cmd_list[1:]
    if not cmd_list:
        return CmdResult(-1, "", "boş komut", ok=False)
    return run(cmd_list, timeout=timeout)
