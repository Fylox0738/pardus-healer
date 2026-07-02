"""Canlı sistem örnekleyici — CPU / RAM / Disk anlık kullanımı.

Dashboard'daki gerçek zamanlı izleme çubukları bunu ~saniyede bir çağırır.
CPU kullanımı /proc/stat'tan iki örnek arasındaki farkla hesaplanır; bu yüzden
sınıf, önceki örneği hatırlar. Linux dışı ortamda tüm değerler None döner.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from .shell import read_file


@dataclass
class LiveSample:
    cpu_percent: Optional[float]
    ram_percent: Optional[float]
    disk_percent: Optional[float]


class LiveSampler:
    def __init__(self):
        self._prev_total: Optional[int] = None
        self._prev_idle: Optional[int] = None

    def sample(self) -> LiveSample:
        return LiveSample(
            cpu_percent=self._cpu(),
            ram_percent=self._ram(),
            disk_percent=self._disk(),
        )

    def _cpu(self) -> Optional[float]:
        text = read_file("/proc/stat")
        if not text:
            return None
        first = text.splitlines()[0]
        if not first.startswith("cpu"):
            return None
        try:
            fields = [int(x) for x in first.split()[1:]]
        except ValueError:
            return None
        idle = fields[3] + (fields[4] if len(fields) > 4 else 0)
        total = sum(fields)
        if self._prev_total is None:
            self._prev_total, self._prev_idle = total, idle
            return None  # ilk örnekte fark hesaplanamaz
        dt = total - self._prev_total
        di = idle - self._prev_idle
        self._prev_total, self._prev_idle = total, idle
        if dt <= 0:
            return None
        return max(0.0, min(100.0, (1 - di / dt) * 100))

    def _ram(self) -> Optional[float]:
        text = read_file("/proc/meminfo")
        if not text:
            return None
        total = avail = None
        for line in text.splitlines():
            if line.startswith("MemTotal:"):
                total = int(line.split()[1])
            elif line.startswith("MemAvailable:"):
                avail = int(line.split()[1])
            if total is not None and avail is not None:
                break
        if not total or avail is None:
            return None
        return (total - avail) / total * 100

    def _disk(self) -> Optional[float]:
        try:
            st = os.statvfs("/")
        except (OSError, AttributeError):
            return None
        total = st.f_blocks
        if total == 0:
            return None
        used = total - st.f_bfree
        return used / total * 100
