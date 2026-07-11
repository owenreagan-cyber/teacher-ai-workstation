from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_SOURCE_HIERARCHY = [
    "owner-confirmed hard rules",
    "explicit current-year pacing-guide entry",
    "approved teacher correction",
    "repeated FPK pacing-guide pattern",
    "predictive suggestion",
    "unresolved",
]


@dataclass
class PatternRecord:
    pattern_id: str
    subject: str
    observation_count: int
    consistency: str
    conflicting_observations: int
    confidence: float
    source_range: str
    owner_confirmed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "patternId": self.pattern_id,
            "subject": self.subject,
            "observationCount": self.observation_count,
            "consistency": self.consistency,
            "conflictingObservations": self.conflicting_observations,
            "confidence": self.confidence,
            "sourceRange": self.source_range,
            "ownerConfirmed": self.owner_confirmed,
        }


def compact(value: Any) -> str:
    return " ".join(str(value or "").replace("\xa0", " ").split())


def load_pacing_knowledge(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if path.suffix.lower() == ".csv":
        entries = _load_csv_entries(path)
        payload = {"sourceKind": "sanitized-csv", "pacingGuideEntries": entries}
    else:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Pacing knowledge payload must be an object")
        payload.setdefault("pacingGuideEntries", [])
    payload.setdefault("sourceHierarchy", list(DEFAULT_SOURCE_HIERARCHY))
    payload.setdefault("ownerConfirmedRules", {})
    payload.setdefault("manualTeacherCorrections", [])
    payload.setdefault("explicitOverrides", [])
    payload["patternRecords"] = build_pattern_records(payload.get("pacingGuideEntries", []))
    return payload


def _load_csv_entries(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(
                {
                    "id": compact(row.get("id")),
                    "subject": compact(row.get("subject")).lower(),
                    "weekday": compact(row.get("weekday")),
                    "eventType": compact(row.get("eventType") or row.get("event_type")),
                    "lessonNumber": int(row["lessonNumber"]) if compact(row.get("lessonNumber")).isdigit() else None,
                    "assessmentNumber": int(row["assessmentNumber"]) if compact(row.get("assessmentNumber")).isdigit() else None,
                    "sourcePacingReference": compact(row.get("sourcePacingReference") or row.get("source_pacing_reference")),
                }
            )
    return rows


def build_pattern_records(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        grouped.setdefault(compact(entry.get("subject")).lower(), []).append(entry)
    records: list[dict[str, Any]] = []
    for subject, subject_entries in grouped.items():
        lesson_numbers = [int(item["lessonNumber"]) for item in subject_entries if str(item.get("lessonNumber") or "").isdigit()]
        records.append(
            PatternRecord(
                pattern_id=f"{subject}.sequence",
                subject=subject,
                observation_count=len(subject_entries),
                consistency="high" if len(subject_entries) >= 2 else "low",
                conflicting_observations=0 if len(subject_entries) < 3 else 1,
                confidence=0.9 if len(subject_entries) >= 2 else 0.55,
                source_range=_source_range(lesson_numbers),
                owner_confirmed=subject in {"math", "reading", "spelling"},
            ).to_dict()
        )
    return records


def _source_range(numbers: list[int]) -> str:
    if not numbers:
        return "n/a"
    return f"{min(numbers)}-{max(numbers)}"
