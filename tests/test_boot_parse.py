"""Açılış süresi ayrıştırma regresyon testleri.

TECHNICAL_AUDIT.md Kol 1 bulgusu: 60 sn'yi aşan açılışlarda systemd toplamı
"1min 7.311s" biçiminde yazar; eski regex bunu ayrıştıramayıp yanlış değere
düşüyordu. Bu testler o hatanın geri gelmesini engeller.
"""

import unittest

from pardus_healer.checks.boot import BootTimeCheck


class BootParseTests(unittest.TestCase):
    def test_saniye_bicimi(self):
        text = "Startup finished in 4.2s (kernel) + 12.6s (userspace) = 16.8s"
        self.assertAlmostEqual(BootTimeCheck._parse_total(text), 16.8)

    def test_dakika_bicimi(self):
        # Denetimdeki birebir senaryo: 67.3 sn'lik açılış "7.3 sn" sanılıyordu.
        text = "Startup finished in 5.1s (kernel) + 1min 2.211s (userspace) = 1min 7.311s"
        self.assertAlmostEqual(BootTimeCheck._parse_total(text), 67.311)

    def test_saat_bicimi(self):
        self.assertAlmostEqual(
            BootTimeCheck._parse_duration("2h 3min 4.5s"), 7384.5)

    def test_cok_satirli_cikti(self):
        text = (
            "Startup finished in 3.0s (firmware) + 2.0s (loader) + "
            "4.2s (kernel) + 1min 5.0s (userspace) = 1min 14.2s\n"
            "graphical.target reached after 1min 4.0s in userspace"
        )
        self.assertAlmostEqual(BootTimeCheck._parse_total(text), 74.2)

    def test_ayristirilamayan_metin(self):
        self.assertIsNone(BootTimeCheck._parse_total("anlamsız çıktı"))

    def test_esikler(self):
        # FAIL_SEC eşiği eskiden hiç kullanılmıyordu (her ikisi de warn'dı).
        self.assertGreater(BootTimeCheck.FAIL_SEC, BootTimeCheck.WARN_SEC)


if __name__ == "__main__":
    unittest.main()
