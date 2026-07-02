"""Çekirdek veri modelleri.

Tüm tanı modülleri bu ortak yapıları döndürür; motor ve arayüz de
bunları tüketir. Böylece yeni bir kontrol eklemek için sadece bir
``CheckResult`` üretmek yeterlidir.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional


class Status(enum.Enum):
    """Bir kontrolün sonuç durumu.

    ``weight_factor`` sağlık skoru hesabında kullanılır (1.0 = tam sağlıklı,
    0.0 = tamamen sorunlu). UNKNOWN skora dahil edilmez.
    """

    OK = "ok"
    INFO = "info"
    WARN = "warn"
    FAIL = "fail"
    UNKNOWN = "unknown"

    @property
    def icon(self) -> str:
        return {
            Status.OK: "✅",
            Status.INFO: "ℹ️",
            Status.WARN: "⚠️",
            Status.FAIL: "❌",
            Status.UNKNOWN: "❔",
        }[self]

    @property
    def css_class(self) -> str:
        return {
            Status.OK: "card-ok",
            Status.INFO: "card-info-b",
            Status.WARN: "card-warn",
            Status.FAIL: "card-fail",
            Status.UNKNOWN: "card-wait",
        }[self]

    @property
    def label_tr(self) -> str:
        return {
            Status.OK: "TAMAM",
            Status.INFO: "BİLGİ",
            Status.WARN: "UYARI",
            Status.FAIL: "SORUNLU",
            Status.UNKNOWN: "BİLİNMİYOR",
        }[self]

    @property
    def weight_factor(self) -> Optional[float]:
        return {
            Status.OK: 1.0,
            Status.INFO: 1.0,
            Status.WARN: 0.55,
            Status.FAIL: 0.0,
            Status.UNKNOWN: None,  # skora dahil edilmez
        }[self]

    @property
    def severity_rank(self) -> int:
        """Sıralama için: yüksek = daha acil."""
        return {
            Status.FAIL: 4,
            Status.WARN: 3,
            Status.UNKNOWN: 2,
            Status.INFO: 1,
            Status.OK: 0,
        }[self]


@dataclass
class Fix:
    """Bir sorunu çözmek için çalıştırılabilir komut.

    ``needs_root`` True ise komut ``pkexec`` ile yükseltilerek çalıştırılır
    (parola penceresi çıkar). ``command`` bir kabuk komutudur.
    """

    label: str
    command: str
    needs_root: bool = True
    description: str = ""

    def resolved_command(self) -> str:
        """Gerçekten çalıştırılacak komutu döndürür."""
        return self.command


@dataclass
class Metric:
    """Sayısal bir ölçüm (dashboard göstergeleri / grafikler için)."""

    value: float
    unit: str = ""
    # 0..100 arası normalize edilmiş "doluluk/kullanım" yüzdesi (varsa)
    percent: Optional[float] = None


@dataclass
class CheckResult:
    """Bir tanı kontrolünün tüm çıktısı."""

    check_id: str
    title: str
    icon: str
    status: Status
    summary: str                       # kısa tek satır
    detail: str = ""                   # uzun açıklama (rapor / tooltip)
    category: str = "Genel"
    weight: float = 1.0                # sağlık skorundaki ağırlığı
    metric: Optional[Metric] = None
    root_cause: str = ""               # tespit edilen olası kök neden
    recommendation: str = ""           # kullanıcıya öneri
    fix: Optional[Fix] = None
    tags: list[str] = field(default_factory=list)
    duration_ms: int = 0

    @property
    def is_actionable(self) -> bool:
        return self.status in (Status.FAIL, Status.WARN) and self.fix is not None


@dataclass
class Insight:
    """Kural motorunun ürettiği, birden çok kontrolü ilişkilendiren içgörü.

    Bu, projenin "akıllı" tarafıdır: tek tek sonuçlara bakmak yerine
    aralarındaki neden-sonuç ilişkisini kurar ve önceliklendirir.
    """

    title: str
    message: str
    severity: Status = Status.WARN
    priority: int = 50                 # 0..100, yüksek = daha acil
    related: list[str] = field(default_factory=list)  # check_id listesi
    suggested_fix: Optional[Fix] = None


@dataclass
class DiagnosisReport:
    """Bir tam tanı turunun sonucu."""

    results: list[CheckResult]
    insights: list[Insight]
    health_score: int                  # 0..100
    grade: str                         # A / B / C / D / F
    started_at: str = ""
    duration_ms: int = 0

    @property
    def fail_count(self) -> int:
        return sum(1 for r in self.results if r.status is Status.FAIL)

    @property
    def warn_count(self) -> int:
        return sum(1 for r in self.results if r.status is Status.WARN)

    @property
    def ok_count(self) -> int:
        return sum(1 for r in self.results if r.status is Status.OK)
