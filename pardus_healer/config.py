"""Kullanıcı ayarlarının kalıcı saklanması.

Ayarlar ~/.config/pardus-healer/settings.json içinde tutulur. Dosya yoksa
varsayılanlar kullanılır; yazma hataları sessizce yok sayılır (uygulama asla
ayar yüzünden çökmemeli).
"""

from __future__ import annotations

import json
import os

_DEFAULTS = {
    "dark_mode": False,
    "auto_interval_min": 0,   # 0 = kapalı
}


def _config_path() -> str:
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
        os.path.expanduser("~"), ".config"
    )
    return os.path.join(base, "pardus-healer", "settings.json")


class Config:
    def __init__(self):
        self._data = dict(_DEFAULTS)
        self.load()

    def load(self) -> None:
        try:
            with open(_config_path(), "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                self._data.update({k: data[k] for k in _DEFAULTS if k in data})
        except (OSError, ValueError):
            pass  # dosya yok veya bozuk → varsayılanlar

    def save(self) -> None:
        path = _config_path()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(self._data, fh, indent=2)
        except OSError:
            pass

    # ---- erişimciler ----
    @property
    def dark_mode(self) -> bool:
        return bool(self._data["dark_mode"])

    @dark_mode.setter
    def dark_mode(self, value: bool) -> None:
        self._data["dark_mode"] = bool(value)
        self.save()

    @property
    def auto_interval_min(self) -> int:
        return int(self._data["auto_interval_min"])

    @auto_interval_min.setter
    def auto_interval_min(self, value: int) -> None:
        self._data["auto_interval_min"] = int(value)
        self.save()
