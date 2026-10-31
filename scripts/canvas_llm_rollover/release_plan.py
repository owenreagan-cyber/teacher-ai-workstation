"""Owner-reviewed Friday release plan (pure; no Canvas I/O, no writes).

The canonical rollover instant is Friday 4:00 PM America/New_York. When that
window has already passed, the plan refuses to reuse the expired delayed-post
timestamp and records ``OWNER_PUBLICATION_TIME_REQUIRED`` until Owen selects a
new future publication time.

The plan always lists the five intended front-page targets (Math,
Reading/Spelling, Language Arts, Science, Homeroom) and their resolved Canvas
page ids. It never creates, mutates, or publishes anything.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from scripts.canvas_llm_intake import manifest as imf
from scripts.canvas_llm_intake import week_resolution as wr

from . import homeroom_weekly
from . import manifest as rollover_manifest
from . import schedule


def _page_target(subject: str, label: str, course_id: int | None, page_lookup: dict[str, Any]) -> dict[str, Any]:
    entry = (page_lookup or {}).get(subject, {})
    return {
        "subject": subject,
        "label": label,
        "course_id": course_id,
        "page_id": entry.get("page_id"),
        "page_slug": entry.get("url"),
        "page_status": entry.get("status", "UNRESOLVED"),
        "front_page_action": "SET_FRONT_PAGE",
    }


def build_release_plan(
    from_quarter: int,
    from_week: int,
    to_quarter: int,
    to_week: int,
    *,
    now: datetime | None = None,
    owner_publication_time: str | None = None,
) -> dict[str, Any]:
    """Build the deterministic release plan for one upcoming instructional week."""
    now = now or datetime.now(timezone.utc)
    manifest = rollover_manifest.build_rollover_manifest(
        from_quarter, from_week, to_quarter, to_week
    )
    to_entry = wr.find_week(to_quarter, to_week) or {}
    from scripts.instructional_weeks import week_range

    bounds = week_range(to_entry)
    if bounds is None:
        raise ValueError("target week dates are unavailable")
    resolved = schedule.resolve_publication_time(
        bounds[0].isoformat(), now=now, owner_selected_at=owner_publication_time,
    )

    intake_manifest = imf.load_manifest(to_quarter, to_week) or {}
    page_lookup = intake_manifest.get("page_lookup") or {}

    academic = []
    for course in manifest.get("academic_courses", []):
        subject = course["subject"]
        academic.append({
            **_page_target(subject, course["label"], course.get("course_id"), page_lookup),
            "page_body_hash": course.get("to_page_hash"),
            "approved": bool(course.get("approved")),
        })

    homeroom_resolution = homeroom_weekly.load_page_resolution(to_quarter, to_week) or {}
    homeroom_approval = homeroom_weekly.load_approval(to_quarter, to_week) or {}
    homeroom_page_id = homeroom_approval.get("page_id") or homeroom_resolution.get("page_id")
    homeroom_target = {
        "subject": "homeroom",
        "label": "Homeroom",
        "course_id": rollover_manifest.HOMEROOM_COURSE_ID,
        "page_id": homeroom_page_id,
        "page_slug": homeroom_resolution.get("slug") or homeroom_approval.get("page_slug"),
        "page_status": homeroom_resolution.get("status", "UNRESOLVED"),
        "page_resolution_method": homeroom_resolution.get("method", "NOT_RESOLVED"),
        "page_front_page": homeroom_resolution.get("front_page"),
        "front_page_action": "SET_FRONT_PAGE",
        "approved": bool((manifest.get("homeroom") or {}).get("approved")),
    }

    targets = academic + [homeroom_target]
    blockers: list[str] = []
    if resolved["requires_owner_time"]:
        blockers.append(
            "Owner-selected publication time required: the canonical Friday 4:00 PM "
            "America/New_York window has passed."
        )
    for target in targets:
        if target.get("course_id") is None:
            blockers.append(f"{target['label']}: no course mapping")
        if target.get("page_id") is None:
            blockers.append(f"{target['label']}: Canvas page id not resolved")
        if not target.get("approved"):
            blockers.append(f"{target['label']}: package not approved")
    if len(targets) != 5:
        blockers.append(f"front-page manifest must contain exactly 5 targets (found {len(targets)})")

    # Report the staged package size, not only approved deploy-plan items.
    from pathlib import Path
    import json as _json
    drafts = imf.staging_dir(to_quarter, to_week) / "drafts"
    def _count(name: str) -> int:
        try:
            return len(_json.loads((drafts / name).read_text(encoding="utf-8")))
        except (OSError, _json.JSONDecodeError, TypeError):
            return 0

    content_warnings: list[str] = []
    try:
        staged_assessments = _json.loads((drafts / "assessment-reminders.json").read_text(encoding="utf-8"))
    except (OSError, _json.JSONDecodeError, TypeError):
        staged_assessments = []
    for item in staged_assessments:
        if item.get("content_status") and item.get("content_status") != "READY":
            detail = "; ".join(item.get("blocked_sections") or []) or "source detail incomplete"
            content_warnings.append(
                f"{item.get('title')}: content_status={item['content_status']} ({detail})"
            )

    assignment_reconciliation = {}
    try:
        assignment_reconciliation = _json.loads(
            (imf.staging_dir(to_quarter, to_week) / "planner" / "assignment-reconciliation.json")
            .read_text(encoding="utf-8")
        )
    except (OSError, _json.JSONDecodeError, TypeError):
        assignment_reconciliation = {}
    for blocker in assignment_reconciliation.get("blockers") or []:
        blockers.append(f"assignment reconciliation: {blocker}")

    status = "OWNER_PUBLICATION_TIME_REQUIRED" if resolved["requires_owner_time"] else "READY_FOR_OWNER_REVIEW"
    if assignment_reconciliation.get("blockers"):
        status = "BLOCKED"

    return {
        "schemaVersion": 1,
        "from_week": manifest.get("from_week"),
        "to_week": manifest.get("to_week"),
        "timezone": schedule.NEW_YORK,
        "generated_at": now.astimezone(timezone.utc).isoformat(),
        "canonical_scheduled_at": resolved["canonical_scheduled_at"],
        "canonical_friday": resolved.get("canonical_friday"),
        "rollover_day": resolved.get("rollover_day"),
        "rollover_day_moved": resolved.get("rollover_day_moved"),
        "scheduled_at": resolved["scheduled_at"],
        "publication_time_source": resolved["source"],
        "publication_time_required": bool(resolved["requires_owner_time"]),
        "publication_time_reason": resolved["reason"],
        "owner_publication_time": owner_publication_time,
        "status": status,
        "front_page_targets": targets,
        "weekly_announcement_count": _count("announcements.json"),
        "assignment_count": _count("assignments.json"),
        "assessment_announcement_count": _count("assessment-reminders.json"),
        "homeroom_artifact_present": (drafts / "homeroom-page.html").exists(),
        "assignment_reconciliation": {
            "bundle_status": assignment_reconciliation.get("bundle_status", "NOT_RUN"),
            "execution_ready": assignment_reconciliation.get("execution_ready", False),
            "counts": assignment_reconciliation.get("counts", {}),
            "blockers": assignment_reconciliation.get("blockers", []),
            "pending_actions": assignment_reconciliation.get("pending_actions", []),
        },
        "content_warnings": content_warnings,
        "blockers": blockers,
        "ready_to_execute": False,  # never auto-executes; owner approval remains authoritative
        "canvas_writes": 0,
        "email_sends": 0,
    }


def write_release_plan(plan: dict[str, Any], *, to_quarter: int, to_week: int) -> str:
    """Persist a release plan under local (gitignored) staging."""
    import json

    path = imf.staging_dir(to_quarter, to_week) / "planner" / "rollover-release-plan.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return str(path)


def command_self_test() -> int:
    plan = build_release_plan(
        2, 3, 2, 4,
        now=datetime(2026, 10, 30, 21, 0, tzinfo=timezone.utc),
    )
    assert plan["to_week"] == "Q2W4"
    assert plan["publication_time_required"] is True
    assert plan["scheduled_at"] is None
    assert plan["canonical_scheduled_at"] == "2026-10-30T20:00:00Z"
    assert plan["status"] == "OWNER_PUBLICATION_TIME_REQUIRED"
    assert len(plan["front_page_targets"]) == 5
    assert {t["subject"] for t in plan["front_page_targets"]} == {
        "math", "reading_spelling", "language_arts", "science", "homeroom"
    }
    assert plan["canvas_writes"] == 0 and plan["email_sends"] == 0

    # An explicit future owner time resolves without reusing the expired instant.
    plan2 = build_release_plan(
        2, 3, 2, 4,
        now=datetime(2026, 10, 30, 21, 0, tzinfo=timezone.utc),
        owner_publication_time="2026-11-01T09:00:00-05:00",
    )
    assert plan2["publication_time_required"] is False
    assert plan2["scheduled_at"] == "2026-11-01T14:00:00Z"
    assert plan2["publication_time_source"] == "OWNER_SELECTED"

    # An upcoming week with a future canonical window uses Friday 4 PM.
    plan3 = build_release_plan(
        2, 4, 2, 5,
        now=datetime(2026, 10, 30, 21, 0, tzinfo=timezone.utc),
    )
    assert plan3["publication_time_required"] is False
    assert plan3["scheduled_at"] == "2026-11-06T21:00:00Z", plan3

    print("PASS canvas-rollover release-plan self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
