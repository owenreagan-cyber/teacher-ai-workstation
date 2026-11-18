"""Explicit restricted-deployment scope for a weekly Canvas release.

A normal weekly release keeps the full-week ``READY_TO_PUBLISH`` gate. A
restricted release is a *separate*, explicitly authorized gate: the owner names
the exact subjects and artifact types being deployed, and the plan must prove
that every other subject and artifact category produces zero actions.

The scope record is a local, audit-trailed JSON file under the week's staging
``planner/`` directory. It is bound to:

* the quarter/week and ``week_code``;
* the intake ``source_hash``;
* the exact deployment ``plan_fingerprint``;
* an expiry timestamp.

It never changes the intake manifest's global readiness. A scoped release and a
full-week release are therefore always distinguishable in the ledger.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from scripts.canvas_llm_intake import constants as intake_constants
from scripts.canvas_llm_intake import manifest as imf

SCOPE_SCHEMA_VERSION = 1
FILE_NAME = "deployment-scope.json"
STATE_ACTIVE = "ACTIVE"
AUTHORIZED_BY = "OWNER"
SUPPORTED_ARTIFACTS = ("page", "assignments")
DEFAULT_TTL_HOURS = 168
_MAX_CLOCK_SKEW = timedelta(minutes=5)


class ScopeError(RuntimeError):
    """The restricted deployment scope is missing or invalid."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def scope_path(quarter: int, week: int) -> Path:
    return imf.staging_dir(quarter, week) / "planner" / FILE_NAME


def load_scope(quarter: int, week: int) -> tuple[dict[str, Any], list[str]]:
    path = scope_path(quarter, week)
    if not path.exists():
        return {}, ["restricted deployment scope is missing"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"restricted deployment scope is unreadable ({type(exc).__name__})"]
    if not isinstance(data, dict):
        return {}, ["restricted deployment scope is not a JSON object"]
    return data, []


def _plan_items(plan: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for page in plan.get("pages") or []:
        items.append({
            "kind": "page", "subject": page.get("subject"),
            "title": page.get("title"), "action": page.get("action"),
            "approved": page.get("approved"),
        })
    for assignment in plan.get("assignments") or []:
        items.append({
            "kind": "assignments", "subject": assignment.get("course"),
            "title": assignment.get("title"), "action": assignment.get("action"),
            "approved": assignment.get("approved"),
        })
    return items


def exclusion_evidence(plan: dict[str, Any], scope: dict[str, Any]) -> dict[str, Any]:
    """Count every plan action per active subject, proving out-of-scope is zero."""
    active = list(intake_constants.active_subject_keys_for_quarter(int(plan.get("quarter") or 2)))
    included = set(scope.get("subjects") or [])
    evidence: dict[str, Any] = {}
    for subject in active:
        pages = [p for p in plan.get("pages") or [] if p.get("subject") == subject]
        assignments = [a for a in plan.get("assignments") or [] if a.get("course") == subject]
        announcements = [
            a for a in plan.get("weekly_announcements") or [] if a.get("subject") == subject
        ]
        reminders = [
            r for r in plan.get("assessment_reminders") or [] if r.get("subject") == subject
        ]
        evidence[subject] = {
            "in_scope": subject in included,
            "pages": len(pages),
            "assignments": len(assignments),
            "weekly_announcements": len(announcements),
            "assessment_reminders": len(reminders),
            "touched": bool(pages or assignments or announcements or reminders),
        }
    return evidence


def validate_scope(
    scope: Any,
    plan: dict[str, Any],
    *,
    quarter: int,
    week: int,
    now: datetime | None = None,
) -> list[str]:
    """Return every reason this scope cannot authorize the given plan."""
    errors: list[str] = []
    if not isinstance(scope, dict) or not scope:
        return ["restricted deployment scope is missing"]
    if scope.get("schemaVersion") != SCOPE_SCHEMA_VERSION:
        errors.append("scope schemaVersion does not match")
    week_code = f"Q{quarter}W{week}"
    if scope.get("week_code") != week_code:
        errors.append(f"scope week_code is {scope.get('week_code')!r}, expected {week_code}")
    if scope.get("quarter") not in (None, quarter) or scope.get("week") not in (None, week):
        errors.append("scope quarter/week does not match this deployment")
    if scope.get("state") != STATE_ACTIVE:
        errors.append("scope is not ACTIVE")
    if scope.get("authorized_by") != AUTHORIZED_BY:
        errors.append("scope is not owner-authorized")
    if scope.get("confirmation") != f"SCOPE {week_code}":
        errors.append("scope confirmation phrase is missing or does not match")

    clock = now or _now()
    if clock.tzinfo is None:
        return errors + ["scope validation clock must include a timezone"]
    clock = clock.astimezone(timezone.utc)
    authorized_at = _parse(scope.get("authorized_at"))
    expires_at = _parse(scope.get("expires_at"))
    if authorized_at is None:
        errors.append("scope authorized_at is missing or invalid")
    elif authorized_at > clock + _MAX_CLOCK_SKEW:
        errors.append("scope authorized_at is in the future")
    if expires_at is None:
        errors.append("scope expires_at is missing or invalid")
    elif expires_at <= clock:
        errors.append("scope authorization has expired")

    if not plan.get("source_hash"):
        errors.append("plan source_hash is missing")
    elif scope.get("source_hash") != plan.get("source_hash"):
        errors.append("scope source_hash does not match the current plan")
    if not plan.get("plan_fingerprint"):
        errors.append("plan fingerprint is missing")
    elif scope.get("plan_fingerprint") != plan.get("plan_fingerprint"):
        errors.append("scope plan_fingerprint does not match the current plan")

    active = set(intake_constants.active_subject_keys_for_quarter(quarter))
    subjects = scope.get("subjects")
    if not isinstance(subjects, list) or not subjects:
        errors.append("scope subjects are missing")
        subjects = []
    subjects = [str(s) for s in subjects]
    if len(set(subjects)) != len(subjects):
        errors.append("scope subjects contain duplicates")
    unknown = sorted(set(subjects) - active)
    if unknown:
        errors.append("scope names unknown/inactive subjects: " + ", ".join(unknown))

    artifacts = scope.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("scope artifacts are missing")
        artifacts = []
    artifacts = [str(a) for a in artifacts]
    unsupported = sorted(set(artifacts) - set(SUPPORTED_ARTIFACTS))
    if unsupported:
        errors.append(
            "scope requests unsupported artifact types: " + ", ".join(unsupported)
        )

    excluded = scope.get("excluded_subjects")
    if not isinstance(excluded, list):
        errors.append("scope excluded_subjects are missing")
        excluded = []
    excluded = {str(s) for s in excluded}
    missing_excluded = sorted(active - set(subjects) - excluded)
    if missing_excluded:
        errors.append(
            "scope does not explicitly exclude: " + ", ".join(missing_excluded)
        )

    # ---- Plan inventory must be exactly inside the scope ------------------
    pages = plan.get("pages") or []
    assignments = plan.get("assignments") or []
    page_subjects = {str(p.get("subject")) for p in pages}
    assignment_subjects = {str(a.get("course")) for a in assignments}
    scope_subjects = set(subjects)

    if "page" in artifacts:
        if not pages:
            errors.append("scope requests pages but the plan has no page actions")
        extra_pages = sorted(page_subjects - scope_subjects)
        if extra_pages:
            errors.append("plan writes pages outside scope: " + ", ".join(extra_pages))
        missing_pages = sorted(scope_subjects - page_subjects)
        if missing_pages:
            errors.append("scope subjects have no page action: " + ", ".join(missing_pages))
        for page in pages:
            if page.get("action") != "UPDATE":
                errors.append(f"page {page.get('subject')} action is not UPDATE")
            if page.get("approved") is not True:
                errors.append(f"page {page.get('subject')} is not approved against this plan")
    elif pages:
        errors.append("scope excludes pages but the plan contains page actions")

    if "assignments" in artifacts:
        if not assignments:
            errors.append("scope requests assignments but the plan has no assignment actions")
        extra_assignments = sorted(assignment_subjects - scope_subjects)
        if extra_assignments:
            errors.append(
                "plan writes assignments outside scope: " + ", ".join(extra_assignments)
            )
        for assignment in assignments:
            action = assignment.get("action")
            if action not in ("CREATE", "SKIP"):
                errors.append(
                    f"assignment {assignment.get('title')!r} action {action!r} is not "
                    "CREATE/SKIP inside a restricted release"
                )
            if assignment.get("approved") is not True:
                errors.append(
                    f"assignment {assignment.get('title')!r} is not approved against this plan"
                )
    elif assignments:
        errors.append("scope excludes assignments but the plan contains assignment actions")

    if plan.get("weekly_announcements"):
        errors.append("restricted scope cannot include weekly announcements")
    if plan.get("assessment_reminders"):
        errors.append("restricted scope cannot include assessment reminders")
    if plan.get("deletes"):
        errors.append("restricted scope cannot include deletes")
    if plan.get("reconciliation_blockers"):
        errors.append("assignment reconciliation still reports blockers")

    protected = scope.get("protected_assignments") or []
    if not isinstance(protected, list):
        errors.append("scope protected_assignments must be a list")
    else:
        for item in protected:
            if not isinstance(item, dict):
                errors.append("scope protected_assignments contains a non-object")
                continue
            if item.get("course_id") is None or item.get("assignment_id") in (None, ""):
                errors.append("protected assignment is missing course_id/assignment_id")

    return errors


def authorize_scope(
    quarter: int,
    week: int,
    *,
    plan: dict[str, Any],
    subjects: list[str],
    artifacts: list[str],
    protected_assignments: list[dict[str, Any]] | None = None,
    confirmation: str,
    reason: str,
    now: datetime | None = None,
    ttl_hours: int = DEFAULT_TTL_HOURS,
) -> dict[str, Any]:
    """Record an owner-authorized restricted scope bound to the exact plan."""
    week_code = f"Q{quarter}W{week}"
    if (confirmation or "").strip() != f"SCOPE {week_code}":
        raise ScopeError(f"type exactly: SCOPE {week_code}")
    clock = (now or _now()).astimezone(timezone.utc)
    active = intake_constants.active_subject_keys_for_quarter(quarter)
    record = {
        "schemaVersion": SCOPE_SCHEMA_VERSION,
        "state": STATE_ACTIVE,
        "quarter": quarter,
        "week": week,
        "week_code": week_code,
        "source_hash": plan.get("source_hash"),
        "plan_fingerprint": plan.get("plan_fingerprint"),
        "subjects": [str(s) for s in subjects],
        "artifacts": [str(a) for a in artifacts],
        "excluded_subjects": sorted(set(active) - {str(s) for s in subjects}),
        "excluded_artifact_types": [
            "weekly_announcement", "assessment_reminder", "delete", "front_page",
        ],
        "protected_assignments": list(protected_assignments or []),
        "authorized_by": AUTHORIZED_BY,
        "authorized_at": clock.isoformat(),
        "expires_at": (clock + timedelta(hours=ttl_hours)).isoformat(),
        "confirmation": f"SCOPE {week_code}",
        "reason": reason,
        "global_ready_to_publish": bool(plan.get("ready_to_publish")),
    }
    errors = validate_scope(record, plan, quarter=quarter, week=week, now=clock)
    if errors:
        raise ScopeError("; ".join(errors))
    path = scope_path(quarter, week)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    record["path"] = str(path)
    return record


def command_self_test() -> int:
    import copy
    import tempfile

    orig = imf.staging_dir
    with tempfile.TemporaryDirectory() as tmp:
        imf.staging_dir = lambda q, w: Path(tmp) / f"q{q}w{w}"
        try:
            plan = {
                "quarter": 2, "week": 6, "week_code": "Q2W6",
                "source_hash": "src-1", "plan_fingerprint": "fp-1",
                "ready_to_publish": False,
                "pages": [
                    {"subject": "math", "action": "UPDATE", "approved": True, "title": "Q2W6"},
                    {"subject": "reading_spelling", "action": "UPDATE", "approved": True, "title": "Q2W6"},
                ],
                "assignments": [
                    {"course": "math", "title": "A", "action": "CREATE", "approved": True},
                    {"course": "reading_spelling", "title": "B", "action": "SKIP", "approved": True},
                ],
                "weekly_announcements": [], "assessment_reminders": [], "deletes": [],
                "reconciliation_blockers": [],
            }
            record = authorize_scope(
                2, 6, plan=plan, subjects=["math", "reading_spelling"],
                artifacts=["page", "assignments"],
                protected_assignments=[{"course_id": 26442, "assignment_id": "1063967",
                                        "title": "RM4: Thursday Comprehension Questions — Lesson 60"}],
                confirmation="SCOPE Q2W6", reason="test",
                now=datetime(2026, 11, 18, 12, tzinfo=timezone.utc),
            )
            assert record["excluded_subjects"] == ["language_arts", "science"]
            loaded, errors = load_scope(2, 6)
            assert not errors, errors
            assert validate_scope(loaded, plan, quarter=2, week=6,
                                  now=datetime(2026, 11, 18, 13, tzinfo=timezone.utc)) == []

            # Out-of-scope subject -> fail closed.
            bad_plan = copy.deepcopy(plan)
            bad_plan["pages"].append(
                {"subject": "language_arts", "action": "UPDATE", "approved": True, "title": "x"}
            )
            assert validate_scope(loaded, bad_plan, quarter=2, week=6)

            # An announcement in a restricted scope -> fail closed.
            bad_plan = copy.deepcopy(plan)
            bad_plan["weekly_announcements"] = [{"title": "Update"}]
            assert validate_scope(loaded, bad_plan, quarter=2, week=6)

            # Existing-assignment UPDATE -> fail closed.
            bad_plan = copy.deepcopy(plan)
            bad_plan["assignments"][0]["action"] = "UPDATE"
            assert validate_scope(loaded, bad_plan, quarter=2, week=6)

            # Stale fingerprint and expiry -> fail closed.
            bad_plan = copy.deepcopy(plan); bad_plan["plan_fingerprint"] = "fp-2"
            assert any("fingerprint" in e for e in validate_scope(loaded, bad_plan, quarter=2, week=6))
            assert any("expired" in e for e in validate_scope(
                loaded, plan, quarter=2, week=6,
                now=datetime(2027, 1, 1, tzinfo=timezone.utc),
            ))

            # Wrong confirmation phrase -> refused.
            try:
                authorize_scope(2, 6, plan=plan, subjects=["math", "reading_spelling"],
                                artifacts=["page", "assignments"], confirmation="SCOPE Q2W5",
                                reason="test")
                raise AssertionError("expected ScopeError")
            except ScopeError:
                pass
        finally:
            imf.staging_dir = orig
    print("PASS canvas-deploy scope self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
