"""GET-only deployment preflight (no writes) + short-lived preflight records.

``run_preflight`` validates the READY_TO_PUBLISH gate, resolves live objects via
GET-only lookups, classifies duplicates, and produces an exact write plan plus a
short-lived preflight record. Deployment may only execute against that exact
preflight record.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from . import ledger
from . import plan as plan_mod
from .client import DeployClient

PREFLIGHT_TTL_MINUTES = 15


def _norm_name(name: str) -> str:
    import re
    s = (name or "").strip().lower()
    s = s.replace("\u2014", "-").replace("\u2013", "-").replace("\u2019", "'")
    s = re.sub(r"\s+", " ", s)
    return s


def _strip_retake_marker(name: str) -> str:
    import re
    return re.sub(r"\s*\((retake|copy|revised|v\d+|redo)\)\s*$", "", name)


def _canvas_owned_message(message: str) -> str:
    """Remove Canvas-injected global assets from an announcement readback."""
    text = re.sub(
        r'<link\b[^>]*\bhref=["\'][^"\']*canvas_global_app\.css[^"\']*["\'][^>]*>\s*',
        "", message or "", flags=re.IGNORECASE,
    )
    text = re.sub(
        r'\s*<script\b[^>]*\bsrc=["\'][^"\']*canvas_global_app\.js[^"\']*["\'][^>]*>\s*</script>',
        "", text, flags=re.IGNORECASE,
    )
    return text


def classify_assignment(proposed_title: str, existing_names: list[str]) -> str:
    """Classify a proposed assignment against existing live assignment names.

    EXACT_MATCH — identical normalized name (safe idempotent skip)
    AMBIGUOUS   — same base title modulo a trailing retake/copy/revised marker
                  (block before write)
    NEW         — no existing equivalent (create)
    """
    n = _norm_name(proposed_title)
    existing = {_norm_name(e) for e in existing_names if (e or "").strip()}
    if n in existing:
        return "EXACT_MATCH"
    base = _strip_retake_marker(n)
    for e in existing:
        if _strip_retake_marker(e) == base:
            return "AMBIGUOUS"
    return "NEW"


# Weekly-announcement identity is WEEK-aware (unlike assignments). A generic
# recurring title such as "Math Canvas Weekly Update" is used every week, so
# title equality alone must NEVER be treated as a duplicate across weeks.
WEEKLY_ANNOUNCE_STATES = ("EXACT_MATCH", "PRIOR_WEEK_SAME_TITLE", "BODY_CHANGED_SAME_WEEK", "AMBIGUOUS", "NEW")

# Assessment-reminder reconciliation state: a separately scheduled, verified
# Canvas assessment topic already satisfies the reminder, so the rollover must
# not create a duplicate.
REMINDER_ALREADY_SCHEDULED = "ALREADY_SCHEDULED_VERIFIED"


def classify_weekly_announcement(proposed: dict[str, Any], live: list[dict[str, Any]]) -> str:
    """Classify a proposed weekly update against live same-title announcements.

    Identity is (course + title + week + body/agenda), where the scheduled
    ``delayed_post_at`` deterministically identifies the target week (prior
    Friday 4 PM ET of each week). A same generic title on a DIFFERENT week is
    ``PRIOR_WEEK_SAME_TITLE`` — not a duplicate — and must not suppress the
    current week's post.

    Returns one of WEEKLY_ANNOUNCE_STATES.
    """
    title = _norm_name(proposed.get("title", ""))
    proposed_week = proposed.get("week_code") or ""
    proposed_delayed = proposed.get("delayed_post_at")
    proposed_course = proposed.get("course_id")
    # Compare embedded agenda fragments apples-to-apples: the proposed message's
    # kl_wrapper_3-onward fragment vs the live message's same fragment (both
    # Canvas-normalized). The page agenda hash is a different fragment (the page
    # body alone), so only use it as a fallback when no message is present.
    proposed_agenda = (_embedded_agenda_hash(proposed.get("message") or "")
                       or proposed.get("agenda_hash") or proposed.get("page_agenda_hash") or "")

    same_week: list[dict[str, Any]] = []
    other_week = False
    for a in live:
        if proposed_course is not None and a.get("course_id") not in (None, proposed_course):
            continue
        if _norm_name(a.get("title") or "") != title:
            continue
        live_delayed = a.get("delayed_post_at")
        live_week = a.get("week_code") or ""
        matched_week = bool(proposed_week and live_week and proposed_week == live_week)
        matched_time = bool(proposed_delayed and live_delayed and proposed_delayed == live_delayed)
        if matched_week or matched_time:
            same_week.append(a)
        else:
            other_week = True
    if len(same_week) > 1:
        return "AMBIGUOUS"
    if len(same_week) == 1:
        live_agenda = (
            same_week[0].get("agenda_hash")
            or same_week[0].get("page_agenda_hash")
            or _embedded_agenda_hash(same_week[0].get("message") or "")
        )
        if proposed_agenda and live_agenda and proposed_agenda == live_agenda:
            return "EXACT_MATCH"
        return "BODY_CHANGED_SAME_WEEK"
    if other_week:
        return "PRIOR_WEEK_SAME_TITLE"
    return "NEW"


def _reminder_identity_tokens(reminder: dict[str, Any]) -> list[str]:
    """Derive assessment-identity tokens from a drafted reminder.

    Reconciliation is by course + assessment type + assessment number(s), which
    are week-scoped. Canvas topic IDs and exact reminder titles are never
    required, so separately scheduled assessment topics are recognized without
    hardcoding.
    """
    rtype = reminder.get("type", "")
    title = reminder.get("title") or ""
    message = reminder.get("message") or reminder.get("body") or ""
    haystack = f"{title} {message}"
    tokens: list[str] = []
    if rtype == "math_assessment":
        for m in re.finditer(r"(Written|Fact)\s+Assessment\s*(\d+)", haystack, re.IGNORECASE):
            tokens.append(f"{m.group(1).title()} Assessment {m.group(2)}")
    elif rtype == "spelling":
        m = re.search(r"Spelling\s+Test\s*(\d+)", haystack, re.IGNORECASE)
        if m:
            tokens.append(f"Spelling Test {m.group(1)}")
    seen: list[str] = []
    for t in tokens:
        if t not in seen:
            seen.append(t)
    return seen


def classify_assessment_reminder(reminder: dict[str, Any], live: list[dict[str, Any]]) -> str:
    """Reconcile a drafted assessment reminder against live announcements.

    Returns:
      EXACT_MATCH              — a live announcement has the identical title+message.
      ALREADY_SCHEDULED_VERIFIED — a live announcement already covers the same
                                   assessment identity (type + numbers), even when
                                   the reminder's own title/body differ.
      NEW                      — no existing announcement satisfies the reminder.
    """
    title = reminder.get("title") or ""
    message = _canvas_owned_message(reminder.get("message") or reminder.get("body") or "")
    proposed_course = reminder.get("course_id")
    proposed_role = _notice_role(reminder)
    scoped = [
        item for item in live
        if proposed_course is None or item.get("course_id") in (None, proposed_course)
    ]
    exact = [
        item for item in scoped
        if (item.get("title") or "") == title
        and _canvas_owned_message(item.get("message") or "") == message
    ]
    if len(exact) > 1:
        return "AMBIGUOUS"
    if len(exact) == 1:
        return "EXACT_MATCH"
    tokens = _reminder_identity_tokens(reminder)
    if tokens:
        covered = []
        for item in scoped:
            live_role = _notice_role(item)
            if proposed_role and live_role and proposed_role != live_role:
                continue
            live_title = _norm_name(item.get("title") or "")
            if all(tok.lower() in live_title for tok in tokens):
                covered.append(item)
        if len(covered) > 1:
            return "AMBIGUOUS"
        if len(covered) == 1:
            return REMINDER_ALREADY_SCHEDULED
    return "NEW"


def _notice_role(item: dict[str, Any]) -> str | None:
    """Separate a first notice from a reminder. Title similarity is not enough."""
    role = str(item.get("notice_role") or item.get("notice_kind") or "").lower()
    if role in {"reminder", "second"}:
        return "reminder"
    if role in {"first", "first_notice"}:
        return "first"
    title = (item.get("title") or "").lower()
    if title.startswith("reminder") or " reminder " in f" {title} ":
        return "reminder"
    return None


def _embedded_agenda_hash(message: str) -> str:
    """Hash the embedded weekly-agenda HTML in an announcement message.

    The weekly-update message embeds the full page body, which begins with
    ``<div id="kl_wrapper_3" ...>``. We hash from that opening ``<div`` onward
    (ignoring the greeting/transition and the Canvas global wrapper) so it can be
    compared to the proposed page agenda hash (which hashes the same fragment).
    """
    import re as _re
    if not message:
        return ""
    # Canvas prepends canvas_global_app.css and appends canvas_global_app.js to
    # announcement messages on write; strip them so the embedded fragment hashes
    # identically to the authored message.
    message = _re.sub(
        r'<link\b[^>]*\bhref=["\'][^"\']*canvas_global_app\.css[^"\']*["\'][^>]*>\s*',
        '', message, flags=_re.IGNORECASE,
    )
    message = _re.sub(
        r'\s*<script\b[^>]*\bsrc=["\'][^"\']*canvas_global_app\.js[^"\']*["\'][^>]*>\s*</script>',
        '', message, flags=_re.IGNORECASE,
    )
    m = _re.search(r'id="kl_wrapper_3"', message)
    if not m:
        return ""
    # Walk back to the opening "<div" of the kl_wrapper_3 element.
    start = message.rfind("<div", 0, m.start())
    if start < 0:
        start = m.start()
    return _sha(message[start:])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_preflight(quarter: int, week: int, client: DeployClient | None = None) -> dict[str, Any]:
    """Build + validate the deployment preflight (GET-only; no writes).

    ``client=None`` produces a plan-only (dry-run) preflight: it evaluates the
    READY_TO_PUBLISH gate and emits the exact write plan, but performs no Canvas
    GETs and marks live context unavailable. ``client`` performs GET-only live
    object resolution (course/page/group/duplicate).
    """
    import json as _json

    plan = plan_mod.build_plan(quarter, week)
    blockers: list[str] = []
    warnings: list[str] = []

    # ---- Hard gate: lifecycle must be READY_TO_PUBLISH -------------------
    if not plan.get("ready_to_publish"):
        blockers.append("week is not READY_TO_PUBLISH")
        blockers.extend(plan.get("publish_blockers", []))
    elif plan.get("status") != "READY_TO_PUBLISH":
        blockers.append(f"lifecycle is {plan.get('status')!r}, not READY_TO_PUBLISH")

    live: dict[str, Any] = {"courses": {}, "pages": {}, "assignment_groups": {},
                            "assignments": {}, "announcements": {}}

    if client is None:
        warnings.append("LIVE CANVAS CONTEXT UNAVAILABLE — dry-run (no Canvas GET performed)")

    # ---- Course identity (GET-only) --------------------------------------
    course_ids: set[int] = set()
    for p in plan.get("pages", []):
        course_ids.add(p["course_id"])
    for a in plan.get("assignments", []):
        course_ids.add(a["course_id"])
    for a in plan.get("weekly_announcements", []) + plan.get("assessment_reminders", []):
        course_ids.add(a["course_id"])

    if client is not None:
        for cid in sorted(course_ids):
            if cid is None:
                blockers.append("course id missing for a touched artifact")
                continue
            try:
                course = client.get_course(int(cid))
            except Exception as exc:  # noqa: BLE001 - fail closed
                blockers.append(f"course {cid} lookup failed: {type(exc).__name__}")
                continue
            live["courses"][str(cid)] = {
                "id": course.get("id"),
                "name": course.get("name"),
                "workflow_state": course.get("workflow_state"),
            }

    # ---- Page identity (unique match; never create) ----------------------
    for p in plan.get("pages", []):
        cid = p["course_id"]
        slug = p.get("slug", "")
        if not slug:
            blockers.append(f"{p['subject']}: page slug missing")
            continue
        if client is None:
            continue
        try:
            found = client.find_page(int(cid), slug)
        except Exception as exc:  # noqa: BLE001
            blockers.append(f"{p['subject']}: page lookup failed: {type(exc).__name__}")
            continue
        if found is None:
            blockers.append(f"{p['subject']}: weekly page missing (cannot create normal weekly page)")
            continue
        pid = found.get("page_id") or found.get("id")
        live["pages"][p["subject"]] = {
            "page_id": pid,
            "url": found.get("url"),
            "title": found.get("title"),
        }
        p["live_page_id"] = pid

        # Slug identity classification: a slug change (or a legacy slug that
        # redirects to the same page_id) is INFO/WARN, NOT a blocker. Only a
        # genuine identity conflict (different page_id) is fatal — and that is
        # already guarded above via the resolved page_id being captured for
        # readback. Record the classification for observability.
        from . import page_identity as pidentity
        classification = pidentity.classify_resolved_page(slug, found)
        p["slug_classification"] = classification
        if pidentity.slug_change_is_warning(classification):
            warnings.append(f"{p['subject']}: canonical slug changed (page_id {pid} stable) — {classification}")
        elif pidentity.slug_change_is_fatal(classification):
            blockers.append(f"{p['subject']}: page identity conflict — {classification}")

    # ---- Assignment group routing (fail closed on missing group) --------
    groups_cache: dict[int, list[str]] = {}
    for a in plan.get("assignments", []):
        cid = a["course_id"]
        if client is None:
            continue
        if cid not in groups_cache:
            try:
                groups_cache[cid] = [g.get("name") for g in client.list_assignment_groups(int(cid))]
            except Exception as exc:  # noqa: BLE001
                blockers.append(f"assignment group lookup failed for course {cid}: {type(exc).__name__}")
                groups_cache[cid] = []
        group = a.get("assignment_group")
        if group not in groups_cache[cid]:
            blockers.append(f"assignment {a.get('title')!r}: group {group!r} missing (routing fail-closed)")
            continue
        live["assignment_groups"].setdefault(str(cid), {})[group] = "FOUND"

    # ---- Assignment duplicate classification -----------------------------
    existing_cache: dict[int, list[str]] = {}
    for a in plan.get("assignments", []):
        cid = a["course_id"]
        if client is None:
            continue
        if cid not in existing_cache:
            try:
                existing_cache[cid] = [x.get("name") or "" for x in client.list_assignments(int(cid))]
            except Exception as exc:  # noqa: BLE001
                blockers.append(f"assignment list failed for course {cid}: {type(exc).__name__}")
                existing_cache[cid] = []
        cls = classify_assignment(a.get("title", ""), existing_cache[cid])
        a["duplicate_classification"] = cls
        live["assignments"].setdefault(a["title"], cls)
        if cls == "AMBIGUOUS":
            blockers.append(f"assignment {a.get('title')!r}: ambiguous near-duplicate exists")

    # ---- Announcement duplicate identity (week-aware idempotency) ---------
    ann_cache: dict[int, list[dict[str, Any]]] = {}
    for a in plan.get("weekly_announcements", []) + plan.get("assessment_reminders", []):
        cid = a["course_id"]
        if client is None:
            continue
        if cid not in ann_cache:
            try:
                ann_cache[cid] = [x for x in client.list_announcements(int(cid))]
            except Exception:  # noqa: BLE001 - listing is advisory
                ann_cache[cid] = []
        if a.get("artifact_type") == "weekly_update":
            # Weekly updates are week-aware: recurring generic titles are NOT
            # cross-week duplicates.
            cls = classify_weekly_announcement(a, ann_cache[cid])
        else:
            # Assessment reminders carry week-specific titles (dates/numbers).
            cls = classify_assignment(a.get("title", ""),
                                      [x.get("title") or "" for x in ann_cache[cid]])
        a["duplicate_classification"] = cls
        live["announcements"].setdefault(a.get("title"), cls)
        if cls == "AMBIGUOUS":
            blockers.append(f"announcement {a.get('title')!r}: ambiguous near-duplicate exists")
        if a.get("duplicate_status") == "AMBIGUOUS":
            blockers.append(f"announcement {a.get('title')!r}: announcement identity is ambiguous")
        if a.get("hash_consistent") is False:
            blockers.append(f"announcement {a.get('title')!r}: agenda hash differs from the page")
        if a.get("action") == "BLOCKED" or a.get("schedule_state") in ("OWNER_TIME_REQUIRED", "BLOCKED"):
            blockers.append(
                f"announcement {a.get('title')!r}: {a.get('block_reason') or a.get('schedule_state') or 'blocked'}"
            )
        if a.get("content_status") not in (None, "READY"):
            blockers.append(f"announcement {a.get('title')!r}: resource or content is unverified")

    ready = len(blockers) == 0

    preflight_id = _sha(_json.dumps(plan, sort_keys=True, ensure_ascii=False) + _now())[:16]
    record = {
        "preflight_id": preflight_id,
        "created_at": _now(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=PREFLIGHT_TTL_MINUTES)).isoformat(),
        "ttl_minutes": PREFLIGHT_TTL_MINUTES,
        "quarter": quarter,
        "week": week,
        "week_code": plan.get("week_code"),
        "source_hash": plan.get("source_hash"),
        "approval_snapshot_hash": plan.get("approval_snapshot_hash"),
        "plan": plan,
        "live": live,
        "warnings": warnings,
        "blockers": blockers,
        "ready": ready,
        "canvas_writes": 0,
    }
    ledger.write_preflight(quarter, week, record)
    return record


def command_self_test() -> int:
    from .client import FakeDeployClient
    import tempfile

    # classify_assignment unit checks.
    assert classify_assignment("SM5: Lesson 39 Homework", ["SM5: Lesson 39 Homework"]) == "EXACT_MATCH"
    assert classify_assignment("SM5: Lesson 39 Homework", ["SM5: Lesson 39 Homework (Retake)"]) == "AMBIGUOUS"
    assert classify_assignment("SM5: Lesson 39 Homework", ["SM5: Lesson 40 Homework"]) == "NEW"

    # Weekly-announcement same-week identity must tolerate Canvas global assets.
    css = '<link rel="stylesheet" href="https://instructure-uploads/canvas_global_app.css">'
    js = '<script src="https://instructure-uploads/canvas_global_app.js"></script>'
    agenda = '<div id="kl_wrapper_3" class="kl_wrapper">agenda</div>'
    proposed_msg = f"<p>Good afternoon,</p>{agenda}<p>Have a great weekend!</p>"
    live_msg = f"{css}{proposed_msg}{js}"
    proposed = {"title": "Math Canvas Weekly Update", "week_code": "Q2W3",
                "delayed_post_at": "2026-10-23T20:00:00Z", "message": proposed_msg}
    live = [{"title": "Math Canvas Weekly Update", "delayed_post_at": "2026-10-23T20:00:00Z",
             "message": live_msg}]
    assert classify_weekly_announcement(proposed, live) == "EXACT_MATCH"
    # A genuinely different same-week agenda is BODY_CHANGED_SAME_WEEK.
    live_diff = [{"title": "Math Canvas Weekly Update", "delayed_post_at": "2026-10-23T20:00:00Z",
                  "message": f"{css}<p>Good afternoon,</p><div id=\"kl_wrapper_3\" class=\"kl_wrapper\">CHANGED</div><p>Have a great weekend!</p>{js}"}]
    assert classify_weekly_announcement(proposed, live_diff) == "BODY_CHANGED_SAME_WEEK"

    # Assessment-reminder reconciliation (identity, not topic IDs/exact titles).
    math_reminder = {"type": "math_assessment",
                     "title": "Math Assessment Reminder — Thursday, October 29",
                     "message": "Written Assessment 7 and Fact Assessment 7 on Thursday, October 29."}
    spelling_reminder = {"type": "spelling",
                         "title": "Spelling Test 45 Reminder",
                         "message": "Spelling Test 45 this Friday, October 30."}
    live_scheduled = [
        {"title": "Written Assessment 7 and Fact Assessment 7 - Thursday, October 29", "message": "…"},
        {"title": "Spelling Test 45 - Friday, October 30", "message": "…"},
    ]
    assert classify_assessment_reminder(math_reminder, live_scheduled) == REMINDER_ALREADY_SCHEDULED
    assert classify_assessment_reminder(spelling_reminder, live_scheduled) == REMINDER_ALREADY_SCHEDULED
    # Different week's assessment must NOT satisfy (assessment number is week-scoped).
    assert classify_assessment_reminder(math_reminder,
        [{"title": "Written Assessment 6 and Fact Assessment 6 - Thursday, October 22", "message": "…"}]) == "NEW"
    assert classify_assessment_reminder(math_reminder, []) == "NEW"
    # Exact title+message still matches, even with Canvas global assets.
    assert classify_assessment_reminder(math_reminder,
        [{"title": math_reminder["title"], "message": math_reminder["message"]}]) == "EXACT_MATCH"
    assert classify_assessment_reminder(math_reminder,
        [{"title": math_reminder["title"],
          "message": f"{css}{math_reminder['message']}{js}"}]) == "EXACT_MATCH"

    # preflight against a fake client (course + page seeded).
    client = FakeDeployClient(courses={26404: {"id": 26404, "name": "Math", "workflow_state": "available"}})
    client.assignment_groups[26404] = [{"id": "60321", "name": "Homework/Class Work"},
                                       {"id": "60319", "name": "Written Assessments"},
                                       {"id": "60320", "name": "Fact Assessments"}]
    client.seed_page(26404, "q2w3-october-26-30-2026", title="Q2W3", body="<div id='kl_wrapper_3'>x</div>")

    # Route preflight to a temp ledger root.
    import scripts.canvas_llm_deploy.ledger as lg
    import scripts.canvas_llm_intake.manifest as imf
    orig_deploy = lg.DEPLOY_ROOT
    orig_staging = imf.staging_dir
    with tempfile.TemporaryDirectory() as tmp:
        from pathlib import Path
        lg.DEPLOY_ROOT = Path(tmp) / "deployments"
        imf.staging_dir = lambda q, w: Path(tmp) / "intake" / f"q{q}w{w}"
        try:
            # Preflight is GET-only: fake client write counts stay zero.
            rec = run_preflight(2, 3, client)
            assert rec["canvas_writes"] == 0
            assert client._write_counts == {"POST": 0, "PUT": 0, "PATCH": 0, "DELETE": 0, "GET": 0}
            # (Whether it is ready depends on staging; assert the record shape.)
            assert "preflight_id" in rec and "expires_at" in rec and "plan" in rec
        finally:
            lg.DEPLOY_ROOT = orig_deploy
            imf.staging_dir = orig_staging
    print("PASS canvas-deploy preflight self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
