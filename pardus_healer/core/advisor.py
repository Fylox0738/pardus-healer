"""Akıllı değerlendirme (danışman) katmanı.

İki mod:
  • RuleAdvisor  — kural tabanlı, doğal dilde özet üretir. Hiç güç/internet
    istemez; varsayılan ve her zaman çalışır (zayıf akıllı tahtalar için ideal).
  • OllamaAdvisor — cihazda çalışan yerel bir dil modeli (Ollama) ile daha
    zengin, sohbet üslubunda özet üretir. İSTEĞE BAĞLIDIR: Ollama kurulu/açık
    değilse ya da yanıt vermezse sessizce RuleAdvisor'a düşülür. Asla uygulamayı
    bloke etmez veya çökertmez.

Her iki danışman da aynı arayüzü paylaşır: ``summarize(report) -> str``.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from .models import DiagnosisReport, Status

OLLAMA_URL = "http://127.0.0.1:11434"


class RuleAdvisor:
    """Kural tabanlı, şablonlu doğal dil değerlendirmesi (güç gerektirmez)."""

    name = "Kural Tabanlı"

    def summarize(self, report: DiagnosisReport) -> str:
        parts: list[str] = []

        # 1) genel durum cümlesi
        s = report.health_score
        if s >= 90:
            parts.append(
                f"Sisteminiz çok sağlıklı görünüyor (skor {s}/100, not "
                f"{report.grade}). Ciddi bir sorun yok.")
        elif s >= 75:
            parts.append(
                f"Sisteminiz genel olarak iyi durumda (skor {s}/100, not "
                f"{report.grade}), ancak birkaç noktaya bakmakta fayda var.")
        elif s >= 50:
            parts.append(
                f"Sisteminizde dikkat gerektiren konular var (skor {s}/100, "
                f"not {report.grade}). Aşağıdaki adımları uygulamanız önerilir.")
        else:
            parts.append(
                f"Sisteminiz bakım istiyor (skor {s}/100, not {report.grade}). "
                f"Önemli sorunlar tespit edildi; bir an önce ele alınmalı.")

        # 2) sayısal özet
        parts.append(
            f"Toplamda {report.fail_count} sorun ve {report.warn_count} uyarı "
            f"bulundu, {report.ok_count} kontrol sağlıklı.")

        # 3) en öncelikli içgörü
        if report.insights:
            top = report.insights[0]
            parts.append(f"En öncelikli konu — {top.title}: {top.message}")
            if len(report.insights) > 1:
                names = ", ".join(i.title for i in report.insights[1:3])
                parts.append(f"Ayrıca şunlara da bakılmalı: {names}.")

        # 4) somut ilk adım
        actionable = [
            r for r in report.results
            if r.status is Status.FAIL and r.fix is not None
        ]
        if actionable:
            first = actionable[0]
            parts.append(
                f"İlk adım olarak “{first.title}” sorununu "
                f"“{first.fix.label}” ile düzeltebilirsiniz. Dilerseniz "
                f"“Otomatik Onar” ile tüm sorunlar sırayla çözülür.")
        elif report.fail_count == 0 and report.warn_count == 0:
            parts.append("Şu an yapmanız gereken bir şey yok; sistem temiz.")

        return " ".join(parts)


class OllamaAdvisor:
    """Yerel Ollama modeliyle değerlendirme üretir (isteğe bağlı, güç ister)."""

    name = "Yerel Yapay Zekâ (Ollama)"

    def __init__(self, model: str = "llama3.2", timeout: int = 40):
        self.model = model
        self.timeout = timeout
        self._fallback = RuleAdvisor()

    def summarize(self, report: DiagnosisReport) -> str:
        text = self._ask_ollama(report)
        # Ollama yoksa/başarısızsa kural tabanlı özete düş.
        return text if text else self._fallback.summarize(report)

    def _build_prompt(self, report: DiagnosisReport) -> str:
        lines = [
            "Bir Pardus/Linux sistem tanı aracının sonuçlarını, teknik "
            "olmayan bir kullanıcıya Türkçe, kısa ve anlaşılır biçimde "
            "özetle. Abartma, uydurma; yalnızca verilen bilgilere dayan.",
            "",
            f"Sağlık skoru: {report.health_score}/100 (Not: {report.grade})",
            f"Sorun: {report.fail_count}, Uyarı: {report.warn_count}, "
            f"Sağlıklı: {report.ok_count}",
            "",
            "Tespitler:",
        ]
        for r in report.results:
            if r.status in (Status.FAIL, Status.WARN):
                lines.append(f"- [{r.status.label_tr}] {r.title}: {r.summary}")
        if report.insights:
            lines.append("")
            lines.append("Öncelikli içgörüler:")
            for i in report.insights[:4]:
                lines.append(f"- {i.title}: {i.message}")
        lines.append("")
        lines.append("En fazla 4-5 cümlelik bir değerlendirme yaz.")
        return "\n".join(lines)

    def _ask_ollama(self, report: DiagnosisReport) -> str | None:
        payload = json.dumps({
            "model": self.model,
            "prompt": self._build_prompt(report),
            "stream": False,
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            text = (data.get("response") or "").strip()
            return text or None
        except (urllib.error.URLError, OSError, ValueError, TimeoutError):
            return None


def is_ollama_available(timeout: int = 2) -> bool:
    """Ollama servisi yerelde çalışıyor mu? (hızlı, bloke etmeyen kontrol)"""
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=timeout):
            return True
    except (urllib.error.URLError, OSError, ValueError):
        return False


def get_advisor(mode: str, model: str = "llama3.2"):
    """Ayara göre uygun danışmanı döndürür."""
    if mode == "ollama":
        return OllamaAdvisor(model=model)
    return RuleAdvisor()
