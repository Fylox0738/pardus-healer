"""BaseCheck fix-sentinel regresyon testleri.

TECHNICAL_AUDIT.md Kol 1 bulgusu: ok()/info()/unknown() içindeki
``fix=None`` sıfırlaması, ``None`` ile "hiç verilmedi" ayrımı yapılamadığı
için çalışmıyordu; ``default_fix`` tanımlı bir kontrolde OK durumunda bile
"Düzelt" butonu geri gelebiliyordu. ``_UNSET`` sentineli bunu çözdü.
"""

import unittest

from pardus_healer.core.check import BaseCheck
from pardus_healer.core.models import Fix

_DEFAULT_FIX = Fix("Onar", "pkexec true", needs_root=True)


class DummyCheck(BaseCheck):
    id = "dummy"
    title = "Deneme Kontrolü"
    default_fix = _DEFAULT_FIX

    def run(self):
        return self.ok("temiz")


class SentinelTests(unittest.TestCase):
    def test_ok_fix_sifirlar(self):
        self.assertIsNone(DummyCheck().ok("temiz").fix)

    def test_info_fix_sifirlar(self):
        self.assertIsNone(DummyCheck().info("bilgi").fix)

    def test_unknown_fix_sifirlar(self):
        self.assertIsNone(DummyCheck().unknown("bilinmiyor").fix)

    def test_fail_default_fix_korur(self):
        self.assertIs(DummyCheck().fail("sorun").fix, _DEFAULT_FIX)

    def test_warn_default_fix_korur(self):
        self.assertIs(DummyCheck().warn("uyarı").fix, _DEFAULT_FIX)

    def test_acik_fix_gecersiz_kilar(self):
        ozel = Fix("Özel", "pkexec false", needs_root=True)
        self.assertIs(DummyCheck().fail("sorun", fix=ozel).fix, ozel)

    def test_ok_acik_fix_verilebilir(self):
        ozel = Fix("Özel", "pkexec false", needs_root=True)
        self.assertIs(DummyCheck().ok("temiz", fix=ozel).fix, ozel)

    def test_execute_cokmez(self):
        class Patlayan(BaseCheck):
            id = "patlayan"
            title = "Patlayan"

            def run(self):
                raise RuntimeError("bilerek")

        result = Patlayan().execute()
        self.assertEqual(result.check_id, "patlayan")
        self.assertIn("bilerek", result.summary + result.detail)


if __name__ == "__main__":
    unittest.main()
