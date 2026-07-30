"""Swarm HMAC kimlik doğrulama testleri.

 Kol 2 bulgusu: imza eskiden yalnızca timestamp:nonce
üzerinden hesaplanıyordu; /health için üretilmiş bir imza /heal_all'a karşı
yeniden kullanılabiliyordu (cross-endpoint replay). İmza artık method+path'i
kapsıyor; nonce'lar tek kullanımlık.
"""

import time
import unittest

from pardus_healer.swarm import auth


class SwarmAuthTests(unittest.TestCase):
    TOKEN = "test-anahtari-123"

    def test_gidis_donus(self):
        h = auth.generate_auth_headers(self.TOKEN, method="GET", path="/health")
        self.assertTrue(
            auth.verify_auth_headers(h, self.TOKEN, method="GET", path="/health"))

    def test_yanlis_token_reddedilir(self):
        h = auth.generate_auth_headers(self.TOKEN, method="GET", path="/health")
        self.assertFalse(
            auth.verify_auth_headers(h, "baska-token", method="GET", path="/health"))

    def test_capraz_uc_nokta_replay_reddedilir(self):
        # Denetimdeki birebir saldırı: /health imzası /heal_all'a karşı.
        h = auth.generate_auth_headers(self.TOKEN, method="GET", path="/health")
        self.assertFalse(
            auth.verify_auth_headers(h, self.TOKEN, method="POST", path="/heal_all"))

    def test_nonce_tekrari_reddedilir(self):
        h = auth.generate_auth_headers(self.TOKEN, method="GET", path="/health")
        self.assertTrue(
            auth.verify_auth_headers(h, self.TOKEN, method="GET", path="/health"))
        # Aynı başlıklar ikinci kez geçersiz olmalı (replay koruması).
        self.assertFalse(
            auth.verify_auth_headers(h, self.TOKEN, method="GET", path="/health"))

    def test_eski_timestamp_reddedilir(self):
        h = dict(auth.generate_auth_headers(self.TOKEN, method="GET", path="/health"))
        h["X-Healer-Timestamp"] = str(int(time.time()) - 3600)
        self.assertFalse(
            auth.verify_auth_headers(h, self.TOKEN, method="GET", path="/health"))

    def test_eksik_baslik_reddedilir(self):
        self.assertFalse(
            auth.verify_auth_headers({}, self.TOKEN, method="GET", path="/health"))


if __name__ == "__main__":
    unittest.main()
