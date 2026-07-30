"""Onarım komutlarını çalıştıran ortak yardımcı.

``pkexec ...`` biçimindeki bir ``Fix.command``'ı ``shell=False`` ile
çalıştırıp çıktısını satır satır (ana GTK thread'ine ``GLib.idle_add`` ile)
akıtan mantık; eskiden ``ui/card.py`` ve ``ui/app.py`` içindeki iki ayrı
worker'da neredeyse birebir kopyalanmıştı (bkz. TECHNICAL_AUDIT.md Kol 3,
FIX_DECISION_MATRIX.md P2 madde 21). Üç kopyadan biri güncellenip
diğerlerinin unutulması riskini (tam da card.py'deki pkexec-silme hatasının
başına geldiği gibi) ortadan kaldırmak için tek yerde toplanmıştır.
"""

from __future__ import annotations

import shlex
import subprocess

from gi.repository import GLib


def run_fix_command(command: str, log_cb) -> int:
    """Bir onarım komutunu (zaten kullanıcı oturumunda, pkexec KORUNARAK)
    çalıştırır; çıktıyı satır satır ``log_cb``'ye yollar.

    ``log_cb`` ana GTK thread'inde çağrılmalıdır — bu fonksiyon ``GLib.idle_add``
    ile bunu garanti eder, kendisi ise (subprocess I/O nedeniyle) bir arka
    plan thread'inden çağrılmak üzere tasarlanmıştır.

    Dönüş: alt sürecin çıkış kodu; komut boşsa/ayrıştırılamazsa ya da
    başlatılamazsa -1.
    """
    try:
        cmd_list = shlex.split(command)
    except ValueError as exc:
        GLib.idle_add(log_cb, f"Hata: Komut ayrıştırılamadı ({exc})\n")
        return -1
    if not cmd_list:
        GLib.idle_add(log_cb, "Hata: Boş komut\n")
        return -1

    try:
        proc = subprocess.Popen(
            cmd_list,
            shell=False,  # Command Injection koruması - shell=True YASAK
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        assert proc.stdout is not None
        for line in iter(proc.stdout.readline, ""):
            if line:
                GLib.idle_add(log_cb, line.rstrip())
        proc.stdout.close()
        proc.wait()
        GLib.idle_add(
            log_cb, f"İşlem tamamlandı (çıkış kodu: {proc.returncode})\n"
        )
        return proc.returncode
    except Exception as exc:
        GLib.idle_add(log_cb, f"Hata: {exc}\n")
        return -1
