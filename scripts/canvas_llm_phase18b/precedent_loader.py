"""Optional read-only precedent-bundle ingestion (Phase 18B).

The August 15 Canvas scout bundle may exist at:

    .local/canvas/precedent/2026-08-15_operational-reconstruction/
        PRECEDENT_REPORT.md
        precedent.json
        evidence/

This loader is read-only and optional:

- absence is normal and must not fail the phase;
- the bundle is never modified;
- malformed bundles produce a controlled WARN/diagnostic state (fail closed,
  no partial promotion);
- anomalies are classified but never promoted;
- canvas_configuration findings are flagged as live-verifiable-only and never
  hardcoded into operational truth;
- when the bundle is absent or unusable, the caller falls back to the static
  Phase 18A precedent catalog.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from scripts.canvas_llm_phase18a.precedent import (
    PRECEDENT_CATALOG,
    is_valid_precedent_class,
)

DEFAULT_BUNDLE_DIR = Path(".local/canvas/precedent/2026-08-15_operational-reconstruction")
BUNDLE_JSON_NAME = "precedent.json"


@dataclass
class PrecedentLoadResult:
    status: str  # "absent" | "ok" | "malformed"
    records: list[dict[str, str]] = field(default_factory=list)  # operational_behavior only
    config_entries: list[dict[str, str]] = field(default_factory=list)  # canvas_configuration
    anomalies: list[dict[str, str]] = field(default_factory=list)  # anomaly
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "records": [dict(r) for r in self.records],
            "configEntries": [dict(r) for r in self.config_entries],
            "anomalies": [dict(r) for r in self.anomalies],
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }

    @property
    def ok(self) -> bool:
        return self.status in {"absent", "ok"}


def static_catalog() -> list[dict[str, str]]:
    """Return the Phase 18A static precedent catalog (fallback source)."""
    return [dict(item) for item in PRECEDENT_CATALOG]


def _classify(record: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    """Classify one parsed bundle record into (category, warnings, errors)."""
    warnings: list[str] = []
    errors: list[str] = []
    classification = str(record.get("classification") or "").strip()
    description = str(record.get("description") or "").strip()
    if not classification or not is_valid_precedent_class(classification):
        errors.append(f"invalid or missing classification: {classification!r}")
        return "", warnings, errors
    if not description:
        errors.append(f"record with classification {classification!r} has no description")
        return "", warnings, errors
    return classification, warnings, errors


def _parse_bundle_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [dict(r) for r in payload if isinstance(r, dict)]
    if isinstance(payload, dict):
        for key in ("precedents", "findings", "records"):
            value = payload.get(key)
            if isinstance(value, list):
                return [dict(r) for r in value if isinstance(r, dict)]
    return []


def load_precedent_bundle(bundle_dir: Path | None = None) -> PrecedentLoadResult:
    """Read and classify the optional precedent bundle, if present."""
    root = bundle_dir or DEFAULT_BUNDLE_DIR
    result = PrecedentLoadResult(status="absent")

    if not root.exists():
        result.warnings.append(
            f"precedent bundle absent ({root}); using static Phase 18A catalog"
        )
        return result

    json_path = root / BUNDLE_JSON_NAME
    if not json_path.is_file():
        result.status = "malformed"
        result.errors.append(
            f"precedent bundle dir exists but {BUNDLE_JSON_NAME} is missing: {root}"
        )
        result.warnings.append(
            "falling back to static Phase 18A catalog; bundle is not consumed"
        )
        return result

    try:
        raw = json_path.read_text(encoding="utf-8")
    except OSError as exc:
        result.status = "malformed"
        result.errors.append(f"could not read precedent bundle: {exc}")
        result.warnings.append("falling back to static Phase 18A catalog")
        return result

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        result.status = "malformed"
        result.errors.append(f"precedent bundle is not valid JSON: {exc}")
        result.warnings.append("falling back to static Phase 18A catalog")
        return result

    records = _parse_bundle_records(payload)
    if not records:
        result.status = "malformed"
        result.errors.append("precedent bundle parsed but contained no recognized records")
        result.warnings.append("falling back to static Phase 18A catalog")
        return result

    result.status = "ok"
    for record in records:
        classification, warnings, errors = _classify(record)
        result.warnings.extend(warnings)
        if classification == "anomaly":
            result.anomalies.append(record)
        elif classification == "canvas_configuration":
            result.config_entries.append(record)
        elif classification == "operational_behavior":
            result.records.append(record)
        if errors:
            result.status = "malformed"
            result.errors.extend(errors)

    if result.status == "malformed":
        # Fail closed: never partially promote a bundle with any invalid record.
        result.records = []
        result.config_entries = []
        result.anomalies = []
        result.warnings.append(
            "bundle contained malformed records; falling back to static Phase 18A catalog"
        )
    return result
