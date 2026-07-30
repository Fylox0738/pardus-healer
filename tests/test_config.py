"""Ayar saklama katmanı testleri.

 kuralı: ayar dosyası bozuk/yok olsa bile uygulama ASLA çökmemeli,
varsayılanlara dönmeli. Yazma atomik olmalı (yarım dosya kalmamalı).
"""

import os
import tempfile
import unittest


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self._eski = os.environ.get("XDG_CONFIG_HOME")
        self._td = tempfile.TemporaryDirectory()
        os.environ["XDG_CONFIG_HOME"] = self._td.name

    def tearDown(self):
        if self._eski is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self._eski
        self._td.cleanup()

    def test_kaydet_ve_yeniden_yukle(self):
        from pardus_healer.config import Config

        c = Config()
        self.assertFalse(c.dark_mode)  # varsayılan
        c.dark_mode = True             # setter save() tetikler
        c2 = Config()                  # taze örnek diskten okur
        self.assertTrue(c2.dark_mode)

    def test_bozuk_dosya_cokertmez(self):
        path = os.path.join(self._td.name, "pardus-healer", "settings.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("{bozuk json!!")

        from pardus_healer.config import Config

        c = Config()  # exception FIRLATMAMALI
        self.assertFalse(c.dark_mode)  # varsayılana dönmeli

    def test_bilinmeyen_anahtar_yok_sayilir(self):
        import json

        path = os.path.join(self._td.name, "pardus-healer", "settings.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"dark_mode": True, "zararli_anahtar": "x"}, fh)

        from pardus_healer.config import Config

        c = Config()
        self.assertTrue(c.dark_mode)
        self.assertNotIn("zararli_anahtar", c._data)


class EngineSmokeTests(unittest.TestCase):
    def test_motor_cokmeden_tamamlanir(self):
        # README'deki smoke-test'in otomatik hali: motor hangi platformda
        # olursa olsun çökmeden tamamlanmalı, eksik araçlarda kontroller
        # nazikçe UNKNOWN/INFO'ya düşmeli.
        from pardus_healer.checks import ALL_CHECK_CLASSES
        from pardus_healer.core.engine import DiagnosisEngine

        report = DiagnosisEngine().run_all()
        self.assertEqual(len(report.results), len(ALL_CHECK_CLASSES))
        self.assertTrue(0 <= report.health_score <= 100)
        self.assertIn(report.grade, list("ABCDF"))


if __name__ == "__main__":
    unittest.main()
