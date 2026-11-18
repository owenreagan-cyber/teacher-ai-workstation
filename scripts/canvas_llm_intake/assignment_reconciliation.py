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

Schema 2 binds the report to the exact proposal bundle (order-independent
digest), the intake source hash, and a checked-at timestamp. The deployment
planner refuses to turn any proposal into a CREATE action unless the report is
present, schema-valid, fresh, and covers every proposal exactly once.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from . import manifest as mf
from scripts.canvas_llm_phase3 import assignment_policy as policy

NEW_YORK = "America/New_York"
REPORT_SCHEMA_VERSION = 2
MAX_REPORT_AGE_HOURS = 24
_MAX_CLOCK_SKEW = timedelta(minutes=5)
CLASSIFICATIONS = (
    "MATCH",
    "UPDATE_REQUIRED",
    "CREATE_REQUIRED",
    "DUPLICATE",
    "SEMANTIC_MATCH_REVIEW",
    "UNVERIFIED",
)
# Classifications that may become a CREATE/UPDATE plan action.
CREATE_CLASSIFICATIONS = ("CREATE_REQUIRED",)
SKIP_CLASSIFICATIONS = ("MATCH",)
UPDATE_CLASSIFICATIONS = ("UPDATE_REQUIRED",)


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


def normalized_proposal(proposal: dict[str, Any]) -> dict[str, Any]:
    """Return the identity-bearing fields the report must be bound to."""
    return {
        "course": proposal.get("course"),
        "course_id": proposal.get("course_id"),
        "title": proposal.get("title"),
        "assignment_group": proposal.get("assignment_group"),
        "due_date": proposal.get("due_date"),
        "points_possible": proposal.get("points_possible"),
        "grading_type": proposal.get("grading_type"),
        "submission_types": _submission_types(proposal.get("submission_types")),
        "omit_from_final_grade": bool(proposal.get("omit_from_final_grade", False)),
    }


def proposal_digest(proposals: list[dict[str, Any]]) -> str:
    """Order-independent digest of the exact proposal bundle."""
    rows = sorted(
        (normalized_proposal(p) for p in proposals),
        key=lambda row: (str(row.get("course")), str(row.get("title"))),
    )
    return hashlib.sha256(
        json.dumps(rows, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def validate_report(
    report: Any,
    *,
    quarter: int,
    week: int,
    proposals: list[dict[str, Any]],
    source_hash: str | None = None,
    now: datetime | None = None,
    max_age_hours: int = MAX_REPORT_AGE_HOURS,
) -> list[str]:
    """Return every reason this report cannot authorize assignment writes.

    Empty list means the report is schema-valid, fresh, bound to this source
    hash, and covers the current proposal bundle exactly once. Any error is
    fatal: callers must fail closed and never fall back to CREATE.
    """
    errors: list[str] = []
    if not isinstance(report, dict) or not report:
        return ["assignment reconciliation report is missing or unreadable"]

    if report.get("schemaVersion") != REPORT_SCHEMA_VERSION:
        errors.append(
            f"reconciliation schemaVersion is {report.get('schemaVersion')!r}, "
            f"expected {REPORT_SCHEMA_VERSION}"
        )
    expected_week_code = f"Q{quarter}W{week}"
    if report.get("week_code") != expected_week_code:
        errors.append(
            f"reconciliation week_code is {report.get('week_code')!r}, "
            f"expected {expected_week_code}"
        )
    if report.get("quarter") not in (None, quarter) or report.get("week") not in (None, week):
        errors.append("reconciliation quarter/week does not match this deployment")

    if source_hash is not None:
        recorded_source = report.get("source_hash")
        if not recorded_source:
            errors.append("reconciliation source_hash is missing")
        elif recorded_source != source_hash:
            errors.append("reconciliation source_hash does not match the current intake source")

    checked_at = _parse_timestamp(report.get("checked_at"))
    if checked_at is None:
        errors.append("reconciliation checked_at is missing or not a timezone-aware timestamp")
    else:
        clock = now or datetime.now(timezone.utc)
        if clock.tzinfo is None:
            errors.append("reconciliation validation clock must include a timezone")
        else:
            clock = clock.astimezone(timezone.utc)
            if checked_at > clock + _MAX_CLOCK_SKEW:
                errors.append("reconciliation checked_at is in the future")
            elif clock - checked_at > timedelta(hours=max_age_hours):
                errors.append(
                    f"reconciliation is stale (older than {max_age_hours} hours); "
                    "regenerate it from live Canvas before deploying"
                )

    results = report.get("results")
    if not isinstance(results, list):
        errors.append("reconciliation results are missing")
        results = []
    if report.get("proposal_count") != len(proposals):
        errors.append(
            f"reconciliation proposal_count is {report.get('proposal_count')!r}, "
            f"expected {len(proposals)}"
        )
    if len(results) != len(proposals):
        errors.append(
            f"reconciliation covers {len(results)} proposals, expected {len(proposals)}"
        )
    expected_digest = proposal_digest(proposals)
    if report.get("proposal_digest") != expected_digest:
        errors.append("reconciliation proposal_digest does not match the current proposals")

    expected_keys = {
        (str(p.get("course")), str(p.get("title"))) for p in proposals
    }
    seen: dict[tuple[str, str], int] = {}
    classified: dict[str, int] = {name: 0 for name in CLASSIFICATIONS}
    for item in results:
        if not isinstance(item, dict):
            errors.append("reconciliation contains a non-object result")
            continue
        key = (str(item.get("course")), str(item.get("title")))
        seen[key] = seen.get(key, 0) + 1
        classification = item.get("classification")
        if classification not in CLASSIFICATIONS:
            errors.append(f"{item.get('title')!r}: unknown classification {classification!r}")
            continue
        classified[classification] += 1
        live = item.get("live")
        if classification in ("MATCH", "UPDATE_REQUIRED"):
            if not isinstance(live, dict) or live.get("assignment_id") in (None, ""):
                errors.append(
                    f"{item.get('title')!r}: {classification} without a live assignment id"
                )
        elif classification == "CREATE_REQUIRED" and live not in (None, {}):
            errors.append(f"{item.get('title')!r}: CREATE_REQUIRED must not carry a live object")
        elif classification in ("DUPLICATE", "SEMANTIC_MATCH_REVIEW"):
            if not live:
                errors.append(f"{item.get('title')!r}: {classification} without live evidence")
    for key in expected_keys:
        count = seen.get(key, 0)
        if count != 1:
            errors.append(
                f"{key[1]!r}: reconciliation entries={count}, expected exactly 1"
            )
    for key in seen:
        if key not in expected_keys:
            errors.append(f"{key[1]!r}: reconciliation entry has no matching proposal")

    counts = report.get("counts")
    if not isinstance(counts, dict):
        errors.append("reconciliation counts are missing")
    else:
        for name, observed in classified.items():
            if counts.get(name) != observed:
                errors.append(
                    f"reconciliation count {name}={counts.get(name)!r} "
                    f"does not match results ({observed})"
                )
    if report.get("canvas_writes") != 0:
        errors.append("reconciliation report claims Canvas writes; it must be GET-only")
    return errors


def _report_key(report: dict[str, Any], course: Any, title: str) -> dict[str, Any] | None:
    for item in report.get("results") or []:
        if str(item.get("course")) == str(course) and str(item.get("title")) == str(title):
            return item
    return None


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
    source_hash: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Reconcile staged assignments against live Canvas (GET-only)."""
    week_code = f"Q{quarter}W{week}"
    if proposals is None:
        path = mf.staging_dir(quarter, week) / "drafts" / "assignments.json"
        try:
            proposals = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            proposals = []
    if source_hash is None:
        manifest = mf.load_manifest(quarter, week) or {}
        source_hash = manifest.get("source_hash")

    courses: dict[int, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []
    counts = {
        "MATCH": 0,
        "UPDATE_REQUIRED": 0,
        "CREATE_REQUIRED": 0,
        "DUPLICATE": 0,
        "SEMANTIC_MATCH_REVIEW": 0,
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

        # Semantic identity: same course, kind family, and lesson/test number.
        # A weekday-title difference (for example a manually created Thursday
        # Lesson 60 against a proposed Tuesday Lesson 60) is a duplicate
        # candidate, never a silent POST and never an automatic rename.
        semantic_candidates = [
            assignment for assignment in cache["assignments"]
            if (assignment.get("name") or assignment.get("title")) != title
            and policy.semantic_identity(assignment.get("name") or assignment.get("title"))
            == policy.semantic_identity(title)
            and policy.semantic_identity(title) is not None
        ]
        if semantic_candidates:
            candidates = [
                _live_summary(a, cache["groups"].get(a.get("assignment_group_id")))
                for a in semantic_candidates
            ]
            classification = ("SEMANTIC_MATCH_REVIEW" if len(matches) <= 1
                              else "DUPLICATE")
            results.append({
                "course": proposal.get("course"),
                "course_id": cid,
                "title": title,
                "classification": classification,
                "reason": (
                    "semantic identity (course + kind family + lesson/test number) "
                    "matches an existing assignment with a different title"
                ),
                "owner_action": (
                    "Choose exactly one: keep the existing assignment (preserve its "
                    "id, title, due date, group, and user work), stage a rename for "
                    "explicit approval, or explicitly create a genuinely distinct "
                    "second object. No Canvas write is performed by this report."
                ),
                "live": candidates,
                "proposed": {
                    "assignment_group": proposal.get("assignment_group"),
                    "due_date": proposal.get("due_date"),
                    "points_possible": proposal.get("points_possible"),
                    "grading_type": proposal.get("grading_type"),
                    "submission_types": proposal.get("submission_types"),
                    "omit_from_final_grade": proposal.get("omit_from_final_grade"),
                },
            })
            counts[classification] += 1
            blockers.append(f"{title}: semantic duplicate candidate requires owner review")
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
        "schemaVersion": REPORT_SCHEMA_VERSION,
        "quarter": quarter,
        "week": week,
        "week_code": week_code,
        "source_hash": source_hash,
        "checked_at": (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(),
        "proposal_count": len(proposals),
        "proposal_digest": proposal_digest(proposals),
        "proposals": sorted(
            (normalized_proposal(p) for p in proposals),
            key=lambda row: (str(row.get("course")), str(row.get("title"))),
        ),
        "results": results,
        "counts": counts,
        "blockers": blockers,
        "pending_actions": pending_actions,
        "bundle_status": "BLOCKED" if blockers else "READY_FOR_APPROVAL",
        "execution_ready": False if blockers or pending_actions else True,
        "canvas_writes": 0,
    }


def load_report(quarter: int, week: int) -> tuple[dict[str, Any], list[str]]:
    """Read the staged report. Returns ``({}, errors)`` when it is unusable."""
    path = mf.staging_dir(quarter, week) / "planner" / "assignment-reconciliation.json"
    if not path.exists():
        return {}, [f"assignment reconciliation report is missing ({path.name})"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"assignment reconciliation report is unreadable ({type(exc).__name__})"]
    if not isinstance(data, dict):
        return {}, ["assignment reconciliation report is not a JSON object"]
    return data, []


def run_live_reconciliation(
    quarter: int,
    week: int,
    *,
    client: Any | None = None,
    write: bool = True,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build (and optionally persist) the authoritative report from GET-only live data.

    A ``client`` must expose ``get_course``, ``list_assignment_groups`` and
    ``list_assignments``. The intake ``CanvasReadOnly`` client satisfies this
    contract and statically forbids write verbs. No write path exists here.
    """
    if client is None:
        from .canvas_readonly import CanvasReadOnly
        client = CanvasReadOnly.from_env()
    proposals_path = mf.staging_dir(quarter, week) / "drafts" / "assignments.json"
    try:
        proposals = json.loads(proposals_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"cannot read staged assignment proposals ({type(exc).__name__})"
        ) from exc
    if not isinstance(proposals, list) or not proposals:
        raise ValueError("staged assignment proposals are missing or empty")
    report = reconcile(
        quarter, week, client=client, proposals=proposals, now=now,
    )
    errors = validate_report(
        report, quarter=quarter, week=week, proposals=proposals,
        source_hash=report.get("source_hash"), now=now,
    )
    if errors:
        raise ValueError("generated reconciliation failed validation: " + "; ".join(errors))
    if write:
        report["report_path"] = str(write_report(report, quarter=quarter, week=week))
    return report


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

    # Semantic duplicate identity: weekday variants and legacy forms.
    from scripts.canvas_llm_phase3 import assignment_policy as policy
    assert policy.semantic_identity("RM4: Tuesday Comprehension Questions — Lesson 60") == \
        policy.semantic_identity("RM4: Thursday Comprehension Questions — Lesson 60")
    assert policy.semantic_identity("RM4: Lesson 60 Workbook and Comprehension") == \
        policy.semantic_identity("RM4: Monday Workbook Classwork — Lesson 60")
    assert policy.semantic_identity("RM4: Mastery Test 6") == \
        policy.semantic_identity("RM4: Reading Mastery Test 6")
    assert policy.semantic_identity("MATH THNK") is None

    # ---- Schema 2 fail-closed contract (pure, no Canvas I/O) -------------
    import copy
    from datetime import datetime as _dt, timedelta as _td, timezone as _tz

    fixed_now = _dt(2026, 11, 18, 12, 0, tzinfo=_tz.utc)
    proposals = [dict(proposal, title="Classroom Practice 27")]
    report = {
        "schemaVersion": REPORT_SCHEMA_VERSION,
        "quarter": 2,
        "week": 6,
        "week_code": "Q2W6",
        "source_hash": "src-1",
        "checked_at": fixed_now.isoformat(),
        "proposal_count": 1,
        "proposal_digest": proposal_digest(proposals),
        "results": [{
            "course": "language_arts", "course_id": 28171,
            "title": "Classroom Practice 27", "classification": "MATCH",
            "live": {"assignment_id": "abc"},
        }],
        "counts": {name: (1 if name == "MATCH" else 0) for name in CLASSIFICATIONS},
        "blockers": [], "canvas_writes": 0,
    }
    kwargs = dict(quarter=2, week=6, proposals=proposals, source_hash="src-1", now=fixed_now)
    assert validate_report(report, **kwargs) == [], validate_report(report, **kwargs)

    assert validate_report({}, **kwargs)  # missing
    assert validate_report("nope", **kwargs)  # malformed
    bad = copy.deepcopy(report); bad["schemaVersion"] = 1
    assert any("schemaVersion" in e for e in validate_report(bad, **kwargs))
    stale = copy.deepcopy(report)
    stale["checked_at"] = (fixed_now - _td(hours=MAX_REPORT_AGE_HOURS + 1)).isoformat()
    assert any("stale" in e for e in validate_report(stale, **kwargs))
    wrong_source = copy.deepcopy(report); wrong_source["source_hash"] = "src-2"
    assert any("source_hash" in e for e in validate_report(wrong_source, **kwargs))
    wrong_digest = copy.deepcopy(report); wrong_digest["proposal_digest"] = "0" * 64
    assert any("proposal_digest" in e for e in validate_report(wrong_digest, **kwargs))
    missing_live = copy.deepcopy(report)
    missing_live["results"][0]["live"] = None
    assert any("live assignment id" in e for e in validate_report(missing_live, **kwargs))
    duplicate_entry = copy.deepcopy(report)
    duplicate_entry["results"].append(copy.deepcopy(duplicate_entry["results"][0]))
    duplicate_entry["counts"]["MATCH"] = 2
    assert any("exactly 1" in e for e in validate_report(duplicate_entry, **kwargs))

    print("PASS assignment reconciliation self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
