"""Tanı modülleri paketi.

Her modül ``BaseCheck``'ten türeyen bir veya birden çok sınıf içerir.
``ALL_CHECK_CLASSES`` motor tarafından otomatik olarak toplanır; buraya yeni
bir sınıf eklemek onu tüm arayüze/skora dahil etmeye yeter.
"""

from __future__ import annotations

from .network import InternetCheck, DnsCheck
from .apt import AptHealthCheck
from .packages import BrokenPackagesCheck
from .updates import UpdatesCheck, SecurityUpdatesCheck
from .disk import DiskSpaceCheck
from .memory import RamUsageCheck, SwapUsageCheck
from .cpu import CpuTempCheck, CpuLoadCheck
from .services import FailedServicesCheck
from .security import FirewallCheck, PendingRebootCheck
from .security_extra import (
    OpenPortsCheck,
    SshHardeningCheck,
    UnattendedUpgradesCheck,
)
from .hardware import BatteryHealthCheck, SmartDiskCheck
from .maintenance import CacheCleanupCheck
from .boot import BootTimeCheck
from .logs import JournalErrorsCheck
from .esignature import ESignatureCheck
from .printer import PrinterCheck
from .bootloader import BootloaderCheck

# Kartların/raporun görüneceği sıra buradaki sıradır.
ALL_CHECK_CLASSES = [
    InternetCheck,
    DnsCheck,
    AptHealthCheck,
    BrokenPackagesCheck,
    UpdatesCheck,
    SecurityUpdatesCheck,
    DiskSpaceCheck,
    RamUsageCheck,
    SwapUsageCheck,
    CpuLoadCheck,
    CpuTempCheck,
    BatteryHealthCheck,
    SmartDiskCheck,
    FailedServicesCheck,
    FirewallCheck,
    PendingRebootCheck,
    OpenPortsCheck,
    SshHardeningCheck,
    UnattendedUpgradesCheck,
    CacheCleanupCheck,
    BootTimeCheck,
    JournalErrorsCheck,
    PrinterCheck,
    BootloaderCheck,
    ESignatureCheck,
]
