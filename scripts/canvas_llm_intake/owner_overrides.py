"""Owner-override ledger for the Canvas Weekly Intake workspace.

Structured, auditable per-day/per-subject owner edits. Stored locally
(gitignored) under ``.local/canvas-llm/intake/<year>/q<q>/w<w>/owner-overrides.json``.

Precedence (canonical, never changed here):
    newest explicit Owen instruction > current live pacing > locked decisions
    > canonical files > history > model inference

An override records the source value alongside the owner value so regeneration
can restore source and the UI can show SOURCE vs OWNER OVERRIDE distinctly.
Source snapshots are never overwritten.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import manifest as mf

# Day-level status vocabulary (UI display concepts; not new lifecycle states).
STATUS_PLANNED = "PLANNED"
STATUS_PENDING_SOURCE = "PENDING_SOURCE"
STATUS_OWNER_CONFIRMED_BLANK = "OWNER_CONFIRMED_BLANK"
STATUS_NOT_APPLICABLE = "NOT_APPLICABLE"
STATUS_NEEDS_INPUT = "NEEDS_INPUT"
STATUS_READY = "READY"

VALID_STATUSES = (
    STATUS_PLANNED,
    STATUS_PENDING_SOURCE,
    STATUS_OWNER_CONFIRMED_BLANK,
    STATUS_NOT_APPLICABLE,
    STATUS_NEEDS_INPUT,
    STATUS_READY,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def override_path(quarter: int, week: int) -> Path:
    return mf.staging_dir(quarter, week) / "owner-overrides.json"


def load_overrides(quarter: int, week: int) -> dict[str, dict[str, Any]]:
    path = override_path(quarter, week)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {k: v for k, v in data.items() if isinstance(v, dict)}


def save_overrides(quarter: int, week: int, data: dict[str, dict[str, Any]]) -> Path:
    path = override_path(quarter, week)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _key(subject: str, day: str) -> str:
    return f"{subject}|{day}"


def list_overrides(quarter: int, week: int) -> list[dict[str, Any]]:
    """All ACTIVE overrides, sorted by subject then day."""
    data = load_overrides(quarter, week)
    order = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")
    items = [v for v in data.values() if v.get("active", True)]
    items.sort(key=lambda v: (v.get("subject", ""), order.index(v.get("day")) if v.get("day") in order else 99))
    return items


def day_override(quarter: int, week: int, subject: str, day: str) -> dict[str, Any] | None:
    data = load_overrides(quarter, week)
    rec = data.get(_key(subject, day))
    if rec and rec.get("active", True):
        return rec
    return None


def upsert_override(
    quarter: int,
    week: int,
    *,
    subject: str,
    day: str,
    source_value: str | None = None,
    in_class: list[str] | None = None,
    at_home: str | None = None,
    status: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    """Create or update a day override (atomic, preserves audit history)."""
    if status is not None and status not in VALID_STATUSES:
        raise ValueError(f"unknown override status {status!r}")
    data = load_overrides(quarter, week)
    key = _key(subject, day)
    now = _now()
    prev = data.get(key, {})
    record = {
        "override_id": key,
        "subject": subject,
        "day": day,
        "source_value": source_value if source_value is not None else prev.get("source_value"),
        "in_class": in_class if in_class is not None else prev.get("in_class"),
        "at_home": at_home if at_home is not None else prev.get("at_home"),
        "status": status if status is not None else prev.get("status", STATUS_PLANNED),
        "note": note if note is not None else prev.get("note", ""),
        "created_at": prev.get("created_at", now),
        "updated_at": now,
        "source": "OWNER_INPUT",
        "active": True,
    }
    history = list(prev.get("history", []))
    history.append({"at": now, "action": "upsert", "fields": sorted(k for k in record if k not in ("history", "created_at", "updated_at"))})
    record["history"] = history
    data[key] = record
    save_overrides(quarter, week, data)
    return record


def restore_source(quarter: int, week: int, subject: str, day: str) -> bool:
    """Deactivate an active override; return True if an active one was removed."""
    data = load_overrides(quarter, week)
    key = _key(subject, day)
    rec = data.get(key)
    if not rec or not rec.get("active", True):
        return False
    rec["active"] = False
    rec["updated_at"] = _now()
    rec.setdefault("history", []).append({"at": _now(), "action": "restore_source"})
    data[key] = rec
    save_overrides(quarter, week, data)
    return True


def mark_pending(quarter: int, week: int, subject: str, day: str, source_value: str | None = None) -> dict[str, Any]:
    return upsert_override(quarter, week, subject=subject, day=day,
                           source_value=source_value, status=STATUS_PENDING_SOURCE,
                           in_class=None, at_home=None)


def mark_blank(quarter: int, week: int, subject: str, day: str, source_value: str | None = None) -> dict[str, Any]:
    return upsert_override(quarter, week, subject=subject, day=day,
                           source_value=source_value, status=STATUS_OWNER_CONFIRMED_BLANK,
                           in_class=[], at_home=None)


def command_self_test() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        import scripts.canvas_llm_intake.manifest as mfmod
        orig = mfmod.staging_dir
        mfmod.staging_dir = lambda q, w: Path(tmp) / f"q{q}w{w}"
        try:
            assert list_overrides(2, 3) == []
            upsert_override(2, 3, subject="math", day="Wednesday", source_value="Review",
                            in_class=["Review"], at_home="Study for tomorrow's test.", status=STATUS_PLANNED)
            rec = day_override(2, 3, "math", "Wednesday")
            assert rec["at_home"] == "Study for tomorrow's test."
            assert rec["source_value"] == "Review"
            assert rec["source"] == "OWNER_INPUT"
            assert len(rec["history"]) == 1

            # Update (not duplicate).
            upsert_override(2, 3, subject="math", day="Wednesday", at_home="Study harder.")
            rec2 = day_override(2, 3, "math", "Wednesday")
            assert rec2["at_home"] == "Study harder."
            assert len(rec2["history"]) == 2
            assert len(list_overrides(2, 3)) == 1

            # mark blank + pending.
            mark_blank(2, 3, "science", "Monday")
            assert day_override(2, 3, "science", "Monday")["status"] == STATUS_OWNER_CONFIRMED_BLANK
            mark_pending(2, 3, "language_arts", "Wednesday")
            assert day_override(2, 3, "language_arts", "Wednesday")["status"] == STATUS_PENDING_SOURCE

            # restore source deactivates.
            assert restore_source(2, 3, "math", "Wednesday") is True
            assert day_override(2, 3, "math", "Wednesday") is None
            assert restore_source(2, 3, "math", "Wednesday") is False

            # invalid status fails closed.
            try:
                upsert_override(2, 3, subject="math", day="Monday", status="BOGUS")
                raise AssertionError("expected ValueError")
            except ValueError:
                pass
        finally:
            mfmod.staging_dir = orig
    print("PASS intake owner-overrides self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
