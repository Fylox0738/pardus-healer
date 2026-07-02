"""Tanı kontrolleri için temel sınıf.

Yeni bir kontrol eklemek için ``BaseCheck``'ten türeyip ``run()`` metodunu
yazmak yeterlidir. Meta bilgiler (id, başlık, ikon, kategori, ağırlık) sınıf
niteliği olarak tanımlanır; ``ok()/warn()/fail()/info()`` yardımcıları
``CheckResult`` üretimini kolaylaştırır.
"""

from __future__ import annotations

import time
from typing import Optional

from .models import CheckResult, Fix, Metric, Status


class BaseCheck:
    # --- alt sınıflar bunları ezmeli ---
    id: str = "base"
    title: str = "Kontrol"
    icon: str = "•"
    category: str = "Genel"
    weight: float = 1.0
    # Varsayılan onarım komutu (kart üzerindeki "Düzelt" butonu). None olabilir.
    default_fix: Optional[Fix] = None

    def run(self) -> CheckResult:  # pragma: no cover - alt sınıf ezmeli
        raise NotImplementedError

    # ---- zamanlamalı çalıştırma sarmalayıcısı ----
    def execute(self) -> CheckResult:
        """run()'ı çalıştırır, süreyi ölçer, hataları yakalar."""
        start = time.monotonic()
        try:
            result = self.run()
        except Exception as exc:  # bir kontrol asla uygulamayı çökertmesin
            result = self.fail(
                f"Kontrol sırasında hata: {exc}",
                detail=repr(exc),
            )
        result.duration_ms = int((time.monotonic() - start) * 1000)
        return result

    # ---- CheckResult üretim yardımcıları ----
    def _make(
        self,
        status: Status,
        summary: str,
        detail: str = "",
        metric: Optional[Metric] = None,
        root_cause: str = "",
        recommendation: str = "",
        fix: Optional[Fix] = None,
        tags: Optional[list[str]] = None,
    ) -> CheckResult:
        return CheckResult(
            check_id=self.id,
            title=self.title,
            icon=self.icon,
            status=status,
            summary=summary,
            detail=detail,
            category=self.category,
            weight=self.weight,
            metric=metric,
            root_cause=root_cause,
            recommendation=recommendation,
            fix=fix if fix is not None else self.default_fix,
            tags=tags or [],
        )

    def ok(self, summary: str, **kw) -> CheckResult:
        # OK durumunda "Düzelt" butonu gösterilmesin diye fix'i sıfırla.
        kw.setdefault("fix", None)
        return self._make(Status.OK, summary, **kw)

    def info(self, summary: str, **kw) -> CheckResult:
        kw.setdefault("fix", None)
        return self._make(Status.INFO, summary, **kw)

    def warn(self, summary: str, **kw) -> CheckResult:
        return self._make(Status.WARN, summary, **kw)

    def fail(self, summary: str, **kw) -> CheckResult:
        return self._make(Status.FAIL, summary, **kw)

    def unknown(self, summary: str, **kw) -> CheckResult:
        kw.setdefault("fix", None)
        return self._make(Status.UNKNOWN, summary, **kw)
