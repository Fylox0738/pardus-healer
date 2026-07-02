"""`python -m pardus_healer [--cli ...]` ile çalıştırma desteği."""

import sys

from .entry import main

if __name__ == "__main__":
    sys.exit(main())
