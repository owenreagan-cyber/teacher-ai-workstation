"""Review-first pacing resync for Canvas Planner.

Fresh source data is stored as a proposal. It never replaces the canonical
snapshot or drafts until Owen explicitly applies it.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.canvas_llm_intake import cycle, intake
from scripts.canvas_llm_intake import manifest as intake_manifest
from scripts.canvas_llm_intake import owner_overrides
from scripts.canvas_llm_phase3 import pacing_extractor

from .events import append_event


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def proposal_path(quarter: int, week: int) -> Path:
    return intake_manifest.staging_dir(quarter, week) / "planner" / "source-proposal.json"


def changes_path(quarter: int, week: int) -> Path:
    return intake_manifest.staging_dir(quarter, week) / "changes.json"


def _write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _affected(change: dict[str, Any]) -> list[str]:
    subject = str(change.get("subject") or "course")
    return [
        f"{subject} lesson plan",
        f"{subject} assignments",
        f"{subject} page",
        f"{subject} announcement",
    ]


def propose_from_normalized(
    quarter: int,
    week: int,
    *,
    normalized: dict[str, Any],
    source_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persist a source proposal without changing canonical packet files."""
    delta = cycle.detect_delta(quarter, week, normalized)
    overrides = owner_overrides.list_overrides(quarter, week)
    changed_subjects = {str(c.get("subject")) for c in delta.get("changes", [])}
    active = set((intake_manifest.load_manifest(quarter, week) or {}).get("subjects", {}).keys())
    proposal = {
        "schemaVersion": 1,
        "status": "PENDING_DECISION" if delta["delta"] == "CHANGED" else delta["delta"],
        "created_at": _now(),
        "quarter": quarter,
        "week": week,
        "delta": delta,
        "changed_cells": [
            {**change, "affects": _affected(change)} for change in delta.get("changes", [])
        ],
        "kept_overrides": [
            {"override_id": item.get("override_id"), "subject": item.get("subject"), "day": item.get("day")}
            for item in overrides
        ],
        "unchanged_subjects": sorted(active - changed_subjects),
        "normalized": normalized,
        "source_metadata": source_metadata or {},
        "decision": None,
    }
    _write(proposal_path(quarter, week), proposal)
    _write(changes_path(quarter, week), {
        "delta": delta,
        "changed_cells": proposal["changed_cells"],
        "kept_overrides": proposal["kept_overrides"],
        "unchanged_subjects": proposal["unchanged_subjects"],
        "decision": None,
        "proposed_at": proposal["created_at"],
    })
    append_event(
        intake_manifest.staging_dir(quarter, week),
        action="source_resync_proposed",
        actor="system",
        reason="Fresh pacing was compared with the canonical snapshot; no change was applied.",
        after={"delta": delta["delta"], "changed_cells": proposal["changed_cells"]},
    )
    return proposal


def resync(quarter: int, week: int, *, fresh: bool = True) -> dict[str, Any]:
    """Read pacing through the existing reader and save a review proposal."""
    rows, metadata = pacing_extractor.fetch_pacing(fresh=fresh)
    normalized = pacing_extractor.extract_week(rows, f"Q{quarter}W{week}", metadata)
    return propose_from_normalized(
        quarter, week, normalized=normalized, source_metadata=metadata
    )


def load_proposal(quarter: int, week: int) -> dict[str, Any] | None:
    try:
        value = json.loads(proposal_path(quarter, week).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def decide(quarter: int, week: int, *, decision: str) -> dict[str, Any]:
    """Apply the proposal or keep the current canonical packet."""
    choice = decision.upper()
    if choice not in ("APPLY", "KEEP"):
        raise ValueError("decision must be APPLY or KEEP")
    proposal = load_proposal(quarter, week)
    if not proposal or proposal.get("status") != "PENDING_DECISION":
        raise ValueError("no pending source proposal")
    before_manifest = intake_manifest.load_manifest(quarter, week) or {}
    if choice == "APPLY":
        summary = intake.build_intake(
            quarter=quarter,
            week=week,
            fresh=False,
            canvas=None,
            include_canvas_context=False,
            normalized_override=proposal["normalized"],
            source_meta_override=proposal.get("source_metadata") or {},
        )
        status = "APPLIED"
    else:
        summary = {
            "week_code": before_manifest.get("week_code", f"Q{quarter}W{week}"),
            "source_hash": before_manifest.get("source_hash"),
            "kept_current_plan": True,
        }
        status = "KEPT"
    proposal["status"] = status
    proposal["decision"] = status
    proposal["decided_at"] = _now()
    proposal.pop("normalized", None)
    _write(proposal_path(quarter, week), proposal)
    changes = {
        "delta": proposal.get("delta") or {},
        "changed_cells": proposal.get("changed_cells") or [],
        "kept_overrides": proposal.get("kept_overrides") or [],
        "unchanged_subjects": proposal.get("unchanged_subjects") or [],
        "decision": status,
        "decided_at": proposal["decided_at"],
    }
    _write(changes_path(quarter, week), changes)
    append_event(
        intake_manifest.staging_dir(quarter, week),
        action="source_change_applied" if choice == "APPLY" else "source_change_kept_current",
        actor="owner",
        reason="Owen applied the reviewed pacing change." if choice == "APPLY" else "Owen kept the current plan.",
        before={"source_hash": before_manifest.get("source_hash")},
        after={"source_hash": summary.get("source_hash"), "decision": status},
        undo={"supported": choice == "KEEP", "action": "reopen_source_proposal"},
    )
    return {"decision": status, "summary": summary, "changes": changes}
