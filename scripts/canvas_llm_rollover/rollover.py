"""Friday rollover: GET-only preflight (readiness gate) + guarded execution.

Order of operations (§15):

    A. PRE-ROLLOVER VALIDATION  (readiness gate; no writes)
    B. ACADEMIC PAGE ROLLOVER   (set upcoming-week page as front page)
    C. HOMEROOM ROLLOVER        (copy newsletter forward + set front page)
    D. WEEKLY COMMUNICATION     (create/schedule weekly update announcements)
    E. FINAL VERIFICATION       (readback + ledger + lifecycle)

No production writes happen unless a live client is explicitly supplied and the
owner confirmation passes. The engine is idempotent and stops on first failure
(partial-failure ledger with a safe recovery path).
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import date, datetime, timezone
from typing import Any

from scripts.canvas_llm_intake import manifest as imf
from scripts.canvas_llm_deploy import preflight as deploy_preflight
from scripts.canvas_llm_deploy import ledger as deploy_ledger
from scripts.canvas_llm_deploy import plan as deploy_plan
from scripts.canvas_llm_deploy.client import DeployClient, DeployClientError

from . import ledger
from . import manifest as rollover_manifest
from . import schedule

# Rollover lifecycle (mirrors schedule.ROLLOVER_STATES).
LIFECYCLE = schedule.ROLLOVER_STATES


class RolloverBlocked(RuntimeError):
    """Raised when the rollover may not proceed (gate/validation failure)."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _confirm_ok(confirmation: str, to_week_code: str) -> bool:
    text = (confirmation or "").strip().upper()
    return bool(text) and text == f"ROLLOVER {to_week_code.upper()}"


_CANVAS_GLOBAL_CSS_RE = re.compile(
    r'<link\b[^>]*\bhref=["\'][^"\']*canvas_global_app\.css[^"\']*["\'][^>]*>\s*',
    re.IGNORECASE,
)
_CANVAS_GLOBAL_JS_RE = re.compile(
    r'\s*<script\b[^>]*\bsrc=["\'][^"\']*canvas_global_app\.js[^"\']*["\'][^>]*>\s*</script>',
    re.IGNORECASE,
)
_CANVAS_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def _submission_type(value: Any) -> str:
    """Return a single Canvas submission type from either a list or a string.

    The intake can carry ``submission_types`` as a list (``["on_paper"]``) or,
    historically, a bare string (``"on_paper"``). Indexing ``[0]`` on the bare
    string would yield ``"o"`` and be rejected by Canvas; normalize here so the
    canonical "on_paper" value is always sent.
    """
    sts = value or ["on_paper"]
    if isinstance(sts, str):
        return sts
    return sts[0] if sts else "on_paper"


def _assignment_title(item: dict[str, Any]) -> str:
    return str(item.get("name") or item.get("title") or "")


def _due_minute(value: Any) -> datetime | None:
    """Parse a Canvas/ISO due timestamp to an exact UTC minute (or None)."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(second=0, microsecond=0)


def _assignment_matches(items: list[dict[str, Any]], title: str) -> list[dict[str, Any]]:
    return [item for item in items if _assignment_title(item) == title]


def _assignment_readback_ok(
    readback: dict[str, Any], assignment: dict[str, Any], *,
    expected_group_id: Any = None,
) -> bool:
    """Verify every required assignment field after a create or update."""
    expected_due = _due_minute(assignment.get("due_utc"))
    submission = _submission_type(assignment.get("submission_types"))
    live_types = readback.get("submission_types") or []
    if isinstance(live_types, str):
        live_types = [live_types]
    ok = (
        _assignment_title(readback) == str(assignment.get("title") or "")
        and _due_minute(readback.get("due_at")) == expected_due
        and float(readback.get("points_possible") or 0) == float(assignment.get("points_possible") or 0)
        and str(readback.get("grading_type") or "") == str(assignment.get("grading_type") or "percent")
        and submission in live_types
        and bool(readback.get("omit_from_final_grade")) == bool(assignment.get("omit_from_final_grade", False))
        and readback.get("published") is not False
    )
    if expected_group_id is not None:
        ok = ok and str(readback.get("assignment_group_id")) == str(expected_group_id)
    return ok


def _canvas_owned_body(body: str) -> str:
    """Remove only Canvas-injected global app assets from page GET readback.

    Canvas may prepend its account-level canvas_global_app.css <link> and append
    canvas_global_app.js <script> to wiki-page bodies. Those tags are not part
    of the teacher-approved artifact and must not invalidate exact content
    verification. No other HTML is normalized or stripped.
    """
    text = body or ""
    text = _CANVAS_GLOBAL_CSS_RE.sub("", text)
    text = _CANVAS_GLOBAL_JS_RE.sub("", text)
    return text


def _canvas_body_hash(body: str) -> str:
    # Canvas strips HTML comments and trailing newlines on write. Neither is
    # visible content, so bind verification to the Canvas-comparable body.
    text = _CANVAS_HTML_COMMENT_RE.sub("", _canvas_owned_body(body)).rstrip("\n")
    return deploy_plan._sha(text)


def _manifest_body_hash(block: dict[str, Any]) -> str:
    """Canvas-comparable hash for an approved body block.

    Canvas strips HTML comments and injects account-level global assets on
    write. The visible authored content is unchanged, so verification compares
    the Canvas-normalized body rather than the raw authoring hash.
    """
    body = block.get("body") or ""
    if body:
        return _canvas_body_hash(body)
    return str(block.get("proposed_content_hash") or "")


# --------------------------------------------------------------------------- #
# A. Readiness gate (pure; no Canvas I/O)
# --------------------------------------------------------------------------- #

def build_readiness(
    from_quarter: int,
    from_week: int,
    to_quarter: int,
    to_week: int,
    *,
    today: date | None = None,
) -> dict[str, Any]:
    """Evaluate the Friday-rollover readiness gate (no Canvas I/O).

    Returns ``{manifest, ready, blockers, needs_owen}``.
    """
    plan = rollover_manifest.build_rollover_manifest(
        from_quarter, from_week, to_quarter, to_week, today=today
    )
    blockers: list[str] = []
    needs_owen = False

    m = imf.load_manifest(to_quarter, to_week)
    if m is None:
        blockers.append("The upcoming week plan is not available yet.")
    else:
        if not m.get("ready_to_publish"):
            blockers.append("The upcoming week's approved course packages are not ready yet.")
        if m.get("status") == "NEEDS_INPUT":
            needs_owen = True
        # Open (unanswered) questions require Owen — not the full question list.
        from scripts.canvas_llm_intake import questions as qs
        open_qs = qs.unresolved_questions(qs.load_questions(to_quarter, to_week))
        if open_qs:
            needs_owen = True

    # Agenda-hash invariant (§10): weekly_update_agenda_hash == page_agenda_hash.
    for a in plan.get("weekly_announcements", []):
        if not a.get("hash_consistent"):
            blockers.append(f"{a['subject']}: weekly agenda hash mismatch")

    for course in plan.get("academic_courses", []):
        if not course.get("approved"):
            blockers.append(f"{course['label']} page needs your approval")

    # Homeroom content freshness.
    h = plan.get("homeroom", {})
    if not h.get("source_content_hash"):
        blockers.append("Homeroom newsletter source is not available yet.")
    if not h.get("approved"):
        blockers.append("Homeroom newsletter needs your approval")

    return {
        "manifest": plan,
        "ready": len(blockers) == 0,
        "blockers": blockers,
        "needs_owen": needs_owen,
    }


# --------------------------------------------------------------------------- #
# Preflight (GET-only when a client is supplied)
# --------------------------------------------------------------------------- #

def run_preflight(
    from_quarter: int,
    from_week: int,
    to_quarter: int,
    to_week: int,
    client: DeployClient | None = None,
    *,
    today: date | None = None,
    manifest_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """GET-only rollover preflight: readiness gate + live object resolution."""
    readiness = (
        {"manifest": manifest_override, "ready": True, "blockers": [], "needs_owen": False}
        if manifest_override is not None
        else build_readiness(from_quarter, from_week, to_quarter, to_week, today=today)
    )
    plan = readiness["manifest"]
    blockers = list(readiness["blockers"])
    warnings: list[str] = []
    live: dict[str, Any] = {
        "academic": {}, "homeroom": {}, "assignments": {},
        "weekly_announcements": {}, "assessment_reminders": {},
    }

    if client is None:
        warnings.append("LIVE CANVAS CONTEXT UNAVAILABLE — dry-run (no Canvas GET performed)")
        return {
            **readiness,
            "live": live,
            "warnings": warnings,
            "blockers": blockers,
            "ready": len(blockers) == 0,
            "canvas_writes": 0,
            "scheduled_at": plan["scheduled_at"],
        }

    # Academic front-page targets (unique; never create).
    for course in plan.get("academic_courses", []):
        cid = course["course_id"]
        slug = course["to_page_slug"]
        if cid is None:
            blockers.append(f"{course['subject']}: no course mapping")
            continue
        res = _resolve_target(client, cid, slug, course["label"], plan["to_week"])
        live["academic"][course["subject"]] = res
        blockers.extend(res["blockers"])
        course["page_id"] = res["page_id"]
        course["already_front_page"] = res["front_page"]
        course["front_page_action"] = "SKIP" if res["front_page"] else "SET_FRONT_PAGE"
        if res["page_id"] is not None:
            try:
                current = client.get_page(cid, slug)
                matches = _canvas_body_hash(current.get("body") or "") == course.get("to_page_hash")
                course["page_body_action"] = "SKIP" if matches else "UPDATE"
                res["page_body_action"] = course["page_body_action"]
            except Exception as exc:  # noqa: BLE001
                blockers.append(f"{course['subject']}: page body lookup failed: {type(exc).__name__}")

    # Homeroom target.
    h = plan.get("homeroom")
    if h:
        hres = _resolve_target(client, h["course_id"], h["to_page_slug"], "Homeroom", plan["to_week"])
        live["homeroom"] = hres
        blockers.extend(hres["blockers"])
        h["page_id"] = hres["page_id"]
        h["already_front_page"] = hres["front_page"]
        h["front_page_action"] = "SKIP" if hres["front_page"] else "SET_FRONT_PAGE"
        # Homeroom HTML approval binds to the exact weekly page id: fail if the
        # live-resolved target no longer matches the approved page id.
        if (h.get("mode") in ("rolling_newsletter_html", "homeroom_weekly_newsletter_html")
                and h.get("to_page_id") is not None
                and str(hres["page_id"]) != str(h.get("to_page_id"))):
            blockers.append("homeroom: weekly page id changed (approved target mismatch)")
        if hres["page_id"] is not None:
            try:
                from . import homeroom as homeroom_mod
                current = client.get_page(h["course_id"], h["to_page_slug"])
                matches = _canvas_body_hash(current.get("body") or "") == _manifest_body_hash(h)
                h["page_body_action"] = "SKIP" if matches else "UPDATE"
                hres["page_body_action"] = h["page_body_action"]
            except Exception as exc:  # noqa: BLE001
                blockers.append(f"homeroom: page body lookup failed: {type(exc).__name__}")
    else:
        live["homeroom"] = {"action": "SKIP", "blockers": []}

    # Approved assignment routes and exact duplicate dispositions.
    assignments_by_course: dict[int, list[dict[str, Any]]] = {}
    groups_by_course: dict[int, set[str]] = {}
    for assignment in plan.get("assignments", []):
        cid = int(assignment["course_id"])
        if cid not in groups_by_course:
            try:
                groups_by_course[cid] = {str(g.get("name") or "") for g in client.list_assignment_groups(cid)}
                assignments_by_course[cid] = client.list_assignments(cid)
            except Exception as exc:  # noqa: BLE001
                blockers.append(f"course {cid}: assignment lookup failed: {type(exc).__name__}")
                groups_by_course[cid], assignments_by_course[cid] = set(), []
        group = str(assignment.get("assignment_group") or "")
        if group not in groups_by_course[cid]:
            blockers.append(f"assignment {assignment.get('title')!r}: group {group!r} missing")
        title = str(assignment.get("title") or "")
        matches = _assignment_matches(assignments_by_course[cid], title)
        action = str(assignment.get("action") or "CREATE")
        if action == "BLOCKED":
            blockers.append(
                f"assignment {title!r}: {assignment.get('block_reason') or 'reconciliation blocked'}"
            )
            assignment["classification"] = "BLOCKED"
        elif len(matches) > 1:
            # Never guess which existing assignment is the target.
            blockers.append(
                f"assignment {title!r}: {len(matches)} live assignments share this exact title"
            )
            assignment["classification"] = "DUPLICATE"
            assignment["action"] = "BLOCKED"
        elif action == "UPDATE":
            approved_id = str(assignment.get("assignment_id") or "")
            if not approved_id:
                blockers.append(f"assignment {title!r}: approved update is missing its Canvas ID")
                assignment["classification"] = "UNVERIFIED"
                assignment["action"] = "BLOCKED"
            elif len(matches) != 1:
                blockers.append(f"assignment {title!r}: approved update target not found")
                assignment["classification"] = "UNVERIFIED"
                assignment["action"] = "BLOCKED"
            elif str(matches[0].get("id")) != approved_id:
                blockers.append(
                    f"assignment {title!r}: live ID {matches[0].get('id')} does not match "
                    f"approved update ID {approved_id}"
                )
                assignment["classification"] = "UNVERIFIED"
                assignment["action"] = "BLOCKED"
            else:
                corrected = (
                    _due_minute(matches[0].get("due_at"))
                    == _due_minute(assignment.get("due_utc"))
                )
                assignment["classification"] = "EXACT_MATCH" if corrected else "UPDATE_REQUIRED"
                assignment["action"] = "SKIP" if corrected else "UPDATE"
        elif action == "SKIP":
            if (len(matches) == 1
                    and _due_minute(matches[0].get("due_at"))
                    == _due_minute(assignment.get("due_utc"))):
                assignment["classification"] = "EXACT_MATCH"
                assignment["action"] = "SKIP"
            else:
                blockers.append(f"assignment {title!r}: expected existing assignment is not exact")
                assignment["classification"] = "UNVERIFIED"
                assignment["action"] = "BLOCKED"
        elif matches:
            if _due_minute(matches[0].get("due_at")) == _due_minute(assignment.get("due_utc")):
                assignment["classification"] = "EXACT_MATCH"
                assignment["action"] = "SKIP"
            else:
                # An existing title with a different due date must be updated
                # through reconciliation, never duplicated by a CREATE.
                blockers.append(
                    f"assignment {title!r}: existing assignment differs; update reconciliation required"
                )
                assignment["classification"] = "UNVERIFIED"
                assignment["action"] = "BLOCKED"
        else:
            assignment["classification"] = "NEW"
            assignment["action"] = "CREATE"
        live["assignments"][assignment.get("title")] = {
            "classification": assignment["classification"], "action": assignment["action"]}

    # Announcement duplicate classification (week-aware).
    target_ledger = ledger.load_rollover_ledger(to_quarter, to_week) or {}
    prior_announcements = target_ledger.get("weekly_announcements") or []
    for a in plan.get("weekly_announcements", []):
        cid = a["course_id"]
        if cid is None:
            continue
        try:
            existing = client.list_announcements(int(cid))
        except Exception as exc:  # noqa: BLE001
            blockers.append(f"{a['subject']}: weekly announcement lookup failed: {type(exc).__name__}")
            existing = []
        a["classification"] = deploy_preflight.classify_weekly_announcement(a, existing)
        message_hash = hashlib.sha256(str(a.get("message", "")).encode("utf-8")).hexdigest()
        if a["classification"] == "PRIOR_WEEK_SAME_TITLE" and any(
            item.get("subject") == a.get("subject")
            and item.get("title") == a.get("title")
            and item.get("message_hash") == message_hash
            and item.get("verified") is True
            for item in prior_announcements
        ):
            # An immediate Publish-now post has no delayed_post_at. Only the
            # verified ledger for this target week can prove it was ours.
            a["classification"] = "EXACT_MATCH"
        a["action"] = "SKIP" if a["classification"] == "EXACT_MATCH" else "CREATE"
        live["weekly_announcements"][a["title"]] = {
            "classification": a["classification"], "action": a["action"]}
        if a["classification"] == "BODY_CHANGED_SAME_WEEK":
            blockers.append(f"{a['subject']}: weekly update body changed within the same week (owner review required)")

    # Approved assessment reminders are Canvas announcements without delay.
    # Reconcile by assessment identity so separately scheduled, verified
    # assessment topics are NOT duplicated by the Friday rollover.
    announcement_cache: dict[int, list[dict[str, Any]]] = {}
    for reminder in plan.get("assessment_reminders", []):
        cid = int(reminder["course_id"])
        if cid not in announcement_cache:
            try:
                announcement_cache[cid] = client.list_announcements(cid)
            except Exception as exc:  # noqa: BLE001
                blockers.append(f"course {cid}: reminder lookup failed: {type(exc).__name__}")
                announcement_cache[cid] = []
        classification = deploy_preflight.classify_assessment_reminder(
            reminder, announcement_cache[cid]
        )
        reminder["classification"] = classification
        reminder["action"] = "SKIP" if classification in (
            "EXACT_MATCH", deploy_preflight.REMINDER_ALREADY_SCHEDULED,
        ) else "CREATE"
        live["assessment_reminders"][reminder.get("title")] = {
            "classification": classification, "action": reminder["action"]}

    return {
        **readiness,
        "live": live,
        "warnings": warnings,
        "blockers": blockers,
        "ready": len(blockers) == 0,
        "canvas_writes": 0,
        "scheduled_at": plan["scheduled_at"],
    }


def _resolve_target(client: DeployClient, course_id: int, slug: str, label: str, week_code: str) -> dict[str, Any]:
    """Resolve a unique front-page target page (GET-only)."""
    blockers: list[str] = []
    page_id = None
    front_page = False
    try:
        found = client.find_page(course_id, slug)
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"{label}: page lookup failed: {type(exc).__name__}")
        return {"page_id": None, "front_page": False, "blockers": blockers}
    if found is None:
        blockers.append(f"{label}: weekly page missing (cannot create a normal weekly page)")
        return {"page_id": None, "front_page": False, "blockers": blockers}

    # Duplicate detection: exactly one page must match the target slug/title.
    try:
        pages = client.list_pages(course_id)
        matches = [p for p in pages if (p.get("url") == slug or p.get("title") == found.get("title"))]
    except Exception:  # noqa: BLE001
        matches = [found]
    if len(matches) > 1:
        blockers.append(f"{label}: duplicate candidate pages for {week_code} (ambiguous target)")
        return {"page_id": None, "front_page": False, "blockers": blockers}

    page_id = found.get("page_id") or found.get("id")
    front_page = bool(found.get("front_page"))
    return {"page_id": page_id, "front_page": front_page, "blockers": blockers}


# --------------------------------------------------------------------------- #
# B–E. Guarded execution
# --------------------------------------------------------------------------- #

def _same_instant(left: str | None, right: str | None) -> bool:
    from scripts.canvas_llm_deploy.coordinator import _same_instant as _compare
    return _compare(left, right)


def _announcement_exists(client, reminder: dict[str, Any]) -> bool:
    try:
        items = client.list_announcements(reminder["course_id"])
    except Exception:  # noqa: BLE001
        return False
    message = reminder.get("message") or ""
    for item in items:
        if item.get("title") == reminder.get("title") and _canvas_owned_body(item.get("message") or "") == message:
            return True
    return False


def _parse_aware_instant(value: str | None) -> datetime | None:
    """Parse a timezone-aware instant. Naive or invalid values return None."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _stale_preflight_blockers(quarter: int, week: int, manifest: dict[str, Any]) -> list[str]:
    """A stored preflight cannot be reused after the plan changes.

    When no preflight exists, the in-process gate is the validation. When one
    exists, its fingerprint must match both the manifest and the current plan.
    """
    directory = deploy_ledger.deploy_dir(quarter, week)
    if not directory.exists():
        return []
    files = sorted(directory.glob("preflight-*.json"))
    if not files:
        return []
    try:
        stored = json.loads(files[-1].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ["stored preflight could not be read"]
    stored_fingerprint = deploy_plan.plan_fingerprint(stored.get("plan") or {})
    claimed = manifest.get("plan_fingerprint")
    if not claimed:
        return ["a preflight exists but the manifest has no plan fingerprint"]
    if claimed != stored_fingerprint:
        return ["manifest plan fingerprint does not match the stored preflight"]
    try:
        current = deploy_plan.plan_fingerprint(deploy_plan.build_plan(quarter, week))
    except Exception as exc:  # noqa: BLE001
        return [f"current plan could not be rebuilt: {type(exc).__name__}"]
    if current != stored_fingerprint:
        return ["current plan changed since preflight"]
    return []


def _authoritative_source_hash(quarter: int, week: int) -> str | None:
    """Current intake source hash. This is not the manifest's own copy."""
    from scripts.canvas_llm_intake import manifest as imf
    record = imf.load_manifest(quarter, week) or {}
    value = record.get("source_hash")
    return value if isinstance(value, str) and value else None


def _content_release(manifest: dict[str, Any]) -> bool:
    if manifest.get("weekly_announcements"):
        return True
    if (manifest.get("homeroom") or {}).get("body") or (manifest.get("homeroom") or {}).get("proposed_content"):
        return True
    return any((course.get("page_body") for course in manifest.get("academic_courses") or []))


def _future_schedule_blocker(item: dict[str, Any], *, now: datetime, label: str) -> str | None:
    """FUTURE_SCHEDULED is accepted only when the instant is actually later than now."""
    if item.get("schedule_state") != "FUTURE_SCHEDULED" and item.get("action") != "CREATE":
        return None
    if item.get("schedule_state") not in (None, "FUTURE_SCHEDULED") and item.get("action") != "CREATE":
        return None
    if item.get("schedule_state") != "FUTURE_SCHEDULED":
        return None
    raw = item.get("delayed_post_at")
    if not raw:
        return f"{label} is FUTURE_SCHEDULED without delayed_post_at"
    try:
        parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return f"{label} delayed_post_at is not a valid timestamp"
    if parsed.tzinfo is None:
        return f"{label} delayed_post_at must include a timezone"
    if parsed.astimezone(timezone.utc) <= now.astimezone(timezone.utc):
        return f"{label} delayed_post_at is not in the future"
    return None


def _explicit_page_approval_blockers(record: dict[str, Any], label: str) -> list[str]:
    """Approval must be the boolean True. Missing, null, and false all block."""
    blockers: list[str] = []
    if record.get("approved") is not True:
        blockers.append(f"{label} approved is not true")
    status = record.get("status") or record.get("approval_state")
    if status in ("PENDING", "BLOCKED"):
        blockers.append(f"{label} approval status is {status}")
    if not record.get("course_id"):
        blockers.append(f"{label} course id is missing")
    approval_hash = (
        record.get("approval_hash")
        or record.get("approved_body_hash")
        or record.get("to_page_hash")
        or record.get("proposed_content_hash")
    )
    if not approval_hash:
        blockers.append(f"{label} approval hash is missing")
    current_hash = record.get("current_hash")
    if current_hash is not None and approval_hash != current_hash:
        blockers.append(f"{label} approval hash does not match the current page")
    if record.get("page_id") and record.get("to_page_id") and str(record.get("page_id")) != str(record.get("to_page_id")):
        blockers.append(f"{label} page id changed")
    return blockers


def _agenda_hash_blocker(manifest: dict[str, Any]) -> str | None:
    """Verify the stored agenda composite. A missing field stays compatible with older plans."""
    if "agenda_hash" not in manifest:
        return None
    claimed = manifest.get("agenda_hash")
    if not claimed:
        return "manifest agenda hash is missing"
    agendas: dict[str, str] = {}
    for item in manifest.get("weekly_announcements") or []:
        subject = str(item.get("subject") or "")
        digest = item.get("agenda_hash")
        if not subject or not digest:
            return "weekly announcement agenda hash is missing"
        agendas[subject] = str(digest)
    expected = deploy_plan.agenda_composite_hash(str(manifest.get("to_week") or ""), agendas)
    if claimed != expected:
        return "manifest agenda hash does not match the weekly agendas"
    if claimed == manifest.get("source_hash"):
        return "agenda hash cannot stand in for the intake source hash"
    return None


def _prewrite_blockers(
    manifest: dict[str, Any],
    client,
    *,
    now: datetime,
    quarter: int,
    week: int,
) -> list[str]:
    """Validate the whole release before any Canvas mutation."""
    blockers: list[str] = []
    if manifest.get("publication_time_required") and not manifest.get("owner_publication_time"):
        blockers.append("publication time required")
    if _content_release(manifest):
        claimed = manifest.get("source_hash")
        authoritative = _authoritative_source_hash(quarter, week)
        if not claimed:
            blockers.append("manifest source hash is missing")
        elif not authoritative:
            blockers.append("authoritative source snapshot is missing")
        elif claimed != authoritative:
            blockers.append("manifest source hash does not match the authoritative source")
        claimed_fingerprint = manifest.get("plan_fingerprint")
        if claimed_fingerprint:
            intake_fingerprint = (imf.load_manifest(quarter, week) or {}).get("plan_fingerprint")
            if claimed_fingerprint != intake_fingerprint:
                blockers.append("manifest plan fingerprint does not match the intake manifest")
        agenda_problem = _agenda_hash_blocker(manifest)
        if agenda_problem:
            blockers.append(agenda_problem)
    required_subjects = ("math", "reading_spelling", "language_arts", "science")
    present = {course.get("subject") for course in manifest.get("academic_courses") or []}
    announced = {item.get("subject") for item in manifest.get("weekly_announcements") or []}
    if set(required_subjects) <= announced:
        missing = [subject for subject in required_subjects if subject not in present]
        if missing:
            blockers.append("five-course release is missing " + ", ".join(missing))
        if not manifest.get("homeroom"):
            blockers.append("five-course release is missing homeroom")
    for course in manifest.get("academic_courses") or []:
        subject = course.get("subject") or course.get("label")
        blockers.extend(_explicit_page_approval_blockers(course, str(subject)))
    for announcement in manifest.get("weekly_announcements") or []:
        title = announcement.get("title")
        if announcement.get("action") == "BLOCKED" or announcement.get("schedule_state") in (
            "OWNER_TIME_REQUIRED", "BLOCKED",
        ):
            blockers.append(f"weekly announcement {title} is blocked")
        if announcement.get("duplicate_classification") == "AMBIGUOUS" or announcement.get("duplicate_status") == "AMBIGUOUS":
            blockers.append(f"weekly announcement {title} identity is ambiguous")
        if not announcement.get("course_id"):
            blockers.append(f"weekly announcement {title} has no course id")
        if (
            announcement.get("classification") != "EXACT_MATCH"
            and announcement.get("schedule_state") != "IMMEDIATE_CONFIRMED"
            and not announcement.get("delayed_post_at")
        ):
            blockers.append(f"weekly announcement {title} has no delayed_post_at")
        if announcement.get("approved") is not True and announcement.get("approval_state") != "APPROVED":
            blockers.append(f"weekly announcement {title} approved is not true")
        if (announcement.get("status") or announcement.get("approval_state")) in ("PENDING", "BLOCKED"):
            blockers.append(f"weekly announcement {title} approval status is {announcement.get('status') or announcement.get('approval_state')}")
        future_problem = _future_schedule_blocker(announcement, now=now, label=f"weekly announcement {title}")
        if future_problem:
            blockers.append(future_problem)
    for reminder in manifest.get("assessment_reminders") or []:
        title = reminder.get("title")
        if reminder.get("classification") == "ALREADY_SCHEDULED_VERIFIED":
            continue
        if reminder.get("action") == "BLOCKED" or reminder.get("schedule_state") in (
            "OWNER_TIME_REQUIRED", "BLOCKED",
        ):
            blockers.append(f"assessment notice {title} is blocked")
        if reminder.get("duplicate_status") == "AMBIGUOUS":
            blockers.append(f"assessment notice {title} identity is ambiguous")
        if reminder.get("approved") is not True and reminder.get("approval_state") != "APPROVED":
            blockers.append(f"assessment notice {title} approved is not true")
        if (reminder.get("status") or reminder.get("approval_state")) in ("PENDING", "BLOCKED"):
            blockers.append(f"assessment notice {title} approval status is {reminder.get('status') or reminder.get('approval_state')}")
        if reminder.get("content_status") not in (None, "READY"):
            blockers.append(f"assessment notice {title} resource is unverified")
        if not reminder.get("course_id"):
            blockers.append(f"assessment notice {title} has no course id")
        future_problem = _future_schedule_blocker(reminder, now=now, label=f"assessment notice {title}")
        if future_problem:
            blockers.append(future_problem)
            continue
        if _announcement_exists(client, reminder):
            continue
        future = reminder.get("schedule_state") == "FUTURE_SCHEDULED" and reminder.get("delayed_post_at")
        if not future and not reminder.get("delayed_post_at"):
            blockers.append(f"assessment notice {title} would post immediately")
    for assignment in manifest.get("assignments") or []:
        if assignment.get("action") == "BLOCKED":
            blockers.append(f"assignment {assignment.get('title')} is blocked")
        elif assignment.get("approved") is not True and assignment.get("approval_state") != "APPROVED":
            blockers.append(f"assignment {assignment.get('title')} approved is not true")
        if not assignment.get("course_id"):
            blockers.append(f"assignment {assignment.get('title')} has no course id")
    homeroom = manifest.get("homeroom") or {}
    announced = {item.get("subject") for item in manifest.get("weekly_announcements") or []}
    if (
        homeroom.get("mode") == "homeroom_weekly_newsletter_html"
        and set(required_subjects) <= announced
        and not manifest.get("homeroom_announcement")
    ):
        blockers.append("homeroom announcement is missing")
    if manifest.get("homeroom"):
        blockers.extend(_explicit_page_approval_blockers(homeroom, "homeroom"))
    family = manifest.get("homeroom_announcement")
    if family:
        future_problem = _future_schedule_blocker(family, now=now, label="homeroom announcement")
        if future_problem:
            blockers.append(future_problem)
        if not homeroom.get("approved"):
            blockers.append("homeroom page is not approved")
        if not homeroom.get("to_page_id"):
            blockers.append("homeroom page id is missing")
        if str(family.get("page_id")) != str(homeroom.get("to_page_id")):
            blockers.append("homeroom announcement page id does not match the page")
        if family.get("publication_dependency") != "HOMEROOM_PAGE_PUBLISHED_AND_VERIFIED":
            blockers.append("homeroom announcement is missing its page-first dependency")
        if family.get("approval_state") != "APPROVED":
            blockers.append("homeroom announcement is not approved")
        if family.get("schedule_state") != "FUTURE_SCHEDULED" or not family.get("delayed_post_at"):
            blockers.append("homeroom announcement publication time is not scheduled")
    return blockers


def _publication_records_agree(existing, published, intake) -> bool:
    """True only when rollover, published ledger, and intake all say the same release."""
    if not isinstance(existing, dict) or existing.get("lifecycle") != schedule.PUBLISHED_VERIFIED:
        return False
    if not isinstance(published, dict) or published.get("status") != schedule.PUBLISHED_VERIFIED:
        return False
    if not isinstance(intake, dict) or intake.get("status") != schedule.PUBLISHED_VERIFIED:
        return False
    if intake.get("approval_state") != "APPROVED":
        return False
    source = intake.get("source_hash")
    fingerprint = intake.get("plan_fingerprint")
    if not source or not fingerprint:
        return False
    return (
        published.get("source_hash") == source
        and published.get("plan_fingerprint") == fingerprint
        and existing.get("source_hash") == source
        and existing.get("plan_fingerprint") == fingerprint
    )


def _restore_rollover_completion(quarter: int, week: int, published: dict, intake: dict) -> dict[str, Any]:
    """Write the missing rollover completion record. Do not touch Canvas."""
    record = {
        "lifecycle": schedule.PUBLISHED_VERIFIED,
        "source_hash": intake.get("source_hash"),
        "plan_fingerprint": intake.get("plan_fingerprint"),
        "recovered_from": "published-verified-ledger",
        "verified_at": published.get("verified_at"),
    }
    try:
        ledger.write_rollover_ledger(quarter, week, record)
        written = ledger.load_rollover_ledger(quarter, week)
    except Exception as exc:  # noqa: BLE001
        return {
            "lifecycle": "PUBLICATION_VERIFIED_ROLLOVER_INCOMPLETE",
            "already_complete": False,
            "failures": [f"rollover completion record could not be written: {type(exc).__name__}"],
            "source_hash": intake.get("source_hash"),
            "plan_fingerprint": intake.get("plan_fingerprint"),
        }
    if not _publication_records_agree(written, published, intake):
        return {
            "lifecycle": "PUBLICATION_VERIFIED_ROLLOVER_INCOMPLETE",
            "already_complete": False,
            "failures": ["rollover completion record did not read back"],
            "source_hash": intake.get("source_hash"),
            "plan_fingerprint": intake.get("plan_fingerprint"),
        }
    return {
        "lifecycle": schedule.PUBLISHED_VERIFIED,
        "already_complete": True,
        "rollover_recovered": True,
    }


def _five_course_report(report: dict[str, Any]) -> bool:
    subjects = {item.get("subject") for item in report.get("pages") or []}
    homeroom = report.get("homeroom") if isinstance(report.get("homeroom"), dict) else {}
    if homeroom.get("verified") is True:
        subjects.add("homeroom")
    return set(deploy_ledger.REQUIRED_COURSES) <= subjects


def _finalization_evidence(quarter: int, week: int, report: dict[str, Any], manifest: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    """Build finalizer evidence from the executed plan and the intake manifest."""
    intake = imf.load_manifest(quarter, week) or {}
    source = manifest.get("source_hash")
    fingerprint = manifest.get("plan_fingerprint")
    failures: list[str] = []
    if not source or source != intake.get("source_hash"):
        failures.append("execution source hash does not match the intake manifest")
    if not fingerprint or fingerprint != intake.get("plan_fingerprint"):
        failures.append("execution plan fingerprint does not match the intake manifest")
    if intake.get("approval_state") != "APPROVED":
        failures.append("intake approval is not explicitly approved")
    if report.get("failures"):
        failures.append("deployment report has outstanding failures")
    evidence = {
        "school_year": report.get("school_year"),
        "quarter": quarter,
        "week": week,
        "week_code": report.get("to_week"),
        "verified_at": report.get("finished_at"),
        "status": "PUBLISHED_VERIFIED",
        "publisher": "FRIDAY_ROLLOVER",
        "source_hash": source,
        "plan_fingerprint": fingerprint,
        "pages": report.get("pages"),
        "assignments": report.get("assignments"),
        "weekly_announcements": report.get("weekly_announcements"),
        "assessment_reminders": report.get("assessment_reminders"),
        "homeroom": report.get("homeroom"),
        "communication": report.get("communication"),
    }
    family = report.get("homeroom_announcement")
    if isinstance(family, dict):
        evidence["homeroom_announcement"] = family
        evidence["homeroom_page_before_announcement"] = True
    return (None, failures) if failures else (evidence, [])


def _blocked_finalization(quarter: int, week: int, report: dict[str, Any], failures: list[str]) -> dict[str, Any]:
    report["lifecycle"] = "FINALIZATION_BLOCKED"
    report["failures"] = list(report.get("failures") or []) + failures
    report["already_complete"] = False
    ledger.write_rollover_ledger(quarter, week, report)
    return report


def _finalize_five_course(quarter: int, week: int, report: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    """Finalize first. A rollover ledger may say PUBLISHED_VERIFIED only after that succeeds."""
    evidence, problems = _finalization_evidence(quarter, week, report, manifest)
    if problems or evidence is None:
        return _blocked_finalization(quarter, week, report, problems or ["finalization evidence is missing"])
    try:
        result = deploy_ledger.finalize_published_verified(quarter, week, evidence)
    except Exception as exc:  # noqa: BLE001
        return _blocked_finalization(
            quarter, week, report, [f"finalizer raised {type(exc).__name__}"],
        )
    if not isinstance(result, dict) or result.get("status") != "PUBLISHED_VERIFIED":
        detail = []
        if isinstance(result, dict):
            detail.extend(result.get("failures") or ["finalizer did not return PUBLISHED_VERIFIED"])
        else:
            detail.append("finalizer returned no result")
        return _blocked_finalization(quarter, week, report, detail)
    report["lifecycle"] = schedule.PUBLISHED_VERIFIED
    report["source_hash"] = evidence["source_hash"]
    report["plan_fingerprint"] = evidence["plan_fingerprint"]
    report["already_complete"] = False
    try:
        ledger.write_rollover_ledger(quarter, week, report)
        written = ledger.load_rollover_ledger(quarter, week)
    except Exception as exc:  # noqa: BLE001
        report["lifecycle"] = "PUBLICATION_VERIFIED_ROLLOVER_INCOMPLETE"
        report["failures"] = [f"publication is verified but the rollover ledger was not written: {type(exc).__name__}"]
        return report
    if not isinstance(written, dict) or written.get("lifecycle") != schedule.PUBLISHED_VERIFIED:
        report["lifecycle"] = "PUBLICATION_VERIFIED_ROLLOVER_INCOMPLETE"
        report["failures"] = ["publication is verified but the rollover ledger did not read back"]
        return report
    _record_publish_event(quarter, week, report, partial=False)
    return report


def execute(
    from_quarter: int,
    from_week: int,
    to_quarter: int,
    to_week: int,
    *,
    client: DeployClient,
    owner_confirmation: str,
    today: date | None = None,
    now: datetime | None = None,
    manifest: dict[str, Any] | None = None,
    partial: bool = False,
    early_content_only: bool = False,
) -> dict[str, Any]:
    """Execute the approved rollover (ordered, stop-on-failure, idempotent)."""
    to_code = plan_code = (manifest or {}).get("to_week") or ""
    if not manifest:
        manifest = rollover_manifest.build_rollover_manifest(
            from_quarter, from_week, to_quarter, to_week, today=today
        )
    to_code = manifest["to_week"]

    if not _confirm_ok(owner_confirmation, to_code):
        raise RolloverBlocked(
            f"owner confirmation missing (must be exactly 'ROLLOVER {to_code.upper()}')"
        )

    existing = ledger.load_rollover_ledger(to_quarter, to_week)
    published = deploy_ledger.load_published_verified(to_quarter, to_week)
    intake = imf.load_manifest(to_quarter, to_week) or {}
    if _publication_records_agree(existing, published, intake):
        return {"lifecycle": schedule.PUBLISHED_VERIFIED, "already_complete": True}
    if (
        isinstance(intake, dict)
        and intake.get("status") == "PUBLISHED_VERIFIED"
        and isinstance(published, dict)
        and published.get("status") == "PUBLISHED_VERIFIED"
        and published.get("source_hash") == intake.get("source_hash")
        and published.get("plan_fingerprint") == intake.get("plan_fingerprint")
    ):
        return _restore_rollover_completion(to_quarter, to_week, published, intake)
    if existing and existing.get("lifecycle") == schedule.PUBLISHED_VERIFIED:
        return {
            "lifecycle": "FINALIZATION_INCOMPLETE",
            "already_complete": False,
            "failures": [
                "rollover ledger claims publication but the published ledger and intake manifest do not agree"
            ],
        }

    # Publication-time gate. A caller that knows "now" (the scheduler or a
    # release-plan execution) must never reuse an expired delayed-post instant.
    # A release-plan manifest that explicitly requires owner time cannot bypass
    # the gate merely by omitting ``now``.
    if now is None and manifest.get("publication_time_required"):
        raise RolloverBlocked(
            "publication time required: now must be supplied for a release plan "
            "that requires an owner-selected timestamp"
        )
    if now is not None:
        from scripts.instructional_weeks import week_range
        from scripts.canvas_llm_intake import week_resolution as _wr
        bounds = week_range(_wr.find_week(to_quarter, to_week) or {})
        if bounds is None:
            raise RolloverBlocked("target week dates are unavailable")
        try:
            resolved = schedule.resolve_publication_time(
                bounds[0].isoformat(),
                now=now,
                owner_selected_at=manifest.get("owner_publication_time"),
            )
        except ValueError as exc:
            raise RolloverBlocked(f"invalid publication time: {exc}") from exc
        if resolved["requires_owner_time"]:
            raise RolloverBlocked(
                "publication time required: the canonical Friday 4:00 PM window has passed; "
                "supply an explicit future owner_publication_time"
            )
        manifest = copy.deepcopy(manifest)
        manifest["scheduled_at"] = resolved["scheduled_at"]
        manifest["publication_time_source"] = resolved["source"]
        manifest["canonical_scheduled_at"] = resolved["canonical_scheduled_at"]
        # Announcement schedule state is validated as submitted. A resolved
        # Friday or owner time must not rewrite BLOCKED, OWNER_TIME_REQUIRED,
        # or an already-recorded delayed_post_at before the gate.
    elif _content_release(manifest):
        manifest = copy.deepcopy(manifest)

    clock = now if now is not None else datetime.now(timezone.utc)
    if clock.tzinfo is None:
        raise RolloverBlocked("execution clock must be timezone-aware")
    prewrite = _prewrite_blockers(manifest, client, now=clock, quarter=to_quarter, week=to_week)
    prewrite.extend(_stale_preflight_blockers(to_quarter, to_week, manifest))
    if prewrite:
        return {
            "lifecycle": schedule.BLOCKED,
            "failures": prewrite,
            "verb_totals": {"GET": 0, "POST": 0, "PUT": 0, "PATCH": 0, "DELETE": 0},
            "canvas_writes": 0,
            "email_sends": 0,
            "already_complete": False,
        }

    counts: dict[str, int] = {"GET": 0, "POST": 0, "PUT": 0, "PATCH": 0, "DELETE": 0}
    report: dict[str, Any] = {
        "school_year": "2026-2027",
        "from_week": manifest["from_week"],
        "to_week": manifest["to_week"],
        "scheduled_at": manifest["scheduled_at"],
        "timezone": manifest["timezone"],
        "lifecycle": schedule.EXECUTING,
        "started_at": _now(),
        "verb_totals": counts,
        "academic_front_pages": [],
        "pages": [],
        "assignments": [],
        "homeroom": {},
        "weekly_announcements": [],
        "assessment_reminders": [],
        "failures": [],
        "notes": (["Early publish: page bodies, approved assignments, and reminders only; front pages and weekly updates remain for Friday 4 PM."]
                  if early_content_only else []),
    }
    ledger.write_rollover_ledger(to_quarter, to_week, report)

    # ---- B. Academic front-page rollover ---------------------------------
    for course in manifest.get("academic_courses", []):
        cid = course["course_id"]
        subject = course["subject"]
        try:
            res = _resolve_target(client, cid, course["to_page_slug"], course["label"], to_code)
            counts["GET"] += 1
        except Exception as exc:  # noqa: BLE001
            report["failures"].append(f"{subject}: front-page resolve failed: {type(exc).__name__}")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
        if res["blockers"]:
            report["failures"].append(f"{subject}: {res['blockers'][0]}")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
        pid = res["page_id"]
        body = course.get("page_body") or ""
        if not body:
            report["failures"].append(f"{subject}: approved page body missing")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
        try:
            current = client.get_page(cid, course["to_page_slug"])
            counts["GET"] += 1
            if _canvas_body_hash(current.get("body") or "") != course.get("to_page_hash"):
                client.update_page(
                    cid, course["to_page_slug"], body=body,
                    published=True, front_page=bool(current.get("front_page")),
                )
                counts["PUT"] += 1
            page_readback = client.get_page(cid, course["to_page_slug"])
            counts["GET"] += 1
        except Exception as exc:  # noqa: BLE001
            report["failures"].append(f"{subject}: page update failed: {type(exc).__name__}")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
        page_ok = _canvas_body_hash(page_readback.get("body") or "") == course.get("to_page_hash")
        report["pages"].append({
            "subject": subject, "course_id": cid, "page_id": pid,
            "disposition": "PUBLISHED_VERIFIED" if page_ok else "FAILED", "verified": page_ok,
        })
        if not page_ok:
            report["failures"].append(f"{subject}: page body readback mismatch")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
        if early_content_only:
            report["academic_front_pages"].append({
                "subject": subject, "course_id": cid, "page_id": pid,
                "disposition": "HELD_UNTIL_4PM", "verified": True,
            })
            continue
        if res["front_page"]:
            report["academic_front_pages"].append(
                {"subject": subject, "course_id": cid, "page_id": pid, "disposition": "ALREADY_FRONT_PAGE"}
            )
            continue
        try:
            client.set_front_page(cid, pid)
            counts["PUT"] += 1
            readback = client.get_page(cid, course["to_page_slug"])
            counts["GET"] += 1
        except Exception as exc:  # noqa: BLE001
            report["failures"].append(f"{subject}: front-page write failed: {type(exc).__name__}")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
        ok = str(readback.get("page_id")) == str(pid) and bool(readback.get("front_page"))
        report["academic_front_pages"].append({
            "subject": subject, "course_id": cid, "page_id": pid,
            "disposition": "PUBLISHED_VERIFIED" if ok else "FAILED", "verified": ok,
        })
        if not ok:
            report["failures"].append(f"{subject}: front-page readback mismatch")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)

    # ---- C. Homeroom rollover --------------------------------------------
    h = manifest.get("homeroom")
    if h:
        homeroom_result = _execute_homeroom(
            client, h, to_code=to_code, counts=counts, report=report,
            to_quarter=to_quarter, to_week=to_week,
            early_content_only=early_content_only,
        )
        if homeroom_result is not None:
            return homeroom_result

    announcement = manifest.get("homeroom_announcement")
    if announcement:
        if not (report.get("homeroom") or {}).get("verified"):
            report["failures"].append("homeroom announcement: page publication was not verified first")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
        if str(announcement.get("page_id")) != str((h or {}).get("to_page_id")):
            report["failures"].append("homeroom announcement: page id changed")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
        if not announcement.get("contains_complete_newsletter_html"):
            report["failures"].append("homeroom announcement: complete newsletter HTML is missing")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
        if announcement.get("action") == "BLOCKED" or announcement.get("schedule_state") != "FUTURE_SCHEDULED":
            report["failures"].append("homeroom announcement: owner-selected publication time required")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
        try:
            created = client.create_announcement(
                announcement["course_id"], title=announcement["title"],
                message=announcement.get("message") or "", published=True,
                delayed_post_at=announcement.get("delayed_post_at"),
            )
            counts["POST"] += 1
            readback = client.get_announcement(announcement["course_id"], str(created.get("id")))
            counts["GET"] += 1
            in_feed = any(
                (item.get("title") or "") == announcement["title"]
                for item in client.list_active_announcements(
                    context_codes=[f"course_{announcement['course_id']}"]
                )
            )
            counts["GET"] += 1
            from scripts.canvas_llm_intake import scheduling as sched
            state = sched.classify_announcement(
                delayed_post_at=readback.get("delayed_post_at"),
                posted_at=readback.get("posted_at"),
                published=readback.get("published"),
                in_active_feed=in_feed,
            )
            delayed = announcement.get("delayed_post_at") or ""
            page_body = _canvas_owned_body((h or {}).get("body") or "")
            live_message = _canvas_owned_body(readback.get("message") or "")
            expected_message = _canvas_owned_body(announcement.get("message") or "")
            course_ok = (
                readback.get("course_id") is not None
                and int(readback.get("course_id")) == int(announcement["course_id"])
            )
            ok = (
                readback.get("title") == announcement["title"]
                and live_message == expected_message
                and state == sched.HELD_SCHEDULED
                and _same_instant(readback.get("delayed_post_at"), delayed)
                and course_ok
                and (not page_body or page_body in live_message)
            )
        except Exception as exc:  # noqa: BLE001
            report["failures"].append(f"homeroom announcement: write failed: {type(exc).__name__}")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
        report["homeroom_announcement"] = {
            "course_id": announcement["course_id"],
            "page_id": announcement.get("page_id"),
            "title": announcement["title"],
            "announcement_id": created.get("id"),
            "delayed_post_at": readback.get("delayed_post_at"),
            "state": state,
            "disposition": "SCHEDULED_VERIFIED" if ok else "FAILED",
            "verified": ok,
        }
        if not ok:
            report["failures"].append("homeroom announcement: readback mismatch")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)

    # ---- D. Approved assignments ----------------------------------------
    for a in manifest.get("assignments", []):
        title = a["title"]
        cid = a["course_id"]
        action = str(a.get("action") or "CREATE")
        try:
            live_assignments = client.list_assignments(cid)
            counts["GET"] += 1
        except Exception as exc:  # noqa: BLE001
            report["failures"].append(f"assignment {title!r}: lookup failed: {type(exc).__name__}")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
        matches = _assignment_matches(live_assignments, title)
        if len(matches) > 1:
            report["failures"].append(
                f"assignment {title!r}: {len(matches)} live assignments share this exact title")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)

        try:
            if action == "UPDATE":
                approved_id = str(a.get("assignment_id") or "")
                if not approved_id:
                    report["failures"].append(f"assignment {title!r}: missing approved Canvas ID")
                    return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
                if len(matches) != 1:
                    report["failures"].append(f"assignment {title!r}: update target not found")
                    return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
                live = matches[0]
                if str(live.get("id")) != approved_id:
                    report["failures"].append(
                        f"assignment {title!r}: live ID {live.get('id')} != approved ID {approved_id}")
                    return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
                group_id = live.get("assignment_group_id")
                if _due_minute(live.get("due_at")) == _due_minute(a.get("due_utc")):
                    created = live
                    disposition = "ALREADY_EXISTS"
                else:
                    corrections = a.get("corrections") or {}
                    unsupported = sorted(set(corrections) - {"due_at"})
                    if unsupported:
                        report["failures"].append(
                            f"assignment {title!r}: unsupported correction fields {unsupported}")
                        return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
                    required_due = (corrections.get("due_at") or {}).get("required") or a.get("due_utc")
                    # UPDATE only the fields the approved reconciliation named.
                    client.update_assignment(cid, approved_id, due_at=required_due)
                    counts["PUT"] += 1
                    created = client.get_assignment(cid, approved_id)
                    counts["GET"] += 1
                    disposition = "UPDATED_VERIFIED"
                ok = _assignment_readback_ok(created, a, expected_group_id=group_id)
            elif action == "SKIP":
                if len(matches) != 1:
                    report["failures"].append(f"assignment {title!r}: expected assignment missing")
                    return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
                created = matches[0]
                disposition = "ALREADY_EXISTS"
                ok = _assignment_readback_ok(created, a)
            else:
                exact = [item for item in matches
                         if _due_minute(item.get("due_at")) == _due_minute(a.get("due_utc"))]
                if exact:
                    created = exact[0]
                    disposition = "ALREADY_EXISTS"
                    ok = _assignment_readback_ok(created, a)
                elif matches:
                    # Never create a replacement for an existing assignment.
                    report["failures"].append(
                        f"assignment {title!r}: existing assignment differs; refusing to duplicate")
                    return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
                else:
                    created = client.create_assignment(
                        cid, title=title, description=a.get("description", ""),
                        assignment_group=a["assignment_group"], points=a["points_possible"],
                        grading_type=a["grading_type"],
                        submission_type=_submission_type(a.get("submission_types")),
                        due_at=a.get("due_utc") or "",
                        counts_toward_final_grade=not a.get("omit_from_final_grade", False),
                        published=True,
                    )
                    counts["POST"] += 1
                    readback = client.get_assignment(cid, str(created.get("id")))
                    counts["GET"] += 1
                    created = readback
                    disposition = "PUBLISHED_VERIFIED"
                    ok = _assignment_readback_ok(created, a)
        except Exception as exc:  # noqa: BLE001
            # An uncertain write is never retried automatically.
            report["failures"].append(f"assignment {title!r}: write failed: {type(exc).__name__}")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
        report["assignments"].append({
            "subject": a.get("course"), "course_id": cid, "title": title,
            "action": action,
            "assignment_id": created.get("id"), "disposition": disposition if ok else "FAILED",
            "due_at": created.get("due_at"), "verified": ok,
        })
        if not ok:
            report["failures"].append(f"assignment {title!r}: readback mismatch")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)

    # ---- E. Weekly updates and approved reminders -----------------------
    for a in ([] if early_content_only else manifest.get("weekly_announcements", [])):
        cid = a["course_id"]
        if a.get("classification") == "EXACT_MATCH":
            report["weekly_announcements"].append(
                {"subject": a["subject"], "title": a["title"],
                 "message_hash": hashlib.sha256(str(a.get("message", "")).encode("utf-8")).hexdigest(),
                 "disposition": "ALREADY_EXISTS", "verified": True})
            continue
        try:
            created = client.create_announcement(
                cid, title=a["title"], message=a["message"], published=True,
                delayed_post_at=a.get("delayed_post_at"))
            counts["POST"] += 1
            tid = created.get("id")
            announcement_readback = client.get_announcement(cid, str(tid))
            counts["GET"] += 1
        except Exception as exc:  # noqa: BLE001
            report["failures"].append(f"{a['subject']}: announcement write failed: {type(exc).__name__}")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
        # A run before 4 PM is held; a due/manual run may already be posted.
        in_feed = False
        try:
            in_feed = any(
                (x.get("title") or "") == a["title"]
                for x in client.list_active_announcements(context_codes=[f"course_{cid}"])
            )
            counts["GET"] += 1
        except Exception:  # noqa: BLE001
            in_feed = False
        from scripts.canvas_llm_intake import scheduling as sched
        state = sched.classify_announcement(
            delayed_post_at=a.get("delayed_post_at"), posted_at=created.get("posted_at"),
            published=created.get("published"), in_active_feed=in_feed)
        # Canvas prepends its account-level canvas_global_app.css <link> to
        # announcement messages on write (same injection as wiki-page bodies).
        # Normalize it off before comparing, so verification binds to our
        # authored message rather than Canvas-owned global assets.
        live_message = _canvas_owned_body(announcement_readback.get("message") or "")
        content_ok = (
            announcement_readback.get("title") == a["title"]
            and live_message == a["message"]
        )
        ok = content_ok and state in (sched.HELD_SCHEDULED, sched.POSTED)
        if not ok:
            disposition = "FAILED"
        elif state == sched.HELD_SCHEDULED:
            disposition = "SCHEDULED_VERIFIED"
        else:
            disposition = "PUBLISHED_VERIFIED"
        report["weekly_announcements"].append({
            "subject": a["subject"], "title": a["title"], "announcement_id": tid,
            "message_hash": hashlib.sha256(str(a.get("message", "")).encode("utf-8")).hexdigest(),
            "delayed_post_at": a.get("delayed_post_at"), "state": state,
            "disposition": disposition, "verified": ok,
        })
        if not ok:
            report["failures"].append(f"{a['subject']}: announcement visibility mismatch ({state})")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)

    for a in manifest.get("assessment_reminders", []):
        title = a["title"]
        if a.get("classification") == deploy_preflight.REMINDER_ALREADY_SCHEDULED:
            # Already satisfied by a separately scheduled, verified Canvas
            # assessment topic (reconciled during preflight); never duplicate.
            report["assessment_reminders"].append({
                "subject": a.get("subject"), "course_id": a["course_id"], "title": title,
                "announcement_id": None, "disposition": "ALREADY_SCHEDULED_VERIFIED",
                "verified": True,
            })
            continue
        if a.get("action") == "BLOCKED" or a.get("schedule_state") in ("OWNER_TIME_REQUIRED", "BLOCKED"):
            report["failures"].append(
                f"reminder {title!r}: publication blocked ({a.get('schedule_state') or a.get('action')})"
            )
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
        scheduled = bool(a.get("scheduled")) and bool(a.get("delayed_post_at"))
        delayed = a.get("delayed_post_at") if scheduled else None
        try:
            exact = next((item for item in client.list_announcements(a["course_id"])
                          if item.get("title") == title
                          and _canvas_owned_body(item.get("message") or "") == a.get("message", "")
                          and (not scheduled or _same_instant(item.get("delayed_post_at"), delayed))), None)
            counts["GET"] += 1
            if exact:
                created = exact
                disposition = "ALREADY_EXISTS"
            else:
                created = client.create_announcement(
                    a["course_id"], title=title, message=a.get("message", ""),
                    published=True, delayed_post_at=delayed,
                )
                counts["POST"] += 1
                disposition = "SCHEDULED_VERIFIED" if scheduled else "PUBLISHED_VERIFIED"
            readback = client.get_announcement(a["course_id"], str(created.get("id")))
            counts["GET"] += 1
            message_ok = _canvas_owned_body(readback.get("message") or "") == a.get("message", "")
            delay_ok = True
            state = None
            if scheduled:
                in_feed = any(
                    (item.get("title") or "") == title
                    for item in client.list_active_announcements(context_codes=[f"course_{a['course_id']}"])
                )
                counts["GET"] += 1
                from scripts.canvas_llm_intake import scheduling as sched
                state = sched.classify_announcement(
                    delayed_post_at=readback.get("delayed_post_at"),
                    posted_at=readback.get("posted_at"),
                    published=readback.get("published"),
                    in_active_feed=in_feed,
                )
                delay_ok = state == sched.HELD_SCHEDULED and _same_instant(readback.get("delayed_post_at"), delayed)
                if delay_ok and disposition != "ALREADY_EXISTS":
                    disposition = "SCHEDULED_VERIFIED"
            course_ok = (
                readback.get("course_id") is not None
                and int(readback.get("course_id")) == int(a["course_id"])
            )
            ok = readback.get("title") == title and message_ok and delay_ok and course_ok
        except Exception as exc:  # noqa: BLE001
            report["failures"].append(f"reminder {title!r}: write failed: {type(exc).__name__}")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
        report["assessment_reminders"].append({
            "subject": a.get("subject"), "course_id": a["course_id"], "title": title,
            "announcement_id": created.get("id"),
            "delayed_post_at": readback.get("delayed_post_at"),
            "state": state,
            "disposition": disposition if ok else "FAILED",
            "verified": ok,
        })
        if not ok:
            report["failures"].append(f"reminder {title!r}: readback mismatch")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)

    # ---- F. Finalize ------------------------------------------------------
    report["finished_at"] = _now()
    report["communication"] = {"email_sends": 0, "canvas_inbox_sends": 0}
    if early_content_only:
        report["lifecycle"] = "EARLY_CONTENT_PUBLISHED_VERIFIED"
        report["warning"] = "Weekly updates and front-page switches remain held until Friday at 4:00 PM America/New_York."
        ledger.write_rollover_ledger(to_quarter, to_week, report)
        _record_publish_event(to_quarter, to_week, report, partial=True)
        return report
    if partial:
        report["lifecycle"] = "PARTIAL_PUBLISHED_VERIFIED"
        report["warning"] = "Families may see mixed weeks; only explicitly approved courses were published."
        ledger.write_rollover_ledger(to_quarter, to_week, report)
        _record_publish_event(to_quarter, to_week, report, partial=True)
        return report
    if not _five_course_report(report):
        report["lifecycle"] = schedule.PUBLISHED_VERIFIED
        ledger.write_rollover_ledger(to_quarter, to_week, report)
        _record_publish_event(to_quarter, to_week, report, partial=False)
        return report
    return _finalize_five_course(to_quarter, to_week, report, manifest)


def _execute_homeroom(client, h, *, to_code, counts, report, to_quarter, to_week,
                      early_content_only=False):
    """Publish and verify Homeroom; return a blocking report on failure."""
    try:
        hres = _resolve_target(client, h["course_id"], h["to_page_slug"], "Homeroom", to_code)
        counts["GET"] += 1
    except Exception as exc:  # noqa: BLE001
        report["failures"].append(f"homeroom: resolve failed: {type(exc).__name__}")
        return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
    if hres["blockers"]:
        report["failures"].append(f"homeroom: {hres['blockers'][0]}")
        return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)

    from . import homeroom as homeroom_mod
    proposed_hash = _manifest_body_hash(h)
    # Production body: the exact approved weekly-newsletter HTML. The retired
    # rolling-page mode remains readable for legacy ledgers only.
    if h.get("mode") in ("rolling_newsletter_html", "homeroom_weekly_newsletter_html"):
        body = h.get("body") or ""
        if str(hres["page_id"]) != str(h.get("to_page_id")):
            report["failures"].append("homeroom: weekly page id changed (approved target mismatch)")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
    else:
        proposed = h.get("proposed_content")
        body = homeroom_mod.render_proposed(proposed) if proposed else ""
    if not body:
        report["failures"].append("homeroom: proposed content missing")
        return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)

    # Idempotent body check: skip rewrite if the upcoming page already matches.
    try:
        cur = client.get_page(h["course_id"], h["to_page_slug"])
        counts["GET"] += 1
        cur_hash = _canvas_body_hash(cur.get("body") or "")
    except Exception:  # noqa: BLE001
        cur_hash = ""
    if cur_hash != proposed_hash:
        try:
            client.update_page(
                h["course_id"], h["to_page_slug"],
                body=body, published=True, front_page=bool(hres["front_page"]),
            )
            counts["PUT"] += 1
        except Exception as exc:  # noqa: BLE001
            report["failures"].append(f"homeroom: copy-forward write failed: {type(exc).__name__}")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
    if early_content_only:
        front_page_disposition = "HELD_UNTIL_4PM"
    elif not hres["front_page"]:
        try:
            client.set_front_page(h["course_id"], hres["page_id"])
            counts["PUT"] += 1
            front_page_disposition = "SET_FRONT_PAGE"
        except Exception as exc:  # noqa: BLE001
            report["failures"].append(f"homeroom: front-page write failed: {type(exc).__name__}")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
    else:
        front_page_disposition = "ALREADY_FRONT_PAGE"
    try:
        hread = client.get_page(h["course_id"], h["to_page_slug"])
        counts["GET"] += 1
    except Exception as exc:  # noqa: BLE001
        report["failures"].append(f"homeroom: readback failed: {type(exc).__name__}")
        return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
    h_ok = (
        str(hread.get("page_id")) == str(hres["page_id"])
        and (early_content_only or bool(hread.get("front_page")))
        and _canvas_body_hash(hread.get("body") or "") == proposed_hash
    )
    report["homeroom"] = {
        "course_id": h["course_id"], "page_id": hres["page_id"],
        "disposition": "PUBLISHED_VERIFIED" if h_ok else "FAILED", "verified": h_ok,
        "front_page_disposition": front_page_disposition,
    }
    if not h_ok:
        report["failures"].append("homeroom: front-page readback mismatch")
        return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)

    return None


def _record_publish_event(to_quarter, to_week, report, *, partial):
    try:
        from scripts.canvas_planner.events import append_event
        append_event(
            imf.staging_dir(to_quarter, to_week),
            action="partial_package_published" if partial else "weekly_package_published",
            actor="friday_rollover",
            reason=("Owner explicitly published approved courses only."
                    if partial else "Friday rollover published and verified the canonical package."),
            after={"week": report["to_week"], "publisher": "FRIDAY_ROLLOVER", "partial": partial},
        )
    except OSError:
        pass


def _release_plan_record(to_quarter: int, to_week: int) -> dict[str, Any]:
    """Read the staged owner release plan (local, read-only)."""
    path = (
        imf.staging_dir(to_quarter, to_week)
        / "planner" / "rollover-release-plan.json"
    )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _attach_release_publication(
    manifest: dict[str, Any], to_quarter: int, to_week: int,
) -> dict[str, Any]:
    """Wire the owner-selected release timestamp into the execution manifest."""
    release = _release_plan_record(to_quarter, to_week)
    if not release:
        return manifest
    manifest = dict(manifest)
    manifest["canonical_scheduled_at"] = release.get("canonical_scheduled_at")
    manifest["publication_time_required"] = bool(release.get("publication_time_required"))
    if release.get("owner_publication_time"):
        manifest["owner_publication_time"] = release["owner_publication_time"]
    manifest["release_plan_status"] = release.get("status")
    return manifest


def publish_weekly_package(
    from_quarter: int, from_week: int, to_quarter: int, to_week: int, *,
    client: DeployClient, owner_confirmation: str, today: date | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Publish the all-or-nothing canonical package through the rollover engine.

    The publication-time gate is ALWAYS evaluated. A missing ``now`` is replaced
    with the current timezone-aware time; it never disables the gate. An
    owner-selected timestamp is wired from the staged release plan.
    """
    now = now or datetime.now(timezone.utc)
    readiness = run_preflight(
        from_quarter, from_week, to_quarter, to_week, client=client, today=today,
    )
    if not readiness["ready"]:
        raise RolloverBlocked("Friday rollover is blocked: " + "; ".join(readiness["blockers"]))
    manifest = _attach_release_publication(readiness["manifest"], to_quarter, to_week)
    return execute(
        from_quarter, from_week, to_quarter, to_week, client=client,
        owner_confirmation=owner_confirmation, today=today, now=now,
        manifest=manifest, partial=False,
    )


def publish_approved_courses_only(
    from_quarter: int, from_week: int, to_quarter: int, to_week: int, *,
    client: DeployClient, owner_confirmation: str, today: date | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Use the same engine for the explicit mixed-week exception."""
    now = now or datetime.now(timezone.utc)
    if (owner_confirmation or "").strip().upper() != "PUBLISH APPROVED COURSES":
        raise RolloverBlocked(
            "partial publish confirmation missing (must be exactly 'PUBLISH APPROVED COURSES')"
        )
    source = rollover_manifest.build_rollover_manifest(
        from_quarter, from_week, to_quarter, to_week, today=today,
    )
    source = _attach_release_publication(source, to_quarter, to_week)
    approved = {c["subject"] for c in source.get("academic_courses", []) if c.get("approved")}
    include_homeroom = bool((source.get("homeroom") or {}).get("approved"))
    if not approved and not include_homeroom:
        raise RolloverBlocked("no approved course package is available")
    plan = copy.deepcopy(source)
    plan["academic_courses"] = [c for c in plan.get("academic_courses", []) if c["subject"] in approved]
    plan["weekly_announcements"] = [a for a in plan.get("weekly_announcements", []) if a["subject"] in approved]
    plan["assignments"] = [a for a in plan.get("assignments", []) if a.get("course") in approved]
    plan["assessment_reminders"] = [a for a in plan.get("assessment_reminders", []) if a.get("subject") in approved]
    plan["homeroom"] = plan.get("homeroom") if include_homeroom else None
    report = execute(
        from_quarter, from_week, to_quarter, to_week, client=client,
        owner_confirmation=f"ROLLOVER {plan['to_week']}", today=today, now=now,
        manifest=plan, partial=True,
    )
    report["published_courses"] = sorted(approved | ({"homeroom"} if include_homeroom else set()))
    return report


def publish_now(
    from_quarter: int, from_week: int, to_quarter: int, to_week: int, *,
    client: DeployClient, courses: list[str], owner_confirmation: str,
    now: datetime | None = None, today: date | None = None,
) -> dict[str, Any]:
    """Publish a selected approved course package using the rollover executor."""
    from zoneinfo import ZoneInfo

    from scripts.instructional_weeks import week_range
    from scripts.canvas_llm_intake import week_resolution as wr

    plan = rollover_manifest.build_rollover_manifest(
        from_quarter, from_week, to_quarter, to_week, today=today,
    )
    target = wr.find_week(to_quarter, to_week) or {}
    bounds = week_range(target)
    if bounds is None:
        raise RolloverBlocked("target week dates are unavailable")
    start_day = bounds[0]
    local_now = (now or datetime.now(ZoneInfo(schedule.NEW_YORK))).astimezone(ZoneInfo(schedule.NEW_YORK))
    deadline = datetime.fromisoformat(
        schedule.friday_rollover_scheduled_at(start_day.isoformat()).replace("Z", "+00:00")
    ).astimezone(ZoneInfo(schedule.NEW_YORK))
    early = local_now < deadline
    after_start = local_now.date() >= start_day
    selected = {str(course).strip().lower() for course in courses}
    allowed = {item["subject"] for item in plan["academic_courses"]} | {"homeroom"}
    if selected == {"all"}:
        selected = set(allowed)
    if not selected or not selected <= allowed:
        raise RolloverBlocked("select one or more active courses, or ALL")
    phrase_courses = "ALL" if selected == allowed else ",".join(sorted(selected))
    expected = f"PUBLISH NOW {plan['to_week']} {phrase_courses}".upper()
    if (owner_confirmation or "").strip().upper() != expected:
        raise RolloverBlocked(f"type exactly: {expected}")

    selected_academic = [c for c in plan["academic_courses"] if c["subject"] in selected]
    unapproved = [c["label"] for c in selected_academic if not c["approved"]]
    if "homeroom" in selected and not plan["homeroom"].get("approved"):
        unapproved.append("Homeroom newsletter")
    if unapproved:
        raise RolloverBlocked("these selected packages still need approval: " + ", ".join(unapproved))

    scoped = copy.deepcopy(plan)
    scoped["academic_courses"] = selected_academic
    scoped["assignments"] = [a for a in plan["assignments"] if a.get("course") in selected]
    scoped["assessment_reminders"] = [a for a in plan["assessment_reminders"] if a.get("subject") in selected]
    scoped["weekly_announcements"] = [a for a in plan["weekly_announcements"] if a.get("subject") in selected]
    if early:
        scoped["weekly_announcements"] = []
        scoped["homeroom"] = plan["homeroom"] if "homeroom" in selected else None
    else:
        scoped["homeroom"] = plan["homeroom"] if "homeroom" in selected else None
        for announcement in scoped["weekly_announcements"]:
            announcement["delayed_post_at"] = None
            announcement["schedule_state"] = "IMMEDIATE_CONFIRMED"
            announcement["scheduled"] = False

    readiness = run_preflight(
        from_quarter, from_week, to_quarter, to_week, client=client, today=today,
        manifest_override=scoped,
    )
    if readiness["blockers"]:
        raise RolloverBlocked("publish now preflight blocked: " + "; ".join(readiness["blockers"]))
    if early:
        report = execute(
            from_quarter, from_week, to_quarter, to_week, client=client,
            owner_confirmation=f"ROLLOVER {plan['to_week']}", today=today,
            manifest=scoped, partial=True, early_content_only=True,
        )
    else:
        is_all = selected == allowed
        report = execute(
            from_quarter, from_week, to_quarter, to_week, client=client,
            owner_confirmation=f"ROLLOVER {plan['to_week']}", today=today,
            manifest=scoped, partial=not is_all,
        )
    report["publish_now_mode"] = "EARLY" if early else ("AFTER_MONDAY_START" if after_start else "LATE")
    report["warning"] = (
        "The instructional week has already started; families may already have seen other materials."
        if after_start else report.get("warning")
    )
    report["published_courses"] = sorted(selected)
    return report


def _finish(to_quarter, to_week, report, state, counts) -> dict[str, Any]:
    report["finished_at"] = _now()
    report["lifecycle"] = state
    report["verb_totals"] = counts
    report["recovery"] = [
        "Inspect the failed object's exact Canvas state.",
        "Rerun the rollover — idempotent rerun skips already-completed actions.",
    ]
    ledger.write_rollover_ledger(to_quarter, to_week, report)
    return report


# --------------------------------------------------------------------------- #
# Status
# --------------------------------------------------------------------------- #

def status(
    from_quarter: int,
    from_week: int,
    to_quarter: int,
    to_week: int,
    *,
    today: date | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Deterministic FRIDAY ROLLOVER status for Chief of Staff / UI."""
    now = now or datetime.now(timezone.utc)
    readiness = build_readiness(from_quarter, from_week, to_quarter, to_week, today=today)
    plan = readiness["manifest"]
    blockers = list(readiness["blockers"])

    # A verified publication is terminal: an expired historical window must
    # not create a new owner-selection blocker for work already completed.
    existing = ledger.load_rollover_ledger(to_quarter, to_week)
    ledger_state = existing.get("lifecycle") if existing else None
    published = deploy_ledger.load_published_verified(to_quarter, to_week)
    already_published = (
        ledger_state == schedule.PUBLISHED_VERIFIED
        and isinstance(published, dict)
        and published.get("status") == "PUBLISHED_VERIFIED"
        and (
            not published.get("source_hash")
            or not (existing or {}).get("source_hash")
            or published.get("source_hash") == existing.get("source_hash")
        )
    )

    # For unpublished work, a missed Friday 4 PM window still requires an
    # explicit future owner-selected timestamp.
    publication_required = False
    canonical_scheduled_at = plan.get("scheduled_at", "")
    if not already_published:
        try:
            from scripts.instructional_weeks import week_range
            from scripts.canvas_llm_intake import week_resolution as _wr
            bounds = week_range(_wr.find_week(to_quarter, to_week) or {})
            if bounds is not None:
                resolved = schedule.resolve_publication_time(
                    bounds[0].isoformat(), now=now
                )
                publication_required = bool(resolved["requires_owner_time"])
                canonical_scheduled_at = resolved["canonical_scheduled_at"]
                if publication_required:
                    blockers.append(
                        "Owner-selected publication time required: the canonical Friday 4:00 PM "
                        "America/New_York window has passed."
                    )
        except (ValueError, RuntimeError):
            publication_required = False
    state = schedule.classify_state(
        scheduled_at=plan["scheduled_at"],
        now=now,
        ready=readiness["ready"],
        needs_owen=readiness["needs_owen"],
        blockers=blockers,
        ledger_state=ledger_state,
        preparing=(not readiness["ready"] and not readiness["needs_owen"] and not blockers),
    )
    return {
        "from_week": plan["from_week"],
        "to_week": plan["to_week"],
        "scheduled_at": plan["scheduled_at"],
        "canonical_scheduled_at": canonical_scheduled_at,
        "publication_time_required": publication_required,
        "timezone": plan["timezone"],
        "status": state,
        "ready": readiness["ready"],
        "needs_owen": readiness["needs_owen"] or publication_required,
        "blockers": blockers,
        "academic_courses": [
            {"subject": c["subject"], "course_id": c["course_id"]}
            for c in plan["academic_courses"]
        ],
        "homeroom_course_id": plan["homeroom"]["course_id"],
        "weekly_announcement_count": len(plan["weekly_announcements"]),
    }


def command_self_test() -> int:
    import tempfile
    from scripts.canvas_llm_deploy.ledger import DEPLOY_ROOT
    from scripts.canvas_llm_intake.manifest import staging_dir
    orig_deploy = DEPLOY_ROOT
    orig_staging = staging_dir
    with tempfile.TemporaryDirectory() as tmp:
        from pathlib import Path
        from scripts.canvas_llm_deploy import ledger as deploy_ledger
        import scripts.canvas_llm_intake.manifest as imf_mod
        deploy_ledger.DEPLOY_ROOT = Path(tmp) / "deployments"
        imf_mod.staging_dir = lambda q, w: Path(tmp) / "intake" / f"q{q}w{w}"
        try:
            # Readiness gate is pure + deterministic.
            r = build_readiness(2, 2, 2, 3)
            assert isinstance(r["ready"], bool)
            assert "scheduled_at" in r["manifest"]
            s = status(2, 2, 2, 3)
            assert s["from_week"] == "Q2W2" and s["to_week"] == "Q2W3"
            assert s["status"] in schedule.ROLLOVER_STATES
            # Confirmation gate requires the exact ROLLOVER phrase.
            try:
                execute(2, 2, 2, 3, client=None, owner_confirmation="DEPLOY Q2W3")
                raise AssertionError("expected blocked")
            except RolloverBlocked:
                pass
        finally:
            deploy_ledger.DEPLOY_ROOT = orig_deploy
            imf_mod.staging_dir = orig_staging
    print("PASS canvas-rollover coordinator self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
