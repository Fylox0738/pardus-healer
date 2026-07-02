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
    "auto_interval_min": 0,        # 0 = kapalı
    "first_run": True,             # tanıtım turu ilk açılışta gösterilir
    "advisor_mode": "rule",        # "rule" (varsayılan) | "ollama"
    "ollama_model": "llama3.2",    # Ollama seçilirse kullanılacak model
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

    @property
    def first_run(self) -> bool:
        return bool(self._data["first_run"])

    @first_run.setter
    def first_run(self, value: bool) -> None:
        self._data["first_run"] = bool(value)
        self.save()

    @property
    def advisor_mode(self) -> str:
        return str(self._data["advisor_mode"])

    @advisor_mode.setter
    def advisor_mode(self, value: str) -> None:
        self._data["advisor_mode"] = str(value)
        self.save()

    @property
    def ollama_model(self) -> str:
        return str(self._data["ollama_model"])

    @ollama_model.setter
    def ollama_model(self, value: str) -> None:
        self._data["ollama_model"] = str(value)
        self.save()
