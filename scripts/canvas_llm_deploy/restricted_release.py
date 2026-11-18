"""Restricted weekly release through the canonical rollover publisher.

D-028 makes the Canvas rollover engine the only publisher of the weekly
package. A restricted (owner-scoped) release therefore must not introduce a
second publisher. This module builds a *restricted* rollover manifest from the
already-approved deploy plan and hands it to ``rollover.execute`` with
``early_content_only=True``:

* only the scoped academic pages are updated;
* only the scoped assignments are created/skipped;
* weekly announcements, assessment reminders, Homeroom, and front-page switches
  are absent from the manifest (not merely blocked);
* the result is ``EARLY_CONTENT_PUBLISHED_VERIFIED`` — never full-week
  ``PUBLISHED_VERIFIED``.

The deploy preflight and scope record remain the audit trail. The rollover
engine remains the only code path that writes to Canvas.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from . import ledger
from . import plan as plan_mod
from . import scope as scope_mod
from scripts.canvas_llm_intake import manifest as imf
from scripts.canvas_llm_intake import week_resolution as weeks
from scripts.canvas_llm_rollover import rollover


class RestrictedReleaseBlocked(RuntimeError):
    """The restricted release cannot proceed. No Canvas write was authorized."""


def _clock(now: datetime | None) -> datetime:
    clock = now or datetime.now(timezone.utc)
    if clock.tzinfo is None:
        raise RestrictedReleaseBlocked("the release clock must include a timezone")
    return clock.astimezone(timezone.utc)


def _previous_week(quarter: int, week: int) -> tuple[int, int]:
    """Prior instructional week (quarter, week)."""
    ordered = sorted(
        (item for item in weeks.load_weeks() if weeks._week_start(item) is not None),
        key=lambda item: weeks._week_start(item),
    )
    code = weeks.week_code_for(quarter, week)
    index = next((i for i, item in enumerate(ordered) if item.get("code") == code), None)
    if index is None or index == 0:
        raise RestrictedReleaseBlocked(f"no prior instructional week for {code}")
    previous = ordered[index - 1]
    return int(previous["quarter"]), int(previous["week"])


def _safe_slug(text: str) -> str:
    import re
    slug = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return slug[:80] or "assignment"


def build_manifest(
    quarter: int,
    week: int,
    plan: dict[str, Any],
    *,
    scope: dict[str, Any],
) -> dict[str, Any]:
    """Build the restricted rollover manifest. Missing artifacts stay absent."""
    packet = plan_mod.load_packet(quarter, week)
    from_quarter, from_week = _previous_week(quarter, week)
    week_code = weeks.week_code_for(quarter, week)
    courses: list[dict[str, Any]] = []
    for page in plan.get("pages") or []:
        subject = page["subject"]
        body = packet["page_bodies"].get(subject, "")
        if not body:
            raise RestrictedReleaseBlocked(f"{subject}: approved page body is missing")
        body_hash = rollover._canvas_body_hash(body)
        courses.append({
            "subject": subject,
            "label": plan_mod.SUBJECT_LABELS.get(subject, subject),
            "course_id": page["course_id"],
            "to_page_slug": plan.get("slug"),
            "page_body": body,
            "to_page_hash": body_hash,
            "approved_body_hash": body_hash,
            "page_body_action": "UPDATE",
            "approved": True,
            "approval_state": "APPROVED",
            "status": "APPROVED",
        })
    assignments: list[dict[str, Any]] = []
    for item in plan.get("assignments") or []:
        action = item.get("action")
        if action not in ("CREATE", "SKIP"):
            raise RestrictedReleaseBlocked(
                f"{item.get('title')!r}: action {action!r} is not CREATE/SKIP"
            )
        assignments.append({
            "course": item.get("course"),
            "course_id": item.get("course_id"),
            "title": item.get("title"),
            "action": action,
            "assignment_id": item.get("assignment_id"),
            "assignment_group": item.get("assignment_group"),
            "due_date": item.get("due_date"),
            "due_utc": item.get("due_utc"),
            "points_possible": item.get("points_possible"),
            "grading_type": item.get("grading_type"),
            "submission_types": item.get("submission_types"),
            "omit_from_final_grade": item.get("omit_from_final_grade", False),
            "description": item.get("description", ""),
            "approved": True,
            "approval_state": "APPROVED",
            "status": "APPROVED",
        })
    return {
        "school_year": "2026-2027",
        "from_week": weeks.week_code_for(from_quarter, from_week),
        "to_week": week_code,
        "timezone": "America/New_York",
        "scheduled_at": None,
        "publication_time_required": False,
        "source_hash": plan.get("source_hash"),
        "plan_fingerprint": plan.get("plan_fingerprint"),
        "academic_courses": courses,
        "assignments": assignments,
        "weekly_announcements": [],
        "assessment_reminders": [],
        "homeroom": None,
        "homeroom_announcement": None,
        "restricted_release": {
            "scope_only": True,
            "subjects": scope.get("subjects"),
            "artifacts": scope.get("artifacts"),
            "excluded_subjects": scope.get("excluded_subjects"),
            "excluded_artifact_types": scope.get("excluded_artifact_types"),
            "protected_assignments": scope.get("protected_assignments"),
            "scope_source_hash": scope.get("source_hash"),
            "scope_plan_fingerprint": scope.get("plan_fingerprint"),
        },
    }


def _validate_preflight(
    preflight: dict[str, Any] | None,
    *,
    plan: dict[str, Any],
    clock: datetime,
) -> list[str]:
    from datetime import datetime as _dt

    if preflight is None:
        return ["preflight not found (run the scoped preflight first)"]
    blockers: list[str] = []
    if preflight.get("ready") is not True:
        blockers.append("preflight is not ready")
        blockers.extend(preflight.get("blockers") or [])
    if preflight.get("scope_only") is not True:
        blockers.append("preflight is not a restricted-scope preflight")
    expires = preflight.get("expires_at")
    try:
        expires_at = _dt.fromisoformat(str(expires).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return blockers + ["preflight expires_at is missing or malformed"]
    if expires_at.tzinfo is None:
        blockers.append("preflight expires_at must include a timezone")
    elif clock > expires_at:
        blockers.append("preflight expired — rerun the scoped preflight")
    if preflight.get("source_hash") != plan.get("source_hash"):
        blockers.append("preflight source hash does not match the current plan")
    if plan_mod.plan_fingerprint(preflight.get("plan") or {}) != plan_mod.plan_fingerprint(plan):
        blockers.append("preflight plan fingerprint does not match the current plan")
    if preflight.get("approval_snapshot_hash") != plan.get("approval_snapshot_hash"):
        blockers.append("preflight approval snapshot does not match current approvals")
    return blockers


def release(
    quarter: int,
    week: int,
    *,
    preflight_id: str,
    confirmation: str,
    now: datetime | None = None,
    read_client: Any | None = None,
    client: Any | None = None,
    authorize_live: bool = False,
) -> dict[str, Any]:
    """Run the restricted release through ``rollover.execute``.

    ``client`` is injected by tests. Production callers leave it ``None`` so the
    canonical live transport is constructed only after every local gate passes.
    """
    clock = _clock(now)
    week_code = weeks.week_code_for(quarter, week)
    if (confirmation or "").strip().upper() != f"ROLLOVER {week_code}".upper():
        raise RestrictedReleaseBlocked(f"type exactly: ROLLOVER {week_code}")

    plan = plan_mod.build_plan(quarter, week, now=clock)
    scope_record, scope_errors = scope_mod.load_scope(quarter, week)
    if scope_errors:
        raise RestrictedReleaseBlocked("; ".join(scope_errors))
    scope_errors = scope_mod.validate_scope(
        scope_record, plan, quarter=quarter, week=week, now=clock,
    )
    if scope_errors:
        raise RestrictedReleaseBlocked("; ".join(scope_errors))

    preflight = ledger.load_preflight(quarter, week, preflight_id)
    preflight_errors = _validate_preflight(preflight, plan=plan, clock=clock)
    if preflight_errors:
        raise RestrictedReleaseBlocked("; ".join(preflight_errors))

    manifest = build_manifest(quarter, week, plan, scope=scope_record)

    if read_client is None:
        from scripts.canvas_llm_intake.canvas_readonly import CanvasReadOnly
        read_client = CanvasReadOnly.from_env()
    preview = rollover.run_preflight(
        *_previous_week(quarter, week), quarter, week,
        read_client, manifest_override=manifest,
    )
    if preview.get("canvas_writes"):
        raise RestrictedReleaseBlocked("restricted preflight performed a Canvas write")
    if not preview.get("ready"):
        return {
            "lifecycle": "BLOCKED",
            "ready": False,
            "failures": list(preview.get("blockers") or []),
            "canvas_writes": 0,
            "scope_only": True,
        }

    # The intake manifest records the exact plan fingerprint for the live
    # transport authorization. It never claims READY_TO_PUBLISH or
    # PUBLISHED_VERIFIED.
    intake = imf.load_manifest(quarter, week) or {}
    intake["plan_fingerprint"] = plan.get("plan_fingerprint")
    imf.save_manifest(quarter, week, intake)

    # Local, gitignored before-state backups (GET-only). A failed backup blocks
    # the release before any Canvas write.
    from . import ledger as deploy_ledger
    from . import plan as _plan_mod

    for page in plan.get("pages") or []:
        try:
            current = read_client.get_page(page["course_id"], plan.get("slug"))
        except Exception as exc:  # noqa: BLE001
            raise RestrictedReleaseBlocked(
                f"{page.get('subject')}: page backup failed ({type(exc).__name__})"
            ) from exc
        deploy_ledger.write_backup(
            quarter, week, f"{page.get('subject')}-page-before",
            {
                "course_id": page["course_id"],
                "page_id": (current or {}).get("page_id") or (current or {}).get("id"),
                "title": (current or {}).get("title"),
                "body": (current or {}).get("body") or "",
                "body_sha256": _plan_mod._sha((current or {}).get("body") or ""),
                "retrieved_at": clock.isoformat(),
            },
        )
    for assignment in plan.get("assignments") or []:
        if assignment.get("action") != "SKIP" or not assignment.get("assignment_id"):
            continue
        try:
            current = read_client.get_assignment(
                assignment["course_id"], str(assignment["assignment_id"])
            )
        except Exception as exc:  # noqa: BLE001
            raise RestrictedReleaseBlocked(
                f"{assignment.get('title')!r}: pre-state backup failed "
                f"({type(exc).__name__})"
            ) from exc
        deploy_ledger.write_backup(
            quarter, week, "assignment-" + _safe_slug(assignment.get("title", "")) + "-before",
            dict(current or {}, retrieved_at=clock.isoformat()),
        )
    for item in scope_record.get("protected_assignments") or []:
        try:
            current = read_client.get_assignment(
                item["course_id"], str(item["assignment_id"])
            )
        except Exception as exc:  # noqa: BLE001
            raise RestrictedReleaseBlocked(
                f"protected assignment {item.get('assignment_id')}: backup failed "
                f"({type(exc).__name__})"
            ) from exc
        deploy_ledger.write_backup(
            quarter, week, f"protected-assignment-{item['assignment_id']}-before",
            dict(current or {}, retrieved_at=clock.isoformat()),
        )

    if client is None:
        from .live_authorization import (
            authorize_live_transport,
            require_scoped_live_transport,
        )
        from datetime import timedelta

        if authorize_live:
            authorize_live_transport(
                school_year="2026-2027", quarter=quarter, week=week,
                source_hash=str(plan.get("source_hash")),
                plan_fingerprint=str(plan.get("plan_fingerprint")),
                publication_time=(clock + timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
                course_ids=sorted({
                    int(item["course_id"])
                    for item in (plan.get("pages") or []) + (plan.get("assignments") or [])
                    if item.get("course_id") is not None
                }),
                authorized_by="OWNER",
                reason="restricted weekly release authorization",
                expires_at=(clock + timedelta(minutes=15)).isoformat().replace("+00:00", "Z"),
                now=clock,
            )
        require_scoped_live_transport(quarter=quarter, week=week, now=clock)
        from .client import LiveDeployClient
        client = LiveDeployClient(quarter=quarter, week=week)

    report = rollover.execute(
        *_previous_week(quarter, week), quarter, week,
        client=client, owner_confirmation=confirmation,
        manifest=preview["manifest"], early_content_only=True,
    )
    report["scope_only"] = True
    report["scope"] = {
        "subjects": scope_record.get("subjects"),
        "artifacts": scope_record.get("artifacts"),
        "excluded_subjects": scope_record.get("excluded_subjects"),
        "excluded_artifact_types": scope_record.get("excluded_artifact_types"),
        "protected_assignments": scope_record.get("protected_assignments"),
    }
    report["global_ready_to_publish"] = bool(plan.get("ready_to_publish"))

    # Independent readback of preserved objects (no writes).
    from .coordinator import _verify_preserved_assignment
    counts = {"GET": 0}
    preserved: list[dict[str, Any]] = []
    for assignment in plan.get("assignments") or []:
        if assignment.get("action") != "SKIP":
            continue
        ok, detail = _verify_preserved_assignment(read_client, assignment, counts)
        preserved.append({
            "assignment_id": assignment.get("assignment_id"),
            "title": assignment.get("title"),
            "verified": ok,
            "detail": detail,
        })
        if not ok:
            report.setdefault("failures", []).append(
                f"preserved assignment {assignment.get('title')!r} changed ({detail})"
            )
    protected = []
    for item in scope_record.get("protected_assignments") or []:
        live = read_client.get_assignment(item["course_id"], str(item["assignment_id"]))
        live = live or {}
        ok = (
            (live.get("name") or live.get("title")) == item.get("title")
            and str(live.get("id")) == str(item["assignment_id"])
        )
        protected.append({
            "course_id": item["course_id"],
            "assignment_id": str(item["assignment_id"]),
            "title": live.get("name") or live.get("title"),
            "verified": ok,
        })
        if not ok:
            report.setdefault("failures", []).append(
                f"protected assignment {item['assignment_id']} changed"
            )
    report["preserved_assignments"] = preserved
    report["protected_assignments"] = protected
    if report.get("failures"):
        report["lifecycle"] = "FAILED"
    return report


def command_self_test() -> int:
    # Pure manifest-shape checks; no Canvas I/O.
    import tempfile
    from pathlib import Path
    from scripts.canvas_llm_storage import isolated_storage

    with isolated_storage() as root:
        d = imf.staging_dir(2, 6)
        (d / "drafts").mkdir(parents=True)
        m = imf.new_manifest(
            quarter=2, week=6, week_code="Q2W6",
            date_range={"start": "2026-11-16", "end": "2026-11-20"},
        )
        m["source_hash"] = "src-1"
        imf.save_manifest(2, 6, m)
        (d / "drafts" / "math-page.html").write_text(
            "<div id='kl_wrapper_3'>agenda</div>", encoding="utf-8"
        )
        plan = {
            "quarter": 2, "week": 6, "week_code": "Q2W6", "slug": "q2w6-test",
            "source_hash": "src-1", "plan_fingerprint": "fp-1",
            "pages": [{"subject": "math", "course_id": 26404, "action": "UPDATE",
                       "title": "Q2W6", "approved": True}],
            "assignments": [{
                "course": "math", "course_id": 26404, "title": "SM5: Lesson 49 Homework",
                "action": "CREATE", "due_date": "2026-11-16",
                "due_utc": "2026-11-17T04:59:00Z", "assignment_group": "Homework/Class Work",
                "points_possible": 100, "grading_type": "percent",
                "submission_types": "on_paper", "omit_from_final_grade": False,
                "description": "", "approved": True,
            }],
            "weekly_announcements": [], "assessment_reminders": [], "deletes": [],
            "ready_to_publish": False,
        }
        scope = {"subjects": ["math"], "artifacts": ["page", "assignments"],
                 "source_hash": "src-1", "plan_fingerprint": "fp-1",
                 "excluded_subjects": ["reading_spelling", "language_arts", "science"],
                 "excluded_artifact_types": ["weekly_announcement"]}
        manifest = build_manifest(2, 6, plan, scope=scope)
        assert manifest["to_week"] == "Q2W6"
        assert manifest["academic_courses"][0]["subject"] == "math"
        assert manifest["assignments"][0]["action"] == "CREATE"
        assert manifest["weekly_announcements"] == []
        assert manifest["assessment_reminders"] == []
        assert manifest["homeroom"] is None
        assert manifest["plan_fingerprint"] == "fp-1"
    print("PASS canvas-deploy restricted release self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
