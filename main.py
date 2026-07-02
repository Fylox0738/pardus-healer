#!/usr/bin/env python3
"""Pardus Healer — geriye dönük uyumlu başlatıcı.

Uygulama artık ``pardus_healer`` paketi altında modüler biçimde
yapılandırılmıştır. Bu dosya yalnızca eski çalıştırma alışkanlıklarını
(python3 main.py) korumak için ince bir sarmalayıcıdır.

    python3 main.py           # grafik arayüz
    python3 main.py --cli     # komut satırı tanı
"""

import sys

from pardus_healer.entry import main

if __name__ == "__main__":
    sys.exit(main())
