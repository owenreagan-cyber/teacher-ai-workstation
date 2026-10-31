"""Live assignment reconciliation for the staged weekly release bundle.

GET-only. Every proposed assignment is compared against the actual Canvas
assignment object:

    course, title, group, due date/time, points, grading type, submission
    types, ``omit_from_final_grade``, and published state.

Classifications:

* ``MATCH``             — one live assignment, all required fields agree.
* ``UPDATE_REQUIRED``   — one live assignment, one or more fields differ; the
                          exact correction is staged in the report.
* ``CREATE_REQUIRED``   — no live assignment with this exact title.
* ``DUPLICATE``         — more than one live assignment with this exact title.
* ``UNVERIFIED``        — Canvas GET failed or a required field is missing.

``DUPLICATE`` and ``UNVERIFIED`` block the release bundle. ``CREATE_REQUIRED``
and ``UPDATE_REQUIRED`` are pending actions, not hidden successes. No Canvas
writes are performed.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from . import manifest as mf

NEW_YORK = "America/New_York"


def _due_utc(date_str: str, timezone_name: str = NEW_YORK) -> datetime | None:
    if not date_str:
        return None
    try:
        y, m, d = (int(x) for x in str(date_str).split("-"))
        local = datetime(y, m, d, 23, 59, tzinfo=ZoneInfo(timezone_name))
    except (ValueError, TypeError):
        return None
    return local.astimezone(ZoneInfo("UTC"))


def _parse_utc(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(
            ZoneInfo("UTC")
        )
    except ValueError:
        return None


def _minute(value: datetime | None) -> datetime | None:
    return value.replace(second=0, microsecond=0) if value else None


def _submission_types(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    return list(value or [])


def _live_summary(
    assignment: dict[str, Any] | None, group_name: str | None
) -> dict[str, Any] | None:
    if assignment is None:
        return None
    return {
        "assignment_id": assignment.get("id"),
        "course_id": assignment.get("course_id"),
        "title": assignment.get("name") or assignment.get("title"),
        "assignment_group": group_name,
        "assignment_group_id": assignment.get("assignment_group_id"),
        "due_at": assignment.get("due_at"),
        "points_possible": assignment.get("points_possible"),
        "grading_type": assignment.get("grading_type"),
        "submission_types": _submission_types(assignment.get("submission_types")),
        "omit_from_final_grade": assignment.get("omit_from_final_grade"),
        "published": assignment.get("published"),
    }


def _compare(
    proposal: dict[str, Any],
    live: dict[str, Any],
    group_name: str | None,
) -> tuple[list[str], dict[str, Any], list[str]]:
    differences: list[str] = []
    corrections: dict[str, Any] = {}
    unverified: list[str] = []

    expected_due = _minute(_due_utc(proposal.get("due_date", "")))
    actual_due = _minute(_parse_utc(live.get("due_at")))
    if expected_due is None:
        unverified.append("proposal due_date")
    elif actual_due is None:
        unverified.append("live due_at")
    elif expected_due != actual_due:
        differences.append("due_at")
        corrections["due_at"] = {
            "actual": live.get("due_at"),
            "required": expected_due.isoformat().replace("+00:00", "Z"),
        }

    expected_group = str(proposal.get("assignment_group") or "")
    if group_name is None:
        unverified.append("live assignment_group")
    elif str(group_name) != expected_group:
        differences.append("assignment_group")
        corrections["assignment_group"] = {"actual": group_name, "required": expected_group}

    expected_points = float(proposal.get("points_possible") or 0)
    actual_points = live.get("points_possible")
    if actual_points is None:
        unverified.append("live points_possible")
    elif float(actual_points) != expected_points:
        differences.append("points_possible")
        corrections["points_possible"] = {"actual": actual_points, "required": expected_points}

    expected_grading = str(proposal.get("grading_type") or "percent")
    actual_grading = live.get("grading_type")
    if actual_grading is None:
        unverified.append("live grading_type")
    elif str(actual_grading) != expected_grading:
        differences.append("grading_type")
        corrections["grading_type"] = {"actual": actual_grading, "required": expected_grading}

    expected_submission = _submission_types(proposal.get("submission_types"))
    actual_submission = _submission_types(live.get("submission_types"))
    if not actual_submission:
        unverified.append("live submission_types")
    elif "on_paper" not in actual_submission:
        differences.append("submission_types")
        corrections["submission_types"] = {
            "actual": actual_submission, "required": ["on_paper"],
        }

    expected_omit = bool(proposal.get("omit_from_final_grade", False))
    actual_omit = live.get("omit_from_final_grade")
    if actual_omit is None:
        # This is the canonical Canvas inclusion field. Never infer it from an
        # internal reporting field.
        unverified.append("live omit_from_final_grade")
    elif bool(actual_omit) != expected_omit:
        differences.append("omit_from_final_grade")
        corrections["omit_from_final_grade"] = {"actual": actual_omit, "required": expected_omit}

    if live.get("published") is None:
        unverified.append("live published")
    elif live.get("published") is not True:
        differences.append("published")
        corrections["published"] = {"actual": live.get("published"), "required": True}

    return differences, corrections, unverified


def reconcile(
    quarter: int,
    week: int,
    *,
    client: Any,
    proposals: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Reconcile staged assignments against live Canvas (GET-only)."""
    week_code = f"Q{quarter}W{week}"
    if proposals is None:
        path = mf.staging_dir(quarter, week) / "drafts" / "assignments.json"
        try:
            proposals = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            proposals = []

    courses: dict[int, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []
    counts = {
        "MATCH": 0,
        "UPDATE_REQUIRED": 0,
        "CREATE_REQUIRED": 0,
        "DUPLICATE": 0,
        "UNVERIFIED": 0,
    }
    blockers: list[str] = []
    pending_actions: list[str] = []

    for proposal in proposals:
        cid = proposal.get("course_id")
        title = proposal.get("title", "")
        if cid is None:
            results.append({
                "course": proposal.get("course"),
                "course_id": None,
                "title": title,
                "classification": "UNVERIFIED",
                "reason": "missing course_id",
                "live": None,
            })
            counts["UNVERIFIED"] += 1
            blockers.append(f"{title}: missing course_id")
            continue

        if cid not in courses:
            try:
                course = client.get_course(int(cid))
                groups = client.list_assignment_groups(int(cid))
                assignments = client.list_assignments(int(cid))
            except Exception as exc:  # noqa: BLE001
                courses[cid] = {
                    "error": type(exc).__name__,
                    "groups": {}, "assignments": [],
                }
            else:
                courses[cid] = {
                    "course": course,
                    "groups": {g.get("id"): g.get("name") for g in groups},
                    "assignments": assignments,
                }

        cache = courses[cid]
        if cache.get("error") or not cache.get("course"):
            results.append({
                "course": proposal.get("course"),
                "course_id": cid,
                "title": title,
                "classification": "UNVERIFIED",
                "reason": "Canvas course/assignment GET unavailable",
                "live": None,
            })
            counts["UNVERIFIED"] += 1
            blockers.append(f"{title}: Canvas GET unavailable")
            continue

        matches = [
            assignment for assignment in cache["assignments"]
            if (assignment.get("name") or assignment.get("title")) == title
        ]
        if len(matches) > 1:
            results.append({
                "course": proposal.get("course"),
                "course_id": cid,
                "title": title,
                "classification": "DUPLICATE",
                "reason": f"{len(matches)} live assignments share this exact title",
                "live": [
                    _live_summary(a, cache["groups"].get(a.get("assignment_group_id")))
                    for a in matches
                ],
            })
            counts["DUPLICATE"] += 1
            blockers.append(f"{title}: duplicate live assignments")
            continue

        if not matches:
            results.append({
                "course": proposal.get("course"),
                "course_id": cid,
                "title": title,
                "classification": "CREATE_REQUIRED",
                "reason": "no live assignment with this exact title",
                "live": None,
                "proposed": {
                    "assignment_group": proposal.get("assignment_group"),
                    "due_date": proposal.get("due_date"),
                    "points_possible": proposal.get("points_possible"),
                    "grading_type": proposal.get("grading_type"),
                    "submission_types": proposal.get("submission_types"),
                    "omit_from_final_grade": proposal.get("omit_from_final_grade"),
                },
            })
            counts["CREATE_REQUIRED"] += 1
            pending_actions.append(f"CREATE {title}")
            continue

        live = matches[0]
        group_name = cache["groups"].get(live.get("assignment_group_id"))
        differences, corrections, unverified = _compare(proposal, live, group_name)
        if unverified:
            classification = "UNVERIFIED"
            counts["UNVERIFIED"] += 1
            blockers.append(f"{title}: missing Canvas field(s): {', '.join(unverified)}")
        elif differences:
            classification = "UPDATE_REQUIRED"
            counts["UPDATE_REQUIRED"] += 1
            pending_actions.append(f"UPDATE {title}: {', '.join(differences)}")
        else:
            classification = "MATCH"
            counts["MATCH"] += 1
        results.append({
            "course": proposal.get("course"),
            "course_id": cid,
            "title": title,
            "classification": classification,
            "differences": differences,
            "corrections": corrections,
            "unverified_fields": unverified,
            "live": _live_summary(live, group_name),
            "proposed": {
                "assignment_group": proposal.get("assignment_group"),
                "due_date": proposal.get("due_date"),
                "points_possible": proposal.get("points_possible"),
                "grading_type": proposal.get("grading_type"),
                "submission_types": proposal.get("submission_types"),
                "omit_from_final_grade": proposal.get("omit_from_final_grade"),
            },
        })

    return {
        "schemaVersion": 1,
        "week_code": week_code,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "proposal_count": len(proposals),
        "results": results,
        "counts": counts,
        "blockers": blockers,
        "pending_actions": pending_actions,
        "bundle_status": "BLOCKED" if blockers else "READY_FOR_APPROVAL",
        "execution_ready": False if blockers or pending_actions else True,
        "canvas_writes": 0,
    }


def write_report(report: dict[str, Any], *, quarter: int, week: int) -> Path:
    path = mf.staging_dir(quarter, week) / "planner" / "assignment-reconciliation.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def command_self_test() -> int:
    # Pure comparison tests (no Canvas I/O).
    proposal = {
        "course": "language_arts", "course_id": 28171, "title": "Classroom Practice 27",
        "assignment_group": "Classwork", "due_date": "2026-11-04",
        "points_possible": 100, "grading_type": "percent",
        "submission_types": "on_paper", "omit_from_final_grade": False,
    }
    live = {
        "id": "1", "course_id": 28171, "name": "Classroom Practice 27",
        "assignment_group_id": "g1", "due_at": "2026-10-31T03:59:00Z",
        "points_possible": 100.0, "grading_type": "percent",
        "submission_types": ["on_paper"], "omit_from_final_grade": False,
        "published": True,
    }
    diffs, corrections, unverified = _compare(proposal, live, "Classwork")
    assert diffs == ["due_at"], diffs
    assert corrections["due_at"]["required"] == "2026-11-05T04:59:00Z", corrections
    assert unverified == []

    matched = dict(live, due_at="2026-11-05T04:59:00Z")
    diffs2, corrections2, unverified2 = _compare(proposal, matched, "Classwork")
    assert diffs2 == [] and corrections2 == {} and unverified2 == [], (diffs2, unverified2)

    # Missing omit_from_final_grade must be UNVERIFIED, never inferred.
    missing = dict(matched)
    missing.pop("omit_from_final_grade")
    _, _, unverified3 = _compare(proposal, missing, "Classwork")
    assert "live omit_from_final_grade" in unverified3

    print("PASS assignment reconciliation self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
