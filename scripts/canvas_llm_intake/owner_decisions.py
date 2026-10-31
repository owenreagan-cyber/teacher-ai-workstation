"""Auditable owner-decision ledger for the Canvas Weekly Intake workspace.

Day-level edits live in :mod:`owner_overrides` (in_class / at_home / status).
This module records decisions that change *meaning* rather than display, such
as an owner-directed assessment title that intentionally overrides a stale
canonical unit name.

Every record preserves BOTH the original source value and the owner-directed
value, plus reason, provenance, and an explicit acknowledgement of stale
configuration. Source snapshots are never modified; only the regenerated
draft consumes the decision.

Stored locally (gitignored) at::

    .local/canvas-llm/intake/<year>/q<q>/w<w>/owner-decisions.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import manifest as mf

# Decision kinds.
KIND_ASSESSMENT_OVERRIDE = "assessment_override"
KIND_UNIT_LABEL_OVERRIDE = "unit_label_override"

VALID_KINDS = (KIND_ASSESSMENT_OVERRIDE, KIND_UNIT_LABEL_OVERRIDE)

# Provenance values.
SOURCE_OWNER_INSTRUCTION = "OWNER_INSTRUCTION"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def decision_path(quarter: int, week: int) -> Path:
    return mf.staging_dir(quarter, week) / "owner-decisions.json"


def load_decisions(quarter: int, week: int) -> list[dict[str, Any]]:
    path = decision_path(quarter, week)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if isinstance(data, dict):
        data = data.get("decisions", [])
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def save_decisions(quarter: int, week: int, decisions: list[dict[str, Any]]) -> Path:
    path = decision_path(quarter, week)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"schemaVersion": 1, "decisions": decisions}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def decision_id(kind: str, subject: str, day: str, date: str = "") -> str:
    parts = [kind, subject, day]
    if date:
        parts.append(date)
    return "|".join(parts)


def upsert_decision(
    quarter: int,
    week: int,
    *,
    kind: str,
    subject: str,
    day: str,
    date: str = "",
    source_value: str,
    owner_value: str,
    reason: str,
    provenance: str = SOURCE_OWNER_INSTRUCTION,
    acknowledgement: str = "",
    active: bool = True,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create or update an auditable owner decision (preserves history)."""
    if kind not in VALID_KINDS:
        raise ValueError(f"unknown owner decision kind {kind!r}")
    if not source_value or not owner_value:
        raise ValueError("owner decisions must preserve both source_value and owner_value")
    decisions = load_decisions(quarter, week)
    key = decision_id(kind, subject, day, date)
    now = _now()
    prev = next((d for d in decisions if d.get("decision_id") == key), None)
    record: dict[str, Any] = {
        "decision_id": key,
        "kind": kind,
        "subject": subject,
        "day": day,
        "date": date,
        "source_value": source_value,
        "owner_value": owner_value,
        "reason": reason,
        "provenance": provenance,
        "acknowledgement": acknowledgement,
        "recorded_at": (prev or {}).get("recorded_at", now),
        "updated_at": now,
        "active": bool(active),
        "history": list((prev or {}).get("history", [])),
    }
    if extra:
        record.update(extra)
    record["history"].append({
        "at": now,
        "action": "upsert" if prev is None else "update",
        "source_value": source_value,
        "owner_value": owner_value,
    })
    if prev is None:
        decisions.append(record)
    else:
        decisions = [record if d.get("decision_id") == key else d for d in decisions]
    save_decisions(quarter, week, decisions)
    return record


def active_decisions(quarter: int, week: int, *, kind: str | None = None) -> list[dict[str, Any]]:
    items = [d for d in load_decisions(quarter, week) if d.get("active", True)]
    if kind is not None:
        items = [d for d in items if d.get("kind") == kind]
    return items


def science_assessment_override(
    decisions: list[dict[str, Any]] | None = None, *, date: str | None = None
) -> dict[str, Any] | None:
    """Return the active Science assessment override (optionally date-matched)."""
    for decision in decisions or []:
        if not decision.get("active", True):
            continue
        if decision.get("kind") != KIND_ASSESSMENT_OVERRIDE:
            continue
        if decision.get("subject") != "science":
            continue
        if date is not None and decision.get("date") not in ("", date):
            continue
        return decision
    return None


def command_self_test() -> int:
    import tempfile

    orig = mf.staging_dir
    with tempfile.TemporaryDirectory() as tmp:
        mf.staging_dir = lambda q, w: Path(tmp) / f"q{q}w{w}"
        try:
            assert load_decisions(2, 4) == []
            rec = upsert_decision(
                2, 4,
                kind=KIND_ASSESSMENT_OVERRIDE,
                subject="science",
                day="Thursday",
                date="2026-11-05",
                source_value="Test",
                owner_value="Energy Transformations Unit Test",
                reason="explicit Owen instruction",
                acknowledgement="canonical unit config may be stale",
            )
            assert rec["source_value"] == "Test"
            assert rec["owner_value"] == "Energy Transformations Unit Test"
            assert rec["history"]

            found = science_assessment_override(load_decisions(2, 4), date="2026-11-05")
            assert found is not None and found["owner_value"] == "Energy Transformations Unit Test"
            assert science_assessment_override(load_decisions(2, 4), date="2026-11-06") is None

            # Update does not duplicate.
            upsert_decision(
                2, 4,
                kind=KIND_ASSESSMENT_OVERRIDE,
                subject="science",
                day="Thursday",
                date="2026-11-05",
                source_value="Test",
                owner_value="Energy Transformations Unit Test",
                reason="explicit Owen instruction (confirmed)",
            )
            assert len(load_decisions(2, 4)) == 1
            assert len(load_decisions(2, 4)[0]["history"]) == 2

            # Both values are mandatory.
            try:
                upsert_decision(
                    2, 4, kind=KIND_ASSESSMENT_OVERRIDE, subject="science",
                    day="Thursday", source_value="", owner_value="X", reason="r",
                )
                raise AssertionError("expected ValueError")
            except ValueError:
                pass
        finally:
            mf.staging_dir = orig
    print("PASS intake owner-decisions self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
