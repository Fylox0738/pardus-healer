#!/usr/bin/env python3
"""Pardus Healer başlatıcı.

Kullanım:
    python3 run.py            # grafik arayüz
    python3 run.py --cli      # komut satırı tanı
    python3 run.py --cli --html rapor.html --json rapor.json
"""

import sys

from pardus_healer.entry import main

if __name__ == "__main__":
    sys.exit(main())
