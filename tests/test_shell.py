"""core/shell.py güvenli komut çalıştırma testleri.

Projenin en katı kuralı: shell=True HİÇBİR yerde kullanılmaz (geçmişte bir
komut enjeksiyonu açığı bu yüzden oluşmuştu,
string girdinin bile kabuk yorumlamasına gitmediğini doğrular.
"""

import os
import sys
import tempfile
import unittest

from pardus_healer.core import shell


class RunTests(unittest.TestCase):
    def test_liste_komut_calisir(self):
        res = shell.run([sys.executable, "-c", "print('merhaba')"], timeout=30)
        self.assertTrue(res.ok)
        self.assertIn("merhaba", res.stdout)

    def test_string_kabuk_yorumlamasina_gitmez(self):
        # "&&" bir kabuk operatörü olarak İŞLENMEMELİ; komut bulunamayınca
        # ikinci komut da asla çalışmamalı.
        res = shell.run("olmayan-komut-xyz && echo sizinti")
        self.assertFalse(res.ok)
        self.assertNotIn("sizinti", res.stdout)

    def test_bos_string_reddedilir(self):
        self.assertFalse(shell.run("").ok)

    def test_bulunamayan_komut(self):
        res = shell.run(["kesinlikle-olmayan-komut-xyz"])
        self.assertFalse(res.ok)
        self.assertTrue(res.not_found)


class RunFixAsRootTests(unittest.TestCase):
    def test_pkexec_oneki_cikarilir(self):
        # Root süreçte (daemon/swarm) pkexec bırakılırsa parola penceresi
        # açmaya çalışıp takılı kalır — önek güvenle çıkarılmalı.
        captured = {}
        orig = shell.run

        def sahte_run(args, timeout=60, env_c_locale=True):
            captured["args"] = args
            return shell.CmdResult(0, "", "", ok=True)

        shell.run = sahte_run
        try:
            res = shell.run_fix_as_root("pkexec apt-get -f install")
        finally:
            shell.run = orig
        self.assertEqual(captured["args"], ["apt-get", "-f", "install"])
        self.assertTrue(res.ok)

    def test_bos_komut_reddedilir(self):
        self.assertFalse(shell.run_fix_as_root("").ok)
        self.assertFalse(shell.run_fix_as_root("pkexec").ok)


class AtomicWriteTests(unittest.TestCase):
    def test_yaz_ve_degistir(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "alt", "ayarlar.json")
            self.assertTrue(shell.write_file_atomic(path, "ilk"))
            self.assertTrue(shell.write_file_atomic(path, "ikinci"))
            self.assertEqual(shell.read_file(path), "ikinci")
            artik = [f for f in os.listdir(os.path.dirname(path))
                     if f.startswith(".tmp-")]
            self.assertEqual(artik, [], "geçici dosya artığı kalmamalı")

    def test_olmayan_dosya_okuma_none(self):
        self.assertIsNone(
            shell.read_file(os.path.join(
                tempfile.gettempdir(), "yok-boyle-dosya-xyz.json")))


if __name__ == "__main__":
    unittest.main()
