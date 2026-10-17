"""GET-only deployment preflight (no writes) + short-lived preflight records.

``run_preflight`` validates the READY_TO_PUBLISH gate, resolves live objects via
GET-only lookups, classifies duplicates, and produces an exact write plan plus a
short-lived preflight record. Deployment may only execute against that exact
preflight record.
"""
from __future__ import annotations

import hashlib
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
        live["pages"][p["subject"]] = {
            "page_id": found.get("page_id") or found.get("id"),
            "url": found.get("url"),
            "title": found.get("title"),
        }
        p["live_page_id"] = found.get("page_id") or found.get("id")

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

    # ---- Announcement duplicate identity (idempotent skip) ---------------
    ann_cache: dict[int, list[str]] = {}
    for a in plan.get("weekly_announcements", []) + plan.get("assessment_reminders", []):
        cid = a["course_id"]
        if client is None:
            continue
        if cid not in ann_cache:
            try:
                ann_cache[cid] = [x.get("title") or "" for x in client.list_announcements(int(cid))]
            except Exception:  # noqa: BLE001 - listing is advisory
                ann_cache[cid] = []
        cls = classify_assignment(a.get("title", ""), ann_cache[cid])
        a["duplicate_classification"] = cls
        live["announcements"].setdefault(a.get("title"), cls)
        if cls == "AMBIGUOUS":
            blockers.append(f"announcement {a.get('title')!r}: ambiguous near-duplicate exists")

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
