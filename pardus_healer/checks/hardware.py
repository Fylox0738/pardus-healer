"""Donanım sağlığı kontrolleri: pil aşınması."""

from __future__ import annotations

import glob
import os

from ..core.check import BaseCheck
from ..core.models import Metric
from ..core.shell import read_file, run, which


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
        # Eskiden yalnızca "/dev/nvme0n1" veya "/dev/sda" sabit kodlanmıştı —
        # sanal makinelerde (virtio: /dev/vda), birden fazla diskli
        # sistemlerde ya da LVM üzerinde bu iki yoldan hiçbiri var olmayabilir,
        # kontrol de sessizce yanlış/eksik sonuç veriyordu.
        # Artık gerçek fiziksel diskler lsblk ile
        # keşfediliyor ve proje genelindeki ortak shell yardımcıları
        # (which/run) kullanılıyor.
        if not which("smartctl"):
            return self.info(
                "Disk sağlığı okunamadı (smartctl eksik).",
                detail="Erken donanım uyarısı için smartmontools paketini kurun."
            )

        disks = self._physical_disks()
        if not disks:
            return self.info(
                "Fiziksel disk bulunamadı.",
                detail="Sanal makine/konteyner ortamında S.M.A.R.T. verisi "
                "genelde erişilemez.",
            )

        failed = []
        checked = 0
        for disk in disks:
            res = run(["smartctl", "-H", disk], timeout=10)
            out = res.out
            if "FAILED" in out:
                failed.append(disk)
                checked += 1
            elif res.ok or "PASSED" in out:
                checked += 1
            # Ne PASSED ne FAILED (izin yetersiz / sanal disk) → bu diski
            # sessizce atla, yanlış-pozitif üretme.

        if failed:
            return self.fail(
                f"S.M.A.R.T. Uyarısı: {', '.join(failed)} disk(in)de arıza tespit edildi!",
                detail="Diskiniz fiziksel olarak ömrünü dolduruyor olabilir.",
                root_cause="Donanım (Disk) yaşlanması veya fiziksel hasar.",
                recommendation="ACİLEN VERİLERİNİZİ YEDEKLEYİN. Diski yenisiyle değiştirin."
            )
        if checked:
            return self.ok(
                f"S.M.A.R.T. disk sağlığı: PASSED ({checked} disk kontrol edildi)."
            )
        return self.info(
            "Disk sağlığı verisi alınamadı.",
            detail="Root yetkisi gerekiyor olabilir ya da sanal disk "
            "S.M.A.R.T. desteklemiyor.",
        )

    @staticmethod
    def _physical_disks() -> list[str]:
        if not which("lsblk"):
            return [
                p for p in ("/dev/sda", "/dev/nvme0n1", "/dev/vda")
                if os.path.exists(p)
            ]
        res = run(["lsblk", "-d", "-n", "-o", "NAME,TYPE"], timeout=10)
        if not res.ok:
            return []
        disks = []
        for line in res.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "disk":
                disks.append(f"/dev/{parts[0]}")
        return disks
