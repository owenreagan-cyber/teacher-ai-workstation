"""One weekly Canvas release: discover, review, approve, publish, recover.

This module does not publish by itself. Publication calls
``rollover.publish_weekly_package`` / ``rollover.execute``, which remain the
only weekly writer. Read-only reconciliation classifies CREATE, UPDATE, SKIP,
and BLOCKED. It does not create a second Canvas transport.
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from scripts.canvas_llm_deploy import ledger as deploy_ledger
from scripts.canvas_llm_deploy import plan as deploy_plan
from scripts.canvas_llm_deploy.live_authorization import (
    ELA_COURSE_ID,
    HOMEROOM_COURSE_ID,
    MATH_COURSE_ID,
    READING_COURSE_ID,
    SCIENCE_COURSE_ID,
    SCHOOL_YEAR,
    LiveAuthorizationError,
    authorize_live_transport,
    require_scoped_live_transport,
)
from scripts.canvas_llm_intake import approval, manifest as intake_manifest
from scripts.canvas_llm_intake import constants as intake_constants
from scripts.canvas_llm_intake import week_resolution as weeks
from scripts.canvas_llm_rollover import homeroom_weekly, ledger as rollover_ledger
from scripts.canvas_llm_rollover import manifest as rollover_manifest
from scripts.canvas_llm_rollover import rollover, schedule
from scripts.canvas_planner.approval_bundle import current_bundle
from scripts.instructional_weeks import week_range
from scripts.teacher_workstation.adapter import latest_completed

NEW_YORK = ZoneInfo("America/New_York")
COURSE_IDS = {
    "math": MATH_COURSE_ID,
    "reading_spelling": READING_COURSE_ID,
    "language_arts": ELA_COURSE_ID,
    "science": SCIENCE_COURSE_ID,
    "homeroom": HOMEROOM_COURSE_ID,
}
RELEASE_COURSES = ("math", "reading_spelling", "language_arts", "science", "homeroom")

NOT_STARTED = "NOT_STARTED"
PREPARED = "PREPARED"
AWAITING_APPROVAL = "AWAITING_APPROVAL"
APPROVED = "APPROVED"
PREFLIGHT_BLOCKED = "PREFLIGHT_BLOCKED"
PARTIALLY_PUBLISHED = "PARTIALLY_PUBLISHED"
PUBLICATION_VERIFIED = "PUBLICATION_VERIFIED"
ROLLOVER_INCOMPLETE = "ROLLOVER_INCOMPLETE"
FULLY_COMPLETED = "FULLY_COMPLETED"

_ACTIONS = {
    "CREATE": "CREATE",
    "NEW": "CREATE",
    "PRIOR_WEEK_SAME_TITLE": "CREATE",
    "UPDATE": "UPDATE",
    "UPDATE_REQUIRED": "UPDATE",
    "BODY_CHANGED_SAME_WEEK": "UPDATE",
    "SET_FRONT_PAGE": "UPDATE",
    "SKIP": "SKIP",
    "EXACT_MATCH": "SKIP",
    "ALREADY_SCHEDULED_VERIFIED": "SKIP",
    "BLOCKED": "BLOCKED",
    "DUPLICATE": "BLOCKED",
    "UNVERIFIED": "BLOCKED",
}


class ReleaseBlocked(RuntimeError):
    """The weekly release cannot continue. No Canvas write was authorized."""


def _clock(now: datetime | None) -> datetime:
    clock = now or datetime.now(NEW_YORK)
    if clock.tzinfo is None:
        raise ReleaseBlocked("the release clock must include a timezone")
    return clock


def _previous_week(quarter: int, week: int) -> tuple[int, int]:
    ordered = sorted(
        (item for item in weeks.load_weeks() if weeks._week_start(item) is not None),
        key=lambda item: weeks._week_start(item),
    )
    code = weeks.week_code_for(quarter, week)
    index = next((i for i, item in enumerate(ordered) if item.get("code") == code), None)
    if index is None or index == 0:
        raise ReleaseBlocked(f"no prior instructional week for {code}")
    previous = ordered[index - 1]
    return int(previous["quarter"]), int(previous["week"])


def discover(
    *,
    today: date | None = None,
    now: datetime | None = None,
    quarter: int | None = None,
    week: int | None = None,
) -> dict[str, Any]:
    """Resolve the target week from the instructional-week calendar."""
    clock = _clock(now)
    today = today or clock.astimezone(NEW_YORK).date()
    if quarter is None or week is None:
        try:
            quarter, week = weeks.current_week(today)
            selection = "current_instructional_week"
        except RuntimeError:
            quarter, week = weeks.next_week(today)
            selection = "next_instructional_week"
    else:
        selection = "explicit"
    entry = weeks.find_week(quarter, week) or {}
    bounds = week_range(entry)
    if bounds is None:
        raise ReleaseBlocked(f"{weeks.week_code_for(quarter, week)} has no instructional dates")
    start, end = bounds
    instructional = []
    cursor = start
    while cursor <= end:
        if cursor.weekday() < 5:
            instructional.append(cursor.isoformat())
        cursor += timedelta(days=1)
    gap = None
    try:
        previous_quarter, previous_week = _previous_week(quarter, week)
        previous = weeks.find_week(previous_quarter, previous_week) or {}
        previous_bounds = week_range(previous)
        if previous_bounds is not None and previous_bounds[1] + timedelta(days=1) < start:
            gap_start = previous_bounds[1] + timedelta(days=1)
            gap_end = start - timedelta(days=1)
            cursor = gap_start
            contains_weekday = False
            while cursor <= gap_end:
                if cursor.weekday() < 5:
                    contains_weekday = True
                    break
                cursor += timedelta(days=1)
            if contains_weekday:
                gap = {
                    "start": gap_start.isoformat(),
                    "end": gap_end.isoformat(),
                    "kind": "gap_between_instructional_weeks",
                    "after": previous.get("code"),
                    "before": entry.get("code"),
                }
    except ReleaseBlocked:
        gap = None
    publication = schedule.resolve_publication_time(start.isoformat(), now=clock)
    subjects = intake_constants.active_subject_keys_for_quarter(quarter) + ["homeroom"]
    return {
        "school_year": SCHOOL_YEAR,
        "quarter": quarter,
        "week": week,
        "week_code": weeks.week_code_for(quarter, week),
        "selection": selection,
        "calendar_source": "config/curriculum/canvas/instructional-weeks-2026-2027.json",
        "date_range": {"start": start.isoformat(), "end": end.isoformat()},
        "instructional_days": instructional,
        "instructional_break": gap,
        "subjects": subjects,
        "publication": publication,
        "friday_publication_valid": not publication["requires_owner_time"],
        "timezone": "America/New_York",
    }


def _artifact_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for course in manifest.get("academic_courses") or []:
        rows.append({
            "kind": "weekly_page",
            "subject": course.get("subject"),
            "course_id": course.get("course_id"),
            "title": course.get("label"),
            "action": _ACTIONS.get(str(course.get("page_body_action") or "UPDATE"), "BLOCKED"),
            "content_hash": course.get("to_page_hash"),
        })
    home = manifest.get("homeroom") or {}
    if not home or not (home.get("body") or home.get("proposed_content") or home.get("proposed_content_hash")):
        rows.append({
            "kind": "homeroom_page",
            "subject": "homeroom",
            "course_id": HOMEROOM_COURSE_ID,
            "title": "Homeroom",
            "action": "BLOCKED",
            "reason": "homeroom content is missing",
        })
    else:
        rows.append({
            "kind": "homeroom_page",
            "subject": "homeroom",
            "course_id": home.get("course_id"),
            "title": "Homeroom",
            "action": _ACTIONS.get(str(home.get("page_body_action") or "UPDATE"), "BLOCKED"),
            "content_hash": home.get("proposed_content_hash"),
        })
    for item in manifest.get("weekly_announcements") or []:
        rows.append({
            "kind": "weekly_announcement",
            "subject": item.get("subject"),
            "course_id": item.get("course_id"),
            "title": item.get("title"),
            "delayed_post_at": item.get("delayed_post_at"),
            "action": _ACTIONS.get(str(item.get("classification") or item.get("action") or "CREATE"), "BLOCKED"),
            "agenda_hash": item.get("agenda_hash"),
        })
    for item in manifest.get("assessment_reminders") or []:
        rows.append({
            "kind": "assessment_notice",
            "subject": item.get("subject"),
            "course_id": item.get("course_id"),
            "title": item.get("title"),
            "assessment_date": item.get("assessment_date"),
            "delayed_post_at": item.get("delayed_post_at"),
            "action": _ACTIONS.get(str(item.get("classification") or item.get("action") or "CREATE"), "BLOCKED"),
        })
    for item in manifest.get("assignments") or []:
        rows.append({
            "kind": "assignment",
            "subject": item.get("course") or item.get("subject"),
            "course_id": item.get("course_id"),
            "title": item.get("title"),
            "due_at": item.get("due_utc") or item.get("due_at"),
            "action": _ACTIONS.get(str(item.get("classification") or item.get("action") or "CREATE"), "BLOCKED"),
        })
    family = manifest.get("homeroom_announcement") or {}
    if family:
        rows.append({
            "kind": "family_announcement",
            "subject": "homeroom",
            "course_id": family.get("course_id"),
            "title": family.get("title"),
            "delayed_post_at": family.get("delayed_post_at"),
            "action": _ACTIONS.get(str(family.get("action") or "CREATE"), "BLOCKED"),
        })
    return rows


def build_package(
    quarter: int,
    week: int,
    *,
    now: datetime | None = None,
    owner_publication_time: str | None = None,
) -> dict[str, Any]:
    """Assemble the staged week. Missing drafts stay missing; nothing is invented."""
    clock = _clock(now)
    target = discover(quarter=quarter, week=week, now=clock)
    from_quarter, from_week = _previous_week(quarter, week)
    manifest = rollover_manifest.build_rollover_manifest(
        from_quarter, from_week, quarter, week, now=clock,
    )
    if owner_publication_time:
        manifest["owner_publication_time"] = owner_publication_time
    plan = deploy_plan.build_plan(
        quarter, week, now=clock, owner_publication_time=owner_publication_time,
    )
    rows = _artifact_rows(manifest)
    blockers = [row["reason"] for row in rows if row.get("reason")]
    if manifest.get("source_hash") != plan.get("source_hash"):
        blockers.append("rollover source hash does not match the deploy plan")
    return {
        "target": target,
        "from_week": manifest.get("from_week"),
        "to_week": manifest.get("to_week"),
        "source_hash": manifest.get("source_hash") or "",
        "agenda_hash": manifest.get("agenda_hash") or "",
        "plan_fingerprint": plan.get("plan_fingerprint"),
        "publication_time": manifest.get("scheduled_at") or owner_publication_time,
        "artifacts": rows,
        "warnings": [],
        "blockers": blockers,
        "manifest": manifest,
        "plan": {
            "weekly_announcements": len(plan.get("weekly_announcements") or []),
            "assessment_reminders": len(plan.get("assessment_reminders") or []),
            "assignments": len(plan.get("assignments") or []),
            "pages": len(plan.get("pages") or []),
        },
    }


def reconcile(manifest: dict[str, Any], client: Any, *, quarter: int, week: int) -> dict[str, Any]:
    """GET-only comparison. The client performs no publication."""
    from_quarter, from_week = _previous_week(quarter, week)
    before = _write_counts(client)
    result = rollover.run_preflight(
        from_quarter, from_week, quarter, week, client, manifest_override=manifest,
    )
    after = _write_counts(client)
    if after != before:
        raise ReleaseBlocked("reconciliation performed a Canvas write")
    rows = _artifact_rows(result["manifest"])
    return {
        "ready": bool(result.get("ready")),
        "blockers": list(result.get("blockers") or []),
        "warnings": list(result.get("warnings") or []),
        "artifacts": rows,
        "canvas_writes": 0,
    }


def review_package(package: dict[str, Any], reconciliation: dict[str, Any] | None = None) -> dict[str, Any]:
    """Owner-facing release. Artifact bodies stay in the staged files."""
    artifacts = reconciliation["artifacts"] if reconciliation else package["artifacts"]
    blockers = list(package.get("blockers") or [])
    if reconciliation:
        blockers.extend(reconciliation.get("blockers") or [])
    return {
        "week_code": package.get("to_week"),
        "school_year": SCHOOL_YEAR,
        "courses": list(RELEASE_COURSES),
        "source_hash": package.get("source_hash"),
        "agenda_hash": package.get("agenda_hash"),
        "plan_fingerprint": package.get("plan_fingerprint"),
        "publication_time": package.get("publication_time"),
        "friday_publication_valid": (package.get("target") or {}).get("friday_publication_valid"),
        "instructional_break": (package.get("target") or {}).get("instructional_break"),
        "artifacts": [
            {key: row.get(key) for key in (
                "kind", "subject", "course_id", "title", "action",
                "assessment_date", "delayed_post_at", "due_at", "reason",
            ) if row.get(key) not in (None, "")}
            for row in artifacts
        ],
        "counts": _count_actions(artifacts),
        "warnings": list(package.get("warnings") or []) + list((reconciliation or {}).get("warnings") or []),
        "blockers": blockers,
        "approval_phrase": f"APPROVE {package.get('to_week')}",
        "publish_phrase": f"ROLLOVER {package.get('to_week')}",
    }


def _count_actions(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"CREATE": 0, "UPDATE": 0, "SKIP": 0, "BLOCKED": 0}
    for row in rows:
        action = row.get("action")
        if action in counts:
            counts[action] += 1
    return counts


def _write_counts(client: Any) -> dict[str, int]:
    counts = getattr(client, "_write_counts", {}) or {}
    return {verb: int(counts.get(verb) or 0) for verb in ("POST", "PUT", "PATCH", "DELETE")}


def release_state(quarter: int, week: int) -> dict[str, Any]:
    """Map the existing ledgers and approval manifest onto one recovery state."""
    intake = intake_manifest.load_manifest(quarter, week) or {}
    published = deploy_ledger.load_published_verified(quarter, week)
    stored = rollover_ledger.load_rollover_ledger(quarter, week)
    code = weeks.week_code_for(quarter, week)
    if rollover._publication_records_agree(stored, published, intake):
        state = FULLY_COMPLETED
    elif (
        isinstance(published, dict) and published.get("status") == "PUBLISHED_VERIFIED"
        and intake.get("status") == "PUBLISHED_VERIFIED"
    ):
        state = ROLLOVER_INCOMPLETE
    elif isinstance(stored, dict) and stored.get("lifecycle") == "PUBLICATION_VERIFIED_ROLLOVER_INCOMPLETE":
        state = ROLLOVER_INCOMPLETE
    elif isinstance(published, dict) and published.get("status") == "PUBLISHED_VERIFIED":
        state = PUBLICATION_VERIFIED
    elif isinstance(stored, dict) and stored.get("lifecycle") in {
        schedule.BLOCKED, "FINALIZATION_BLOCKED", "FINALIZATION_INCOMPLETE",
    }:
        state = PARTIALLY_PUBLISHED
    elif intake.get("status") == "READY_TO_PUBLISH" and intake.get("approval_state") == "APPROVED":
        state = APPROVED
    elif intake.get("source_hash") and intake.get("approval_state") not in (None, "APPROVED"):
        state = AWAITING_APPROVAL
    elif intake:
        state = PREPARED
    else:
        state = NOT_STARTED
    return {
        "week_code": code,
        "state": state,
        "source_hash": intake.get("source_hash"),
        "plan_fingerprint": intake.get("plan_fingerprint"),
        "intake_status": intake.get("status"),
        "approval_state": intake.get("approval_state"),
        "published_status": None if not isinstance(published, dict) else published.get("status"),
        "rollover_lifecycle": None if not isinstance(stored, dict) else stored.get("lifecycle"),
    }


def _stable_approval(
    quarter: int,
    week: int,
    *,
    source_hash: str,
    owner_publication_time: str,
    now: datetime,
) -> str:
    subjects = intake_constants.active_subject_keys_for_quarter(quarter)
    fingerprint = ""
    for _ in range(3):
        plan = deploy_plan.build_plan(
            quarter, week, now=now, owner_publication_time=owner_publication_time,
        )
        fingerprint = str(plan.get("plan_fingerprint") or "")
        for subject in subjects:
            hashes = current_bundle(quarter, week, subject)["hashes"]
            for kind in approval.GRANULARITIES:
                digest = str(hashes.get(kind) or "")
                if kind == "assessment_reminder" and not digest:
                    approval.mark_not_required(
                        quarter, week, subject, kind, subjects=subjects,
                        reason="no assessment notice in this release",
                    )
                    continue
                if not digest:
                    raise ReleaseBlocked(f"{subject} {kind} has no draft to approve")
                approval.approve_artifact(
                    quarter, week, subject, kind,
                    draft_hash=digest, source_hash=source_hash, subjects=subjects,
                    plan_fingerprint=fingerprint,
                    owner_publication_time=owner_publication_time,
                    course_id=COURSE_IDS[subject],
                )
    plan = deploy_plan.build_plan(
        quarter, week, now=now, owner_publication_time=owner_publication_time,
    )
    if plan.get("plan_fingerprint") != fingerprint:
        raise ReleaseBlocked("approval did not settle on one plan fingerprint")
    return fingerprint


def approve_release(
    quarter: int,
    week: int,
    *,
    confirmation: str,
    owner_publication_time: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Record one package approval as granular, hash-bound artifact approvals."""
    clock = _clock(now)
    code = weeks.week_code_for(quarter, week)
    if (confirmation or "").strip() != f"APPROVE {code}":
        raise ReleaseBlocked(f"type exactly: APPROVE {code}")
    if not owner_publication_time:
        raise ReleaseBlocked("owner publication time is required")
    intake = intake_manifest.load_manifest(quarter, week) or {}
    source_hash = str(intake.get("source_hash") or "")
    if not source_hash:
        raise ReleaseBlocked("the intake source hash is missing")
    html_path = homeroom_weekly.html_path(quarter, week)
    if not html_path.is_file():
        raise ReleaseBlocked("homeroom page content is missing")
    family_path = intake_manifest.staging_dir(quarter, week) / homeroom_weekly.ANNOUNCEMENT_FILE
    if not family_path.is_file():
        raise ReleaseBlocked("homeroom family announcement is missing")
    resolution = homeroom_weekly.load_page_resolution(quarter, week) or {}
    if not resolution.get("page_id") or not resolution.get("page_slug"):
        raise ReleaseBlocked("homeroom page identity is not recorded")
    fingerprint = _stable_approval(
        quarter, week, source_hash=source_hash,
        owner_publication_time=owner_publication_time, now=clock,
    )
    html = html_path.read_text(encoding="utf-8")
    digest = homeroom_weekly._sha(html)
    homeroom_weekly.record_approval(
        quarter, week, page_id=int(resolution["page_id"]),
        page_slug=str(resolution["page_slug"]), week_code_value=code,
        source_body_hash=digest, approved_body_hash=digest, body=html,
    )
    family = json.loads(family_path.read_text(encoding="utf-8"))
    family["approval_state"] = "APPROVED"
    family["approved"] = True
    homeroom_weekly.write_family_announcement(quarter, week, family)
    intake["approval_state"] = "APPROVED"
    intake["ready_to_publish"] = True
    intake["status"] = "READY_TO_PUBLISH"
    intake["plan_fingerprint"] = fingerprint
    intake_manifest.save_manifest(quarter, week, intake)
    return {
        "state": APPROVED,
        "week_code": code,
        "source_hash": source_hash,
        "plan_fingerprint": fingerprint,
        "owner_publication_time": owner_publication_time,
    }


def invalidate_changed_artifacts(
    quarter: int,
    week: int,
    *,
    plan_fingerprint: str | None = None,
) -> bool:
    """Drop granular approval when a draft, source, or plan fingerprint changed."""
    subjects = intake_constants.active_subject_keys_for_quarter(quarter)
    intake = intake_manifest.load_manifest(quarter, week) or {}
    data = approval.load_approvals(quarter, week, subjects)
    changed = False
    for subject in subjects:
        hashes = current_bundle(quarter, week, subject)["hashes"]
        changed = approval.invalidate_if_stale(
            data, subject=subject, draft_hashes=hashes,
            source_hash=intake.get("source_hash"),
            plan_fingerprint=plan_fingerprint,
        ) or changed
    if changed:
        approval.save_approvals(quarter, week, data)
        if intake.get("approval_state") == "APPROVED":
            intake["approval_state"] = "PENDING"
            intake["ready_to_publish"] = False
            intake["status"] = "READY_FOR_REVIEW"
            intake_manifest.save_manifest(quarter, week, intake)
    return changed


def publish_release(
    quarter: int,
    week: int,
    *,
    client: Any,
    confirmation: str,
    now: datetime | None = None,
    manifest: dict[str, Any] | None = None,
    owner_publication_time: str | None = None,
) -> dict[str, Any]:
    """Run the existing rollover publisher after the local gates agree."""
    clock = _clock(now)
    code = weeks.week_code_for(quarter, week)
    if (confirmation or "").strip() != f"ROLLOVER {code}":
        raise ReleaseBlocked(f"type exactly: ROLLOVER {code}")
    if client is None:
        raise ReleaseBlocked("publication requires an explicit Canvas client")
    from_quarter, from_week = _previous_week(quarter, week)
    intake = intake_manifest.load_manifest(quarter, week) or {}
    published = deploy_ledger.load_published_verified(quarter, week)
    stored = rollover_ledger.load_rollover_ledger(quarter, week)
    if rollover._publication_records_agree(stored, published, intake):
        return {
            "lifecycle": schedule.PUBLISHED_VERIFIED,
            "state": FULLY_COMPLETED,
            "already_complete": True,
            "canvas_writes": 0,
            "chief_of_staff": latest_completed(),
        }
    if (
        intake.get("status") == "PUBLISHED_VERIFIED"
        and isinstance(published, dict)
        and published.get("status") == "PUBLISHED_VERIFIED"
        and published.get("source_hash") == intake.get("source_hash")
        and published.get("plan_fingerprint") == intake.get("plan_fingerprint")
    ):
        restored = rollover._restore_rollover_completion(quarter, week, published, intake)
        restored["state"] = release_state(quarter, week)["state"]
        restored["canvas_writes"] = 0
        restored["chief_of_staff"] = latest_completed()
        return restored
    if manifest is None:
        manifest = rollover_manifest.build_rollover_manifest(
            from_quarter, from_week, quarter, week, now=clock,
        )
    if owner_publication_time:
        manifest["owner_publication_time"] = owner_publication_time
    if manifest.get("source_hash") != intake.get("source_hash"):
        raise ReleaseBlocked("manifest source hash does not match the intake manifest")
    if manifest.get("plan_fingerprint") != intake.get("plan_fingerprint"):
        raise ReleaseBlocked("manifest plan fingerprint does not match the intake manifest")
    publication_time = str(manifest.get("owner_publication_time") or manifest.get("scheduled_at") or "")
    try:
        publication_at = datetime.fromisoformat(publication_time.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReleaseBlocked("publication time is not a valid timestamp") from exc
    if publication_at.tzinfo is None or publication_at <= datetime.now(timezone.utc):
        raise ReleaseBlocked("publication time must be a future timezone-aware instant")
    before = _write_counts(client)
    preflight = rollover.run_preflight(
        from_quarter, from_week, quarter, week, client, manifest_override=manifest,
    )
    if _write_counts(client) != before or preflight.get("canvas_writes"):
        raise ReleaseBlocked("preflight performed a Canvas write")
    if not preflight.get("ready"):
        return {
            "lifecycle": schedule.BLOCKED,
            "state": PREFLIGHT_BLOCKED,
            "failures": list(preflight.get("blockers") or []),
            "canvas_writes": 0,
            "already_complete": False,
        }
    expiry = clock.astimezone(timezone.utc) + timedelta(days=7)
    authorize_live_transport(
        school_year=SCHOOL_YEAR, quarter=quarter, week=week,
        source_hash=str(intake.get("source_hash")),
        plan_fingerprint=str(intake.get("plan_fingerprint")),
        publication_time=publication_time,
        course_ids=[COURSE_IDS[name] for name in RELEASE_COURSES],
        authorized_by="OWNER_UI", reason="weekly release manager",
        expires_at=expiry.isoformat().replace("+00:00", "Z"),
    )
    require_scoped_live_transport(quarter=quarter, week=week, now=clock.astimezone(timezone.utc))
    report = rollover.execute(
        from_quarter, from_week, quarter, week, client=client,
        owner_confirmation=confirmation, now=clock, manifest=manifest,
    )
    report["state"] = release_state(quarter, week)["state"]
    report["chief_of_staff"] = latest_completed()
    return report


def _parse_week(token: str) -> tuple[int, int]:
    text = token.lower().replace(" ", "").removeprefix("q")
    quarter, week = text.split("w")
    return int(quarter), int(week)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="canvas-weekly-release")
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--review", action="store_true")
    parser.add_argument("--approve", action="store_true")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--week", help="target week, for example q2w5")
    parser.add_argument("--today", help="YYYY-MM-DD calendar pin")
    parser.add_argument("--confirm", help="APPROVE Q2W5 or ROLLOVER Q2W5")
    parser.add_argument("--owner-time", help="future owner publication timestamp")
    parser.add_argument("--production", action="store_true",
                        help="allow the existing rollover engine to use live Canvas")
    parser.add_argument("--live-readonly", action="store_true",
                        help="with --review, classify against Canvas using GET only")
    args = parser.parse_args(argv)
    selected = [args.prepare, args.review, args.approve, args.publish, args.status]
    if sum(bool(item) for item in selected) != 1:
        parser.error("choose one of --prepare, --review, --approve, --publish, or --status")
    if args.publish and not args.production:
        print("BLOCKED: weekly publication requires --production and uses the existing rollover engine")
        return 2
    if args.live_readonly and not args.review:
        parser.error("--live-readonly requires --review")
    today = date.fromisoformat(args.today) if args.today else None
    quarter = week = None
    if args.week:
        quarter, week = _parse_week(args.week)
    try:
        if args.publish:
            from scripts.canvas_llm_deploy.client import LiveDeployClient
            target = discover(today=today, quarter=quarter, week=week)
            report = publish_release(
                target["quarter"], target["week"],
                client=LiveDeployClient(quarter=target["quarter"], week=target["week"]),
                confirmation=args.confirm or "", now=datetime.now(NEW_YORK),
                owner_publication_time=args.owner_time,
            )
            print(json.dumps(_public_report(report), indent=2, ensure_ascii=False))
            return 0 if report.get("lifecycle") == schedule.PUBLISHED_VERIFIED else 1
        target = discover(today=today, quarter=quarter, week=week)
        quarter, week = target["quarter"], target["week"]
        if args.status:
            print(json.dumps({**target, **release_state(quarter, week)}, indent=2, ensure_ascii=False))
            return 0
        if args.prepare or args.review:
            package = build_package(quarter, week, now=datetime.now(NEW_YORK),
                                     owner_publication_time=args.owner_time)
            reconciliation = None
            if args.live_readonly:
                from scripts.canvas_llm_deploy.client import LiveDeployClient
                reconciliation = reconcile(
                    package["manifest"], LiveDeployClient(quarter=quarter, week=week),
                    quarter=quarter, week=week,
                )
            view = review_package(package, reconciliation)
            view.pop("manifest", None)
            print(json.dumps(view, indent=2, ensure_ascii=False))
            return 0 if not view["blockers"] else 2
        result = approve_release(
            quarter, week, confirmation=args.confirm or "",
            owner_publication_time=args.owner_time or "", now=datetime.now(NEW_YORK),
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (ReleaseBlocked, LiveAuthorizationError, rollover.RolloverBlocked) as exc:
        print(f"BLOCKED: {exc}")
        return 2


def _public_report(report: dict[str, Any]) -> dict[str, Any]:
    chief = report.get("chief_of_staff") or {}
    return {
        "lifecycle": report.get("lifecycle"),
        "state": report.get("state"),
        "already_complete": report.get("already_complete"),
        "failures": report.get("failures") or [],
        "source_hash": report.get("source_hash"),
        "plan_fingerprint": report.get("plan_fingerprint"),
        "chief_of_staff_week": chief.get("week_code"),
        "chief_of_staff_status": chief.get("status"),
    }


if __name__ == "__main__":
    raise SystemExit(main())
