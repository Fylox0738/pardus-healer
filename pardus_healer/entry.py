"""Ortak giriş yönlendiricisi.

Argüman verilmişse (örn. --cli, --html) komut satırı modunu; hiç argüman
yoksa GTK arayüzünü başlatır.
"""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:]) if argv is None else argv
    if argv:
        from .cli import run_cli
        return run_cli(argv)
    # Argümansız → grafik arayüz
    from .ui.main_entry import launch
    launch()
    return 0
