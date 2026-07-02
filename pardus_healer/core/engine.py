"""Tanı motoru: kontrolleri çalıştırır, sağlık skorunu hesaplar,
kural motorunu tetikler ve bütünleşik bir rapor üretir.
"""

from __future__ import annotations

import datetime
import time
from typing import Callable, Optional

from . import rules
from .check import BaseCheck
from .models import CheckResult, DiagnosisReport
from .registry import get_all_checks

ProgressCb = Callable[[int, int, CheckResult], None]


def compute_health_score(results: list[CheckResult]) -> int:
    """Ağırlıklı sağlık skoru (0..100).

    Her sonucun durumu bir "sağlık faktörüne" (OK=1.0, WARN=0.55, FAIL=0.0)
    dönüşür ve kontrolün ağırlığıyla çarpılır. UNKNOWN/eksik ölçümler skora
    dahil edilmez.
    """
    total_weight = 0.0
    earned = 0.0
    for r in results:
        factor = r.status.weight_factor
        if factor is None:  # UNKNOWN → skora katma
            continue
        total_weight += r.weight
        earned += r.weight * factor
    if total_weight == 0:
        return 100
    return round(earned / total_weight * 100)


def score_to_grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


class DiagnosisEngine:
    """Tüm tanı akışını yöneten üst düzey motor."""

    def __init__(self, checks: Optional[list[BaseCheck]] = None):
        self.checks: list[BaseCheck] = checks if checks is not None else get_all_checks()

    def run_all(
        self,
        progress_cb: Optional[ProgressCb] = None,
        concurrent: bool = True,
        max_workers: int = 8,
    ) -> DiagnosisReport:
        """Tüm kontrolleri çalıştırır ve tam rapor döndürür.

        concurrent=True (varsayılan) ise kontroller bir iş parçacığı havuzunda
        eşzamanlı çalışır. Kontroller ağırlıklı olarak G/Ç bağımlı (subprocess,
        dosya, soket) olduğundan bu, toplam tarama süresini belirgin biçimde
        kısaltır. Sonuçlar her zaman kontrol tanım sırasına göre döndürülür.

        progress_cb(tamamlanan, toplam, sonuç) her kontrol bittikçe çağrılır.
        """
        start = time.monotonic()
        started_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total = len(self.checks)
        # Orijinal sırayı korumak için id → sıra eşlemesi.
        order = {check.id: i for i, check in enumerate(self.checks)}
        collected: list[CheckResult] = []

        if concurrent and total > 1:
            from concurrent.futures import ThreadPoolExecutor, as_completed

            done = 0
            with ThreadPoolExecutor(max_workers=min(max_workers, total)) as pool:
                futures = {pool.submit(c.execute): c for c in self.checks}
                for fut in as_completed(futures):
                    result = fut.result()
                    collected.append(result)
                    done += 1
                    if progress_cb is not None:
                        progress_cb(done, total, result)
        else:
            for idx, check in enumerate(self.checks, start=1):
                result = check.execute()
                collected.append(result)
                if progress_cb is not None:
                    progress_cb(idx, total, result)

        results = sorted(collected, key=lambda r: order.get(r.check_id, 999))
        insights = rules.evaluate(results)
        score = compute_health_score(results)
        duration_ms = int((time.monotonic() - start) * 1000)
        return DiagnosisReport(
            results=results,
            insights=insights,
            health_score=score,
            grade=score_to_grade(score),
            started_at=started_at,
            duration_ms=duration_ms,
        )

    def run_one(self, check_id: str) -> Optional[CheckResult]:
        """Tek bir kontrolü id ile çalıştırır (kart bazında yenileme için)."""
        for check in self.checks:
            if check.id == check_id:
                return check.execute()
        return None
