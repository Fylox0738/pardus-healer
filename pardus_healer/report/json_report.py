"""Makine tarafından okunabilir JSON rapor (otomasyon/entegrasyon için)."""

from __future__ import annotations

import json
import os

from ..core.models import DiagnosisReport


def report_to_dict(report: DiagnosisReport) -> dict:
    return {
        "generated_at": report.started_at,
        "health_score": report.health_score,
        "grade": report.grade,
        "summary": {
            "fail": report.fail_count,
            "warn": report.warn_count,
            "ok": report.ok_count,
        },
        "insights": [
            {
                "title": ins.title,
                "message": ins.message,
                "severity": ins.severity.value,
                "priority": ins.priority,
                "related": ins.related,
            }
            for ins in report.insights
        ],
        "results": [
            {
                "id": r.check_id,
                "title": r.title,
                "category": r.category,
                "status": r.status.value,
                "summary": r.summary,
                "root_cause": r.root_cause,
                "recommendation": r.recommendation,
                "metric": (
                    {"value": r.metric.value, "unit": r.metric.unit}
                    if r.metric else None
                ),
            }
            for r in report.results
        ],
    }


def build_json_report(report: DiagnosisReport) -> str:
    return json.dumps(report_to_dict(report), ensure_ascii=False, indent=2)


def save_json_report(report: DiagnosisReport, path: str | None = None) -> str:
    if path is None:
        path = os.path.join(os.path.expanduser("~"), "pardus-healer-rapor.json")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(build_json_report(report))
    return path
