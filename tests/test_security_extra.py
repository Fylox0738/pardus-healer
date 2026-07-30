"""Güvenlik kontrolleri ayrıştırma regresyon testleri.

İki denetim bulgusunu kilitler:
1. Açık port kontrolü ss çıktısının yalnızca Local Address sütununa bakmalı —
   LISTEN satırlarının Peer sütunu her zaman "0.0.0.0:*" olduğundan, tüm
   satırda arama yapmak 127.0.0.1'e bağlı servisleri "dışa açık" gösteriyordu.
2. Otomatik güncelleme kontrolü direktifin GERÇEK değerini okumalı — dosyada
   herhangi bir yerde "1" geçmesi "etkin" demek değildir.
"""

import unittest

from pardus_healer.checks.security_extra import (
    OpenPortsCheck,
    UnattendedUpgradesCheck,
)


class OpenPortsRegexTests(unittest.TestCase):
    RE = OpenPortsCheck._LOCAL_ADDR_RE
    WILD = OpenPortsCheck._WILDCARD_ADDRS

    def test_localhost_disa_acik_sayilmaz(self):
        # Denetimdeki birebir yanlış-pozitif: 127.0.0.1:3306 + peer "0.0.0.0:*"
        line = "tcp   LISTEN 0      128            127.0.0.1:3306        0.0.0.0:*"
        m = self.RE.match(line)
        self.assertIsNotNone(m)
        self.assertNotIn(m.group(1), self.WILD)
        self.assertEqual(m.group(2), "3306")

    def test_gercek_disa_acik_yakalanir(self):
        line = "tcp   LISTEN 0      128              0.0.0.0:23            0.0.0.0:*"
        m = self.RE.match(line)
        self.assertIsNotNone(m)
        self.assertIn(m.group(1), self.WILD)
        self.assertEqual(m.group(2), "23")

    def test_ipv6_joker_yakalanir(self):
        line = "tcp   LISTEN 0      128                [::]:5900             [::]:*"
        m = self.RE.match(line)
        self.assertIsNotNone(m)
        self.assertIn(m.group(1), self.WILD)

    def test_udp_satiri_ayristirilir(self):
        line = "udp   UNCONN 0      0              127.0.0.1:323           0.0.0.0:*"
        m = self.RE.match(line)
        self.assertIsNotNone(m)
        self.assertNotIn(m.group(1), self.WILD)


class DirectiveValueTests(unittest.TestCase):
    CFG_ACIK = (
        'APT::Periodic::Update-Package-Lists "1";\n'
        'APT::Periodic::Unattended-Upgrade "1";\n'
    )
    # Denetimdeki birebir senaryo: liste güncelleme açık ("1" dosyada VAR),
    # ama asıl yükseltme KAPALI — eski kod bunu "etkin" sanıyordu.
    CFG_KAPALI = (
        'APT::Periodic::Update-Package-Lists "1";\n'
        'APT::Periodic::Unattended-Upgrade "0";\n'
    )

    def test_acik_dogru_okunur(self):
        val = UnattendedUpgradesCheck._directive_value(
            self.CFG_ACIK, "Unattended-Upgrade")
        self.assertEqual(val, "1")

    def test_kapali_dogru_okunur(self):
        val = UnattendedUpgradesCheck._directive_value(
            self.CFG_KAPALI, "Unattended-Upgrade")
        self.assertEqual(val, "0")

    def test_bos_dosya_none(self):
        self.assertIsNone(
            UnattendedUpgradesCheck._directive_value("", "Unattended-Upgrade"))


if __name__ == "__main__":
    unittest.main()
