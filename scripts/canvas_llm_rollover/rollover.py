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
                matches = deploy_plan._sha(current.get("body") or "") == course.get("to_page_hash")
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
        # Rolling-newsletter HTML approval binds to the exact page id: fail if
        # the live-resolved target no longer matches the approved page id.
        if (h.get("mode") == "rolling_newsletter_html"
                and h.get("to_page_id") is not None
                and str(hres["page_id"]) != str(h.get("to_page_id"))):
            blockers.append("homeroom: rolling page id changed (approved target mismatch)")
        if hres["page_id"] is not None:
            try:
                from . import homeroom as homeroom_mod
                current = client.get_page(h["course_id"], h["to_page_slug"])
                matches = homeroom_mod._body_hash(current.get("body") or "") == h.get("proposed_content_hash")
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
        exact = next((item for item in assignments_by_course[cid]
                      if (item.get("name") or item.get("title")) == assignment.get("title")
                      and str(item.get("due_at") or "")[:10] == str(assignment.get("due_utc") or "")[:10]), None)
        assignment["classification"] = "EXACT_MATCH" if exact else "NEW"
        assignment["action"] = "SKIP" if exact else "CREATE"
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

def execute(
    from_quarter: int,
    from_week: int,
    to_quarter: int,
    to_week: int,
    *,
    client: DeployClient,
    owner_confirmation: str,
    today: date | None = None,
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
    if existing and existing.get("lifecycle") == schedule.PUBLISHED_VERIFIED:
        return {"lifecycle": schedule.PUBLISHED_VERIFIED, "already_complete": True}

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
            if deploy_plan._sha(current.get("body") or "") != course.get("to_page_hash"):
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
        page_ok = deploy_plan._sha(page_readback.get("body") or "") == course.get("to_page_hash")
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

    # ---- D. Approved assignments ----------------------------------------
    for a in manifest.get("assignments", []):
        title = a["title"]
        try:
            exact = next((item for item in client.list_assignments(a["course_id"])
                          if (item.get("name") or item.get("title")) == title
                          and str(item.get("due_at") or "")[:10] == str(a.get("due_utc") or "")[:10]), None)
            counts["GET"] += 1
            if exact:
                created = exact
                disposition = "ALREADY_EXISTS"
            else:
                created = client.create_assignment(
                    a["course_id"], title=title, description="",
                    assignment_group=a["assignment_group"], points=a["points_possible"],
                    grading_type=a["grading_type"],
                    submission_type=(a.get("submission_types") or ["on_paper"])[0],
                    due_at=a.get("due_utc") or "",
                    counts_toward_final_grade=not a.get("omit_from_final_grade", False),
                    published=True,
                )
                counts["POST"] += 1
                disposition = "PUBLISHED_VERIFIED"
            readback = client.get_assignment(a["course_id"], str(created.get("id")))
            counts["GET"] += 1
            ok = ((readback.get("name") or "") == title
                  and str(readback.get("due_at") or "")[:10] == str(a.get("due_utc") or "")[:10])
        except Exception as exc:  # noqa: BLE001
            report["failures"].append(f"assignment {title!r}: write failed: {type(exc).__name__}")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
        report["assignments"].append({
            "subject": a.get("course"), "course_id": a["course_id"], "title": title,
            "assignment_id": created.get("id"), "disposition": disposition if ok else "FAILED",
            "verified": ok,
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
            in_feed = any((x.get("title") or "") == a["title"] for x in client.list_active_announcements())
            counts["GET"] += 1
        except Exception:  # noqa: BLE001
            in_feed = False
        from scripts.canvas_llm_intake import scheduling as sched
        state = sched.classify_announcement(
            delayed_post_at=a.get("delayed_post_at"), posted_at=created.get("posted_at"),
            published=created.get("published"), in_active_feed=in_feed)
        content_ok = (
            announcement_readback.get("title") == a["title"]
            and announcement_readback.get("message", "") == a["message"]
        )
        ok = content_ok and state in (sched.HELD_SCHEDULED, sched.POSTED)
        report["weekly_announcements"].append({
            "subject": a["subject"], "title": a["title"], "announcement_id": tid,
            "message_hash": hashlib.sha256(str(a.get("message", "")).encode("utf-8")).hexdigest(),
            "delayed_post_at": a.get("delayed_post_at"), "state": state,
            "disposition": "PUBLISHED_VERIFIED" if ok else "FAILED", "verified": ok,
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
        try:
            exact = next((item for item in client.list_announcements(a["course_id"])
                          if item.get("title") == title and item.get("message") == a.get("message", "")), None)
            counts["GET"] += 1
            if exact:
                created = exact
                disposition = "ALREADY_EXISTS"
            else:
                created = client.create_announcement(
                    a["course_id"], title=title, message=a.get("message", ""),
                    published=True, delayed_post_at=None,
                )
                counts["POST"] += 1
                disposition = "PUBLISHED_VERIFIED"
            readback = client.get_announcement(a["course_id"], str(created.get("id")))
            counts["GET"] += 1
            ok = readback.get("title") == title and readback.get("message", "") == a.get("message", "")
        except Exception as exc:  # noqa: BLE001
            report["failures"].append(f"reminder {title!r}: write failed: {type(exc).__name__}")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
        report["assessment_reminders"].append({
            "subject": a.get("subject"), "course_id": a["course_id"], "title": title,
            "announcement_id": created.get("id"), "disposition": disposition if ok else "FAILED",
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
    report["lifecycle"] = schedule.PUBLISHED_VERIFIED
    ledger.write_rollover_ledger(to_quarter, to_week, report)
    deploy_ledger.finalize_published_verified(
        to_quarter, to_week,
        {
            "school_year": report["school_year"], "quarter": to_quarter, "week": to_week,
            "week_code": report["to_week"], "verified_at": report["finished_at"],
            "status": "PUBLISHED_VERIFIED", "publisher": "FRIDAY_ROLLOVER",
            "pages": report["pages"], "assignments": report["assignments"],
            "weekly_announcements": report["weekly_announcements"],
            "assessment_reminders": report["assessment_reminders"],
            "homeroom": report["homeroom"], "communication": report["communication"],
        },
    )
    _record_publish_event(to_quarter, to_week, report, partial=False)
    return report


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
    proposed_hash = h.get("proposed_content_hash")
    # Production body: the exact approved rolling-newsletter HTML when an HTML
    # approval exists; otherwise the JSON proposal renderer (planning fallback).
    if h.get("mode") == "rolling_newsletter_html":
        body = h.get("body") or ""
        if str(hres["page_id"]) != str(h.get("to_page_id")):
            report["failures"].append("homeroom: rolling page id changed (approved target mismatch)")
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
        cur_hash = homeroom_mod._body_hash(cur.get("body") or "")
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
        and homeroom_mod._body_hash(hread.get("body") or "") == proposed_hash
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


def publish_weekly_package(
    from_quarter: int, from_week: int, to_quarter: int, to_week: int, *,
    client: DeployClient, owner_confirmation: str, today: date | None = None,
) -> dict[str, Any]:
    """Publish the all-or-nothing canonical package through the rollover engine."""
    readiness = run_preflight(
        from_quarter, from_week, to_quarter, to_week, client=client, today=today,
    )
    if not readiness["ready"]:
        raise RolloverBlocked("Friday rollover is blocked: " + "; ".join(readiness["blockers"]))
    return execute(
        from_quarter, from_week, to_quarter, to_week, client=client,
        owner_confirmation=owner_confirmation, today=today,
        manifest=readiness["manifest"], partial=False,
    )


def publish_approved_courses_only(
    from_quarter: int, from_week: int, to_quarter: int, to_week: int, *,
    client: DeployClient, owner_confirmation: str, today: date | None = None,
) -> dict[str, Any]:
    """Use the same engine for the explicit mixed-week exception."""
    if (owner_confirmation or "").strip().upper() != "PUBLISH APPROVED COURSES":
        raise RolloverBlocked(
            "partial publish confirmation missing (must be exactly 'PUBLISH APPROVED COURSES')"
        )
    source = rollover_manifest.build_rollover_manifest(
        from_quarter, from_week, to_quarter, to_week, today=today,
    )
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
        owner_confirmation=f"ROLLOVER {plan['to_week']}", today=today,
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
    readiness = build_readiness(from_quarter, from_week, to_quarter, to_week, today=today)
    plan = readiness["manifest"]
    existing = ledger.load_rollover_ledger(to_quarter, to_week)
    ledger_state = existing.get("lifecycle") if existing else None
    state = schedule.classify_state(
        scheduled_at=plan["scheduled_at"],
        now=now,
        ready=readiness["ready"],
        needs_owen=readiness["needs_owen"],
        blockers=readiness["blockers"],
        ledger_state=ledger_state,
        preparing=(not readiness["ready"] and not readiness["needs_owen"] and not readiness["blockers"]),
    )
    return {
        "from_week": plan["from_week"],
        "to_week": plan["to_week"],
        "scheduled_at": plan["scheduled_at"],
        "timezone": plan["timezone"],
        "status": state,
        "ready": readiness["ready"],
        "needs_owen": readiness["needs_owen"],
        "blockers": readiness["blockers"],
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
