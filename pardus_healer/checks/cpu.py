"""CPU yük ve sıcaklık kontrolleri."""

from __future__ import annotations

import os

from ..core.check import BaseCheck
from ..core.models import Metric
from ..core.shell import read_file, run, which


class CpuLoadCheck(BaseCheck):
    id = "cpu_load"
    title = "CPU Yükü"
    icon = "⚙️"
    category = "Donanım"
    weight = 0.8

    def run(self):
        try:
            load1, load5, load15 = os.getloadavg()
        except (OSError, AttributeError):
            return self.unknown("Yük ortalaması bu ortamda okunamadı.")

        cpus = os.cpu_count() or 1
        # Çekirdek başına normalize edilmiş yük.
        per_core = load1 / cpus
        pct = min(int(per_core * 100), 999)
        metric = Metric(round(per_core * 100, 1), "%", percent=min(pct, 100))
        base = (
            f"1/5/15 dk yük: {load1:.2f} / {load5:.2f} / {load15:.2f} "
            f"({cpus} çekirdek)."
        )
        if per_core >= 1.5:
            return self.fail(
                f"CPU aşırı yüklü! (çekirdek başına %{pct})",
                detail=base,
                metric=metric,
                root_cause="Çalışan bir süreç işlemciyi doyuruyor olabilir.",
                recommendation="Sistem İzleyici ile en çok CPU kullanan "
                "süreci bulun.",
            )
        if per_core >= 0.9:
            return self.warn(
                f"CPU yükü yüksek. (çekirdek başına %{pct})",
                detail=base,
                metric=metric,
            )
        return self.ok(f"CPU yükü normal. (çekirdek başına %{pct})",
                       detail=base, metric=metric)


class CpuTempCheck(BaseCheck):
    id = "cpu_temp"
    title = "CPU Sıcaklığı"
    icon = "🌡️"
    category = "Donanım"
    weight = 1.0

    def run(self):
        temp = self._read_temp()
        if temp is None:
            return self.info(
                "Sıcaklık sensörü bulunamadı.",
                detail="Sanal makinelerde donanım sensörü bulunmayabilir.",
            )
        metric = Metric(round(temp, 1), "°C", percent=min(int(temp / 100 * 100), 100))
        msg = f"Sıcaklık: {temp:.1f} °C"
        if temp > 85:
            return self.fail(
                f"CPU aşırı ısınıyor! ({temp:.0f} °C)",
                detail=msg,
                metric=metric,
                root_cause="Yetersiz soğutma, tozlu fan ya da yüksek yük "
                "sıcaklığı artırıyor olabilir.",
                recommendation="Havalandırmayı ve fanları kontrol edin; "
                "yükü azaltın.",
            )
        if temp > 65:
            return self.warn(
                f"CPU sıcaklığı yüksek. ({temp:.0f} °C)",
                detail=msg,
                metric=metric,
            )
        return self.ok(f"CPU sıcaklığı normal. ({temp:.0f} °C)",
                       detail=msg, metric=metric)

    # "sensors" çıktısında yalnızca CPU'ya ait çipleri (Package/Tdie/Core)
    # dikkate alıyoruz. Eskiden ÇIKTIDAKİ TÜM "°C" değerlerinin maksimumu
    # alınıyordu — bu, sistemde nvme/GPU/anakart sıcaklık sensörü varsa
    # "CPU sıcaklığı" olarak yanlış bir bileşenin (ör. ısınan bir SSD/GPU)
    # değerini raporlayabiliyordu (bkz. TECHNICAL_AUDIT.md).
    _CPU_CHIP_HINTS = ("coretemp", "k10temp", "zenpower", "cpu_thermal")
    _CPU_LABEL_HINTS = ("package", "tdie", "tctl", "core")

    # ---- sıcaklık okuma stratejileri ----
    def _read_temp(self) -> float | None:
        return self._from_sensors() or self._from_sysfs()

    def _from_sensors(self) -> float | None:
        if not which("sensors"):
            return None
        res = run(["sensors"], timeout=10)
        if not res.ok:
            return None

        best = None
        is_cpu_chip = False
        for raw in res.stdout.splitlines():
            line = raw.strip()
            if not line:
                is_cpu_chip = False
                continue
            if ":" not in line:
                # yeni çip başlığı, ör. "coretemp-isa-0000", "nvme-pci-0100"
                is_cpu_chip = any(h in line.lower() for h in self._CPU_CHIP_HINTS)
                continue
            if not is_cpu_chip or "°C" not in line:
                continue
            label = line.split(":", 1)[0].strip().lower()
            if not any(h in label for h in self._CPU_LABEL_HINTS):
                continue
            for tok in line.split():
                if "°C" in tok:
                    try:
                        val = float(tok.replace("+", "").replace("°C", ""))
                    except ValueError:
                        continue
                    if 0 < val < 150:
                        best = val if best is None else max(best, val)
        return best

    def _from_sysfs(self) -> float | None:
        text = read_file("/sys/class/thermal/thermal_zone0/temp")
        if not text:
            return None
        try:
            return int(text.strip()) / 1000.0
        except ValueError:
            return None
