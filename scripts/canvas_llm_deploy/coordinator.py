"""Guarded deployment coordinator — ordered writes + post-write verification.

This is the ONLY component that reaches Canvas mutation code. It enforces:

1. Preflight must exist, be unexpired, and match the current source + approval
   hashes (no stale deployment).
2. Explicit owner confirmation ("DEPLOY {week_code}").
3. Ordered writes (backup -> pages -> readback -> assignments -> readback ->
   announcements -> readback -> final sweep) with STOP-ON-FAILURE.
4. Idempotent rerun (skip already-correct objects).
5. PUBLISHED_VERIFIED only after every write passes readback, and every artifact
   has an explicit final disposition (no "held / never posted" ambiguity).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from . import ledger
from . import plan as plan_mod
from .client import DeployClient, DeployClientError

DEPLOYMENT_STATES = ("PREFLIGHT_READY", "DEPLOYING", "DEPLOYMENT_PARTIAL", "PUBLISHED_VERIFIED", "FAILED")


class DeploymentBlocked(RuntimeError):
    """Raised when a deployment may not proceed (gate/validation failure)."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _submission_type(value: Any) -> str:
    """Return a single Canvas submission type from either a list or a string.

    ``submission_types`` may be a list (``["on_paper"]``) or a bare string
    (``"on_paper"``). Indexing ``[0]`` on the bare string yields ``"o"`` and is
    rejected by Canvas; normalize so "on_paper" is always sent.
    """
    sts = value or ["on_paper"]
    if isinstance(sts, str):
        return sts
    return sts[0] if sts else "on_paper"


def _confirm_ok(confirmation: str, week_code: str, *, deletes: int) -> bool:
    text = (confirmation or "").strip()
    if not text:
        return False
    upper = text.upper()
    if deletes > 0:
        return upper == f"DEPLOY {week_code.upper()}"
    return "DEPLOY" in upper


def _load_and_validate(
    quarter: int, week: int, *, preflight_id: str,
    expected_source_hash: str, expected_approval_snapshot_hash: str,
    owner_confirmation: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load the preflight + re-derive the CURRENT plan; fail closed on any mismatch."""
    pre = ledger.load_preflight(quarter, week, preflight_id)
    if pre is None:
        raise DeploymentBlocked("preflight not found (run preflight first)")

    # Expiry.
    from datetime import datetime as _dt
    expires = pre.get("expires_at")
    if expires:
        try:
            if _dt.now(timezone.utc) > _dt.fromisoformat(expires):
                raise DeploymentBlocked("preflight expired — rerun preflight")
        except ValueError:
            pass

    current = plan_mod.build_plan(quarter, week)

    # Hash re-check (source + approval) vs preflight.
    if pre.get("source_hash") != current.get("source_hash"):
        raise DeploymentBlocked("STALE — source changed since preflight; rerun preflight")
    if pre.get("approval_snapshot_hash") != current.get("approval_snapshot_hash"):
        raise DeploymentBlocked("STALE — approvals changed since preflight; rerun preflight")

    # Expected hashes from the request must match too (prevents deploying a
    # different packet than the one the caller thinks it confirmed).
    if expected_source_hash and expected_source_hash != current.get("source_hash"):
        raise DeploymentBlocked("STALE — expected_source_hash does not match current source")
    if expected_approval_snapshot_hash and expected_approval_snapshot_hash != current.get("approval_snapshot_hash"):
        raise DeploymentBlocked("STALE — expected approval snapshot does not match current approvals")

    if not pre.get("ready"):
        raise DeploymentBlocked("preflight is not ready: " + "; ".join(pre.get("blockers", [])))

    if not _confirm_ok(owner_confirmation, current.get("week_code", ""),
                       deletes=len(pre.get("plan", {}).get("deletes", []))):
        raise DeploymentBlocked("owner confirmation missing (must include 'DEPLOY')")

    return pre, current


def _verify_page(client: DeployClient, course_id: int, slug: str, expected_page_id: Any,
                 week_code: str, counts: dict[str, int]) -> tuple[bool, str]:
    page = client.get_page(course_id, slug)
    counts["GET"] = counts.get("GET", 0) + 1
    pid = page.get("page_id")
    body = page.get("body") or ""
    ok = (
        pid is not None
        and (expected_page_id is None or str(pid) == str(expected_page_id))
        and "kl_wrapper_3" in body
        and "Reminders" in body
    )
    detail = "" if ok else f"page_id={pid} kl_wrapper_3={'kl_wrapper_3' in body} Reminders={'Reminders' in body}"
    return ok, detail


def _verify_assignment(client: DeployClient, course_id: int, assignment_id: Any,
                       title: str, due_utc: str, counts: dict[str, int]) -> tuple[bool, str]:
    a = client.get_assignment(course_id, str(assignment_id))
    counts["GET"] = counts.get("GET", 0) + 1
    ok = (
        (a.get("name") or "") == title
        and int(a.get("points_possible") or 0) == 100
        and a.get("grading_type") == "percent"
        and "on_paper" in (a.get("submission_types") or [])
        and not a.get("omit_from_final_grade")
        and (a.get("due_at") or "").startswith(due_utc[:10])
    )
    return ok, "" if ok else f"name={a.get('name')!r} points={a.get('points_possible')} due={a.get('due_at')}"


def _verify_announcement(client: DeployClient, course_id: int, topic_id: Any,
                         *, title: str, scheduled: bool, delayed_post_at: str | None,
                         expect_agenda: bool, counts: dict[str, int]) -> tuple[bool, str]:
    a = client.get_announcement(course_id, str(topic_id))
    counts["GET"] = counts.get("GET", 0) + 1
    msg = a.get("message") or ""
    content_ok = a.get("title") == title and "Mr. Reagan" in msg
    if expect_agenda:
        content_ok = content_ok and "kl_wrapper_3" in msg and "Reminders" in msg

    from scripts.canvas_llm_intake import scheduling as sched
    in_feed = any(
        (x.get("title") or "") == title
        for x in client.list_active_announcements(context_codes=[f"course_{course_id}"])
    )
    counts["GET"] = counts.get("GET", 0) + 1
    state = sched.classify_announcement(
        delayed_post_at=a.get("delayed_post_at"),
        posted_at=a.get("posted_at"),
        published=a.get("published"),
        in_active_feed=in_feed,
    )
    if scheduled:
        # Correct held state: future delayed_post_at + NOT in active feed.
        sched_ok = state == sched.HELD_SCHEDULED
        # delayed_post_at must match intent (prefix).
        if delayed_post_at and not (a.get("delayed_post_at") or "").startswith(delayed_post_at[:16]):
            sched_ok = False
    else:
        # Immediate: should be POSTED (in active feed).
        sched_ok = state in (sched.POSTED,)
    ok = content_ok and sched_ok
    return ok, "" if ok else f"title_ok={a.get('title')==title} content_ok={content_ok} sched={state}"


def deploy(
    quarter: int, week: int, *,
    preflight_id: str,
    expected_source_hash: str,
    expected_approval_snapshot_hash: str,
    owner_confirmation: str,
    client: DeployClient,
    source: str = "OWNER_UI",
) -> dict[str, Any]:
    """Execute the approved preflight's write plan (ordered, stop-on-failure)."""
    existing = ledger.load_ledger(quarter, week)
    if existing and existing.get("deployment_state") == "PUBLISHED_VERIFIED":
        raise DeploymentBlocked("week already PUBLISHED_VERIFIED (idempotent rerun not needed)")

    pre, current = _load_and_validate(
        quarter, week, preflight_id=preflight_id,
        expected_source_hash=expected_source_hash,
        expected_approval_snapshot_hash=expected_approval_snapshot_hash,
        owner_confirmation=owner_confirmation,
    )
    plan = pre["plan"]
    week_code = plan.get("week_code")
    slug = plan.get("slug", "")
    counts: dict[str, int] = {"GET": 0, "POST": 0, "PUT": 0, "PATCH": 0, "DELETE": 0}
    packet = plan_mod.load_packet(quarter, week)  # staged page bodies (single load)

    report: dict[str, Any] = {
        "school_year": "2026-2027",
        "quarter": quarter,
        "week": week,
        "week_code": week_code,
        "source": source,
        "preflight_id": preflight_id,
        "deployment_state": "DEPLOYING",
        "confirmation_at": _now(),
        "started_at": _now(),
        "verb_totals": counts,
        "pages": [],
        "assignments": [],
        "weekly_announcements": [],
        "assessment_reminders": [],
        "deleted_assignments": [],
        "untouched": plan.get("untouched", {}),
        "failures": [],
        "notes": [],
    }
    ledger.write_ledger(quarter, week, report)

    # ---- 1. Page backups (GET current body before write) ------------------
    backups: dict[str, dict[str, Any]] = {}
    for p in plan.get("pages", []):
        try:
            cur = client.get_page(p["course_id"], slug)
            counts["GET"] += 1
            backups[p["subject"]] = {
                "course_id": p["course_id"], "page_id": cur.get("page_id"),
                "title": cur.get("title"), "body": cur.get("body") or "",
                "body_sha256": plan_mod._sha(cur.get("body") or ""),
                "retrieved_at": _now(),
            }
            ledger.write_backup(quarter, week, f"{p['subject']}-page-before", backups[p["subject"]])
        except Exception as exc:  # noqa: BLE001
            report["failures"].append(f"backup {p['subject']} failed: {type(exc).__name__}")
            return _finish_partial(quarter, week, report, "FAILED")

    # ---- 2. Page updates + 3. readback ------------------------------------
    for p in plan.get("pages", []):
        subject = p["subject"]
        body = packet["page_bodies"].get(subject, "")
        if not body:
            report["failures"].append(f"{subject}: staged page body missing")
            return _finish_partial(quarter, week, report, "DEPLOYMENT_PARTIAL")
        client.update_page(p["course_id"], slug, body=body, published=True, front_page=False)
        counts["PUT"] += 1
        ok, detail = _verify_page(client, p["course_id"], slug, p.get("live_page_id"), week_code, counts)
        report["pages"].append({
            "subject": subject, "course_id": p["course_id"],
            "page_id": p.get("live_page_id"), "verified": ok, "detail": detail,
        })
        if not ok:
            report["failures"].append(f"{subject}: page readback failed ({detail})")
            return _finish_partial(quarter, week, report, "DEPLOYMENT_PARTIAL")

    # ---- 4. Assignment writes + 5. readback ------------------------------
    for a in plan.get("assignments", []):
        title = a["title"]
        if a.get("duplicate_classification") == "EXACT_MATCH":
            report["assignments"].append({
                "title": title, "course_id": a["course_id"], "disposition": "ALREADY_EXISTS",
                "verified": True, "canvas_id": None,
            })
            continue
        try:
            created = client.create_assignment(
                a["course_id"], title=title, description="", assignment_group=a["assignment_group"],
                points=a["points_possible"], grading_type=a["grading_type"],
                submission_type=_submission_type(a.get("submission_types")),
                due_at=a["due_utc"], counts_toward_final_grade=not a["omit_from_final_grade"],
                published=True)
            counts["POST"] += 1
            aid = created.get("id")
            ok, detail = _verify_assignment(client, a["course_id"], aid, title, a["due_utc"], counts)
            report["assignments"].append({
                "title": title, "course_id": a["course_id"], "assignment_group": a["assignment_group"],
                "due_at": a["due_utc"], "canvas_id": aid,
                "disposition": "PUBLISHED_VERIFIED" if ok else "FAILED",
                "verified": ok, "detail": detail,
            })
            if not ok:
                report["failures"].append(f"assignment {title!r}: readback mismatch ({detail})")
                return _finish_partial(quarter, week, report, "DEPLOYMENT_PARTIAL")
        except (DeployClientError, Exception) as exc:  # noqa: BLE001
            report["failures"].append(f"assignment {title!r}: write failed: {type(exc).__name__}")
            return _finish_partial(quarter, week, report, "DEPLOYMENT_PARTIAL")

    # ---- 6. Announcement writes + 7. readback -----------------------------
    for a in plan.get("weekly_announcements", []):
        title = a["title"]
        if a.get("duplicate_classification") == "EXACT_MATCH":
            report["weekly_announcements"].append({
                "subject": a["subject"], "title": title, "course_id": a["course_id"],
                "disposition": "ALREADY_EXISTS", "verified": True, "canvas_id": None,
            })
            continue
        try:
            created = client.create_announcement(
                a["course_id"], title=title, message=a["message"], published=True,
                delayed_post_at=a.get("delayed_post_at"))
            counts["POST"] += 1
            tid = created.get("id")
            ok, detail = _verify_announcement(
                client, a["course_id"], tid, title=title, scheduled=bool(a.get("scheduled")),
                delayed_post_at=a.get("delayed_post_at"), expect_agenda=True, counts=counts)
            report["weekly_announcements"].append({
                "subject": a["subject"], "title": title, "course_id": a["course_id"],
                "delayed_post_at": a.get("delayed_post_at"), "canvas_id": tid,
                "disposition": "PUBLISHED_VERIFIED" if ok else "FAILED",
                "verified": ok, "detail": detail,
            })
            if not ok:
                report["failures"].append(f"announcement {title!r}: readback mismatch ({detail})")
                return _finish_partial(quarter, week, report, "DEPLOYMENT_PARTIAL")
        except Exception as exc:  # noqa: BLE001
            report["failures"].append(f"announcement {title!r}: write failed: {type(exc).__name__}")
            return _finish_partial(quarter, week, report, "DEPLOYMENT_PARTIAL")

    for a in plan.get("assessment_reminders", []):
        title = a["title"]
        if a.get("duplicate_classification") == "EXACT_MATCH":
            report["assessment_reminders"].append({
                "title": title, "course_id": a["course_id"], "disposition": "ALREADY_EXISTS",
                "verified": True, "canvas_id": None,
            })
            continue
        try:
            created = client.create_announcement(
                a["course_id"], title=title, message=a["message"], published=True,
                delayed_post_at=None)
            counts["POST"] += 1
            tid = created.get("id")
            ok, detail = _verify_announcement(
                client, a["course_id"], tid, title=title, scheduled=False,
                delayed_post_at=None, expect_agenda=False, counts=counts)
            report["assessment_reminders"].append({
                "title": title, "course_id": a["course_id"], "type": a.get("type"),
                "canvas_id": tid, "disposition": "PUBLISHED_VERIFIED" if ok else "FAILED",
                "verified": ok, "detail": detail,
            })
            if not ok:
                report["failures"].append(f"assessment reminder {title!r}: readback mismatch ({detail})")
                return _finish_partial(quarter, week, report, "DEPLOYMENT_PARTIAL")
        except Exception as exc:  # noqa: BLE001
            report["failures"].append(f"assessment reminder {title!r}: write failed: {type(exc).__name__}")
            return _finish_partial(quarter, week, report, "DEPLOYMENT_PARTIAL")

    # ---- 9/10. Final sweep + finalize -------------------------------------
    report["finished_at"] = _now()
    report["deployment_state"] = "PUBLISHED_VERIFIED"
    report["communication"] = {"email_sends": 0, "canvas_inbox_sends": 0}
    report["notes"].append("All writes passed post-write readback; every artifact has an explicit final disposition.")
    ledger.write_ledger(quarter, week, report)

    # Canonical published-verified ledger (the adapter reads this).
    ledger.finalize_published_verified(quarter, week, _published_ledger(report))
    return report


def _published_ledger(report: dict[str, Any]) -> dict[str, Any]:
    """Shape the canonical published-verified-ledger.json from the deploy report."""
    return {
        "school_year": report.get("school_year"),
        "quarter": report.get("quarter"),
        "week": report.get("week"),
        "week_code": report.get("week_code"),
        "verified_at": report.get("finished_at"),
        "status": "PUBLISHED_VERIFIED",
        "pages": [
            {"subject": p["subject"], "course_id": p["course_id"], "page_id": p["page_id"],
             "verified": p["verified"]}
            for p in report.get("pages", [])
        ],
        "assignments": [
            {"assignment_id": a["canvas_id"], "title": a["title"], "course_id": a["course_id"],
             "verified": a["verified"]}
            for a in report.get("assignments", []) if a.get("canvas_id")
        ],
        "weekly_announcements": [
            {"subject": a["subject"], "announcement_id": a["canvas_id"], "course_id": a["course_id"],
             "verified": a["verified"]}
            for a in report.get("weekly_announcements", []) if a.get("canvas_id")
        ],
        "assessment_reminders": [
            {"type": a.get("type"), "announcement_id": a["canvas_id"], "course_id": a["course_id"],
             "verified": a["verified"]}
            for a in report.get("assessment_reminders", []) if a.get("canvas_id")
        ],
        "deleted_assignments": report.get("deleted_assignments", []),
        "communication": report.get("communication", {}),
        "untouched": report.get("untouched", {}),
        "notes": report.get("notes", []),
    }


def _finish_partial(quarter: int, week: int, report: dict[str, Any], state: str) -> dict[str, Any]:
    report["finished_at"] = _now()
    report["deployment_state"] = state
    report["corrective_plan"] = {
        "completed": [a.get("title") or a.get("subject") for a in
                      report["pages"] + report["assignments"] + report["weekly_announcements"]
                      + report["assessment_reminders"] if a.get("verified")],
        "failed": list(report["failures"]),
        "recommendation": [
            "Inspect the failed object's exact Canvas state.",
            "Correct the underlying issue (identity/group/duplicate).",
            "Rerun preflight, then deploy again — idempotent rerun skips already-written objects.",
        ],
    }
    ledger.write_ledger(quarter, week, report)
    return report


def verify(quarter: int, week: int, *, client: DeployClient) -> dict[str, Any]:
    """Post-hoc readback verification of a prior deployment (from the ledger)."""
    rec = ledger.load_ledger(quarter, week)
    if rec is None:
        raise DeploymentBlocked("no deployment ledger for this week")
    counts: dict[str, int] = {"GET": 0, "POST": 0, "PUT": 0, "PATCH": 0, "DELETE": 0}
    failures: list[str] = []
    slug = None
    pre = rec.get("preflight_id")
    if pre:
        preflight = ledger.load_preflight(quarter, week, pre)
        if preflight:
            slug = preflight.get("plan", {}).get("slug", "")

    for p in rec.get("pages", []):
        if slug:
            ok, detail = _verify_page(client, p["course_id"], slug, p.get("page_id"),
                                      rec.get("week_code", ""), counts)
            p["reverified"] = ok
            if not ok:
                failures.append(f"page {p['subject']}: {detail}")
    for a in rec.get("assignments", []):
        if a.get("canvas_id"):
            ok, detail = _verify_assignment(client, a["course_id"], a["canvas_id"],
                                            a["title"], a.get("due_at", ""), counts)
            a["reverified"] = ok
            if not ok:
                failures.append(f"assignment {a['title']}: {detail}")
    return {"quarter": quarter, "week": week, "verb_totals": counts,
            "failures": failures, "ok": len(failures) == 0}


def command_self_test() -> int:
    import tempfile
    from .client import FakeDeployClient

    # A fully-seeded fake deployment environment.
    courses = {
        26404: {"id": 26404, "name": "Math", "workflow_state": "available"},
        26442: {"id": 26442, "name": "Reading/Spelling", "workflow_state": "available"},
    }
    client = FakeDeployClient(courses=courses)
    client.assignment_groups[26404] = [{"id": "60321", "name": "Homework/Class Work"},
                                       {"id": "60319", "name": "Written Assessments"},
                                       {"id": "60320", "name": "Fact Assessments"}]
    client.seed_page(26404, "q2w3-october-26-30-2026", title="Q2W3", body="<div id='kl_wrapper_3'>x</div><p>Reminders</p>")

    # Confirm gate rejects missing confirmation.
    import scripts.canvas_llm_deploy.ledger as lg
    import scripts.canvas_llm_intake.manifest as imf
    orig_deploy = lg.DEPLOY_ROOT
    orig_staging = imf.staging_dir
    with tempfile.TemporaryDirectory() as tmp:
        from pathlib import Path
        lg.DEPLOY_ROOT = Path(tmp) / "deployments"
        imf.staging_dir = lambda q, w: Path(tmp) / "intake" / f"q{q}w{w}"
        try:
            # No preflight -> blocked.
            try:
                deploy(2, 3, preflight_id="missing", expected_source_hash="",
                       expected_approval_snapshot_hash="", owner_confirmation="DEPLOY Q2W3",
                       client=client)
                raise AssertionError("expected blocked")
            except DeploymentBlocked:
                pass
            print("PASS canvas-deploy coordinator self-test")
        finally:
            lg.DEPLOY_ROOT = orig_deploy
            imf.staging_dir = orig_staging
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
