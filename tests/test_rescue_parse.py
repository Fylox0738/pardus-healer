"""Healer Rescue apt geçmişi ayrıştırma testleri.

 Kol 2 bulgusu: kurtarma aracı temel sistem paketlerini
(çekirdek, systemd, grub...) geri alma listesine ekleyebiliyor ve apt
geçmişindeki serbest metin, komut satırına süzülmeden aktarılıyordu.
Bu testler koruma listesi + paket adı regex filtresinin çalıştığını doğrular.
"""

import os
import tempfile
import unittest

import healer_rescue

HISTORY = """\
Start-Date: 2026-07-28  09:00:00
Commandline: apt-get install -y vlc
Install: vlc:amd64 (3.0.20)
End-Date: 2026-07-28  09:01:00

Start-Date: 2026-07-28  10:00:00
Commandline: apt install linux-image-6.1.0-18-amd64 htop bad;pkg
Install: linux-image-6.1.0-18-amd64:amd64
End-Date: 2026-07-28  10:02:00

Start-Date: 2026-07-28  11:00:00
Commandline: apt remove nano
Remove: nano:amd64 (7.2)
End-Date: 2026-07-28  11:00:30
"""


class RescueParseTests(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".log")
        os.close(fd)
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write(HISTORY)
        self.actions = healer_rescue.parse_history(self.path)

    def tearDown(self):
        os.remove(self.path)

    def test_en_yeni_islem_basta(self):
        self.assertEqual(self.actions[0]["revert_action"], "install")
        self.assertEqual(self.actions[0]["packages"], ["nano"])

    def test_kurulum_geri_alma_remove_olur(self):
        vlc = [a for a in self.actions if a["packages"] == ["vlc"]]
        self.assertEqual(len(vlc), 1)
        self.assertEqual(vlc[0]["revert_action"], "remove")

    def test_temel_paket_korunur(self):
        # linux-image asla "remove" önerisine girmemeli.
        for action in self.actions:
            for pkg in action["packages"]:
                self.assertFalse(
                    pkg.startswith("linux-image"),
                    f"Korunan paket geri alma listesine sızdı: {pkg}",
                )

    def test_enjeksiyon_tokeni_suzulur(self):
        # "bad;pkg" paket adı regex'ine uymaz, argv'ye asla girmemeli.
        for action in self.actions:
            for pkg in action["packages"]:
                self.assertNotIn(";", pkg)

    def test_htop_korunmadan_kalir(self):
        # Aynı işlemdeki korunmayan paket listede kalmalı.
        htop = [a for a in self.actions if "htop" in a["packages"]]
        self.assertEqual(len(htop), 1)
        self.assertEqual(htop[0]["packages"], ["htop"])

    def test_dosya_yoksa_bos_liste(self):
        self.assertEqual(
            healer_rescue.parse_history("/yok/boyle/bir/dosya.log"), [])

    def test_korunan_onekler(self):
        self.assertTrue(healer_rescue._is_protected("linux-image-6.1"))
        self.assertTrue(healer_rescue._is_protected("systemd"))
        self.assertTrue(healer_rescue._is_protected("grub-efi-amd64"))
        self.assertFalse(healer_rescue._is_protected("vlc"))


if __name__ == "__main__":
    unittest.main()
