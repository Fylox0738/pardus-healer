"""Sistem kimlik bilgilerini toplar (dashboard başlığı ve rapor için).

Skora dahil edilmez; yalnızca bağlam sağlar. Tüm okumalar güvenlidir ve
Linux dışı ortamlarda makul varsayılanlar döndürür.
"""

from __future__ import annotations

import os
import platform
import socket
from dataclasses import dataclass

from .shell import read_file


@dataclass
class SystemInfo:
    distro: str
    kernel: str
    hostname: str
    cpu_model: str
    cpu_cores: int
    ram_total_gb: float
    uptime: str

    def as_pairs(self) -> list[tuple[str, str]]:
        return [
            ("Dağıtım", self.distro),
            ("Çekirdek", self.kernel),
            ("Bilgisayar", self.hostname),
            ("İşlemci", f"{self.cpu_model} ({self.cpu_cores} çekirdek)"),
            ("Bellek", f"{self.ram_total_gb:.1f} GB"),
            ("Çalışma süresi", self.uptime),
        ]


def _distro() -> str:
    text = read_file("/etc/os-release")
    if text:
        fields = {}
        for line in text.splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                fields[k] = v.strip().strip('"')
        name = fields.get("PRETTY_NAME") or fields.get("NAME")
        if name:
            return name
    return platform.system() or "Bilinmiyor"


def _cpu_model() -> str:
    text = read_file("/proc/cpuinfo")
    if text:
        for line in text.splitlines():
            if line.lower().startswith("model name"):
                return line.split(":", 1)[1].strip()
    return platform.processor() or platform.machine() or "Bilinmiyor"


def _ram_total_gb() -> float:
    text = read_file("/proc/meminfo")
    if text:
        for line in text.splitlines():
            if line.startswith("MemTotal:"):
                try:
                    return int(line.split()[1]) / (1024 * 1024)
                except (ValueError, IndexError):
                    pass
    return 0.0


def _uptime() -> str:
    text = read_file("/proc/uptime")
    if not text:
        return "Bilinmiyor"
    try:
        seconds = int(float(text.split()[0]))
    except (ValueError, IndexError):
        return "Bilinmiyor"
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    parts = []
    if days:
        parts.append(f"{days} gün")
    if hours:
        parts.append(f"{hours} saat")
    parts.append(f"{minutes} dk")
    return " ".join(parts)


def collect() -> SystemInfo:
    return SystemInfo(
        distro=_distro(),
        kernel=platform.release() or "Bilinmiyor",
        hostname=socket.gethostname() or "Bilinmiyor",
        cpu_model=_cpu_model(),
        cpu_cores=os.cpu_count() or 1,
        ram_total_gb=_ram_total_gb(),
        uptime=_uptime(),
    )
