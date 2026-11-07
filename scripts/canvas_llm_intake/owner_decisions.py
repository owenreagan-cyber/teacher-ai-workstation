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

import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import manifest as mf

# Decision kinds.
KIND_ASSESSMENT_OVERRIDE = "assessment_override"
KIND_UNIT_LABEL_OVERRIDE = "unit_label_override"
# Parser-facing interpretation of an unchanged source cell (for example
# Math "Test 8" -> "WA8/FA8"). Applied only to a translation working copy.
KIND_SEMANTIC_INTERPRETATION = "semantic_interpretation"

VALID_KINDS = (
    KIND_ASSESSMENT_OVERRIDE,
    KIND_UNIT_LABEL_OVERRIDE,
    KIND_SEMANTIC_INTERPRETATION,
)

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


def semantic_decisions(
    decisions: list[dict[str, Any]] | None = None, *, subject: str | None = None,
) -> list[dict[str, Any]]:
    """Active semantic interpretations, optionally limited to one subject."""
    items = []
    for decision in decisions or []:
        if not decision.get("active", True):
            continue
        if decision.get("kind") != KIND_SEMANTIC_INTERPRETATION:
            continue
        if subject is not None and decision.get("subject") != subject:
            continue
        items.append(decision)
    return items


def _semantic_key(decision: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(decision.get("subject") or ""),
        str(decision.get("day") or ""),
        str(decision.get("date") or ""),
    )


def apply_translation_working_copy(
    week: dict[str, Any], decisions: list[dict[str, Any]] | None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return a deep copy whose matching cells use the owner parser value.

    The caller's week dict and its raw source strings are not modified. A
    decision applies only when the copied cell still equals ``source_value``,
    the weekday matches, and the cell date matches the decision date. Duplicate
    active decisions for the same cell fail closed and do not rewrite anything.
    Inactive decisions are ignored.
    """
    working = copy.deepcopy(week)
    week_code = ((week.get("week") or {}).get("code") or "")
    active = semantic_decisions(decisions)
    counts: dict[tuple[str, str, str], int] = {}
    for decision in active:
        key = _semantic_key(decision)
        counts[key] = counts.get(key, 0) + 1
    applied: list[dict[str, Any]] = []
    for decision in active:
        day_name = decision.get("day") or ""
        subject = decision.get("subject") or ""
        source_value = decision.get("source_value") or ""
        owner_value = decision.get("owner_value") or ""
        decision_date = decision.get("date") or ""
        day = (working.get("days") or {}).get(day_name) or {}
        cell = (day.get("subjects") or {}).get(subject) if isinstance(day, dict) else None
        cell_date = day.get("date", "") if isinstance(day, dict) else ""
        record = {
            "decision_id": decision.get("decision_id", ""),
            "subject": subject,
            "day": day_name,
            "date": decision_date,
            "source_value": source_value,
            "owner_value": owner_value,
            "observed_raw": cell.get("raw") if isinstance(cell, dict) else None,
            "observed_date": cell_date,
            "applied": False,
            "conflict": True,
        }
        decision_week = decision.get("week") or ""
        if counts[_semantic_key(decision)] > 1:
            record["reason"] = "duplicate active semantic decisions for the same cell"
        elif decision_week and week_code and decision_week != week_code:
            record["reason"] = "decision week does not match the instructional week"
        elif not isinstance(cell, dict):
            record["reason"] = "subject cell missing"
        elif not decision_date or decision_date != cell_date:
            record["reason"] = "source cell date does not match the decision date"
        elif cell.get("raw") != source_value:
            record["reason"] = "source value no longer matches the decision"
        else:
            cell["raw"] = owner_value
            record["applied"] = True
            record["conflict"] = False
            record["reason"] = "applied to translation working copy only"
        applied.append(record)
    return working, applied


def semantic_publication_blockers(applications: list[dict[str, Any]] | None) -> list[str]:
    """Block publication when a semantic decision did not apply cleanly."""
    blockers: list[str] = []
    for record in applications or []:
        if record.get("applied") is True and record.get("conflict") is not True:
            continue
        blockers.append(
            "semantic override conflict: "
            f"{record.get('subject')} {record.get('day')} {record.get('date')} "
            f"({record.get('reason') or 'not applied'})"
        )
    return blockers


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

            week = {
                "days": {"Tuesday": {"date": "2026-11-10", "subjects": {"math": {"raw": "Test 8"}}}},
            }
            original_raw = week["days"]["Tuesday"]["subjects"]["math"]["raw"]
            decision = upsert_decision(
                2, 4,
                kind=KIND_SEMANTIC_INTERPRETATION,
                subject="math",
                day="Tuesday",
                date="2026-11-10",
                source_value="Test 8",
                owner_value="WA8/FA8",
                reason="owner-confirmed cumulative and fact assessments",
                extra={"written_title": "Cumulative Test 8", "fact_title": "Fact Test 8"},
            )
            assert decision["written_title"] == "Cumulative Test 8"
            working, applied = apply_translation_working_copy(week, load_decisions(2, 4))
            assert week["days"]["Tuesday"]["subjects"]["math"]["raw"] == original_raw == "Test 8"
            assert working["days"]["Tuesday"]["subjects"]["math"]["raw"] == "WA8/FA8"
            assert applied[0]["applied"] is True
            drifted = {"days": {"Tuesday": {"subjects": {"math": {"raw": "Test 9"}}}}}
            _, skipped = apply_translation_working_copy(drifted, load_decisions(2, 4))
            assert skipped[0]["applied"] is False
            assert drifted["days"]["Tuesday"]["subjects"]["math"]["raw"] == "Test 9"

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
