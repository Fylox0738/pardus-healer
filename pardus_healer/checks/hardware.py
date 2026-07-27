"""Donanım sağlığı kontrolleri: pil aşınması."""

from __future__ import annotations

import glob
import os

from ..core.check import BaseCheck
from ..core.models import Metric
from ..core.shell import read_file


class BatteryHealthCheck(BaseCheck):
    id = "battery"
    title = "Pil Sağlığı"
    icon = "🔋"
    category = "Donanım"
    weight = 0.6

    def run(self):
        bats = sorted(glob.glob("/sys/class/power_supply/BAT*"))
        if not bats:
            return self.info(
                "Pil bulunamadı.",
                detail="Masaüstü sistem ya da pil algılanmadı.",
            )
        bat = bats[0]

        design = self._read_int(bat, "energy_full_design") or self._read_int(
            bat, "charge_full_design"
        )
        full = self._read_int(bat, "energy_full") or self._read_int(
            bat, "charge_full"
        )
        capacity = self._read_int(bat, "capacity")  # anlık şarj %
        status = (read_file(os.path.join(bat, "status")) or "").strip()

        if not design or not full:
            # Aşınma hesaplanamıyor; yine de anlık durumu bildir.
            if capacity is not None:
                return self.info(
                    f"Pil şarjı: %{capacity} ({status or 'bilinmiyor'})",
                    detail="Pil aşınma verisi bu cihazda mevcut değil.",
                )
            return self.info("Pil durumu okunamadı.")

        health = int(full / design * 100)
        metric = Metric(health, "%", percent=min(health, 100))
        base = (
            f"Pil sağlığı %{health} · anlık şarj "
            f"%{capacity if capacity is not None else '?'} ({status or '—'})."
        )
        if health < 60:
            return self.warn(
                f"Pil belirgin aşınmış. (Sağlık %{health})",
                detail=base,
                metric=metric,
                root_cause="Pil, tasarım kapasitesinin önemli bir kısmını "
                "kaybetmiş.",
                recommendation="Pilin değiştirilmesi düşünülebilir.",
            )
        if health < 80:
            return self.warn(
                f"Pil aşınması artıyor. (Sağlık %{health})",
                detail=base,
                metric=metric,
            )
        return self.ok(f"Pil sağlığı iyi. (%{health})", detail=base, metric=metric)

    @staticmethod
    def _read_int(base: str, name: str) -> int | None:
        text = read_file(os.path.join(base, name))
        if text is None:
            return None
        try:
            return int(text.strip())
        except ValueError:
            return None

class SmartDiskCheck(BaseCheck):
    id = "smart_disk"
    title = "S.M.A.R.T. Disk Sağlığı"
    icon = "💽"
    category = "Donanım"
    weight = 1.0

    def run(self):
        import shutil
        import subprocess
        
        if not shutil.which("smartctl"):
            return self.info(
                "Disk sağlığı okunamadı (smartctl eksik).",
                detail="Erken donanım uyarısı için smartmontools paketini kurun."
            )
            
        try:
            # Sadece kök (root) veya sudo izinleriyle çalışır, 
            # pkexec istemeyiz çünkü tarama anında parola sorsun istemiyoruz.
            # Eger root degilse hata verir, biz bunu algılayıp pass geçebiliriz.
            result = subprocess.run(["smartctl", "-H", "/dev/sda"], capture_output=True, text=True, timeout=2)
            out = result.stdout
            
            if result.returncode == 0 or "PASSED" in out:
                return self.ok("S.M.A.R.T. disk sağlığı: PASSED (İyi durumda)")
            elif "FAILED" in out:
                return self.fail(
                    "S.M.A.R.T. Uyarısı: Disk arızası tespit edildi!",
                    detail="Diskiniz fiziksel olarak ömrünü dolduruyor olabilir.",
                    root_cause="Donanım (Disk) yaşlanması veya fiziksel hasar.",
                    recommendation="ACİLEN VERİLERİNİZİ YEDEKLEYİN. Diski yenisiyle değiştirin."
                )
            else:
                return self.info("Disk sağlığı verisi root yetkisi gerektirebilir.")
        except Exception as e:
            return self.info(f"Disk sağlığı taraması başarısız: {e}")
