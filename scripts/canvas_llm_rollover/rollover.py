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

from datetime import date, datetime, timezone
from typing import Any

from scripts.canvas_llm_intake import manifest as imf
from scripts.canvas_llm_deploy import preflight as deploy_preflight
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
        blockers.append("upcoming week intake packet missing (run prepare-next)")
    else:
        if not m.get("ready_to_publish"):
            blockers.append("upcoming week is not READY_TO_PUBLISH")
            blockers.extend(m.get("publish_blockers", []))
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

    # Homeroom content freshness.
    h = plan.get("homeroom", {})
    if not h.get("source_content_hash"):
        blockers.append("homeroom: approved content source missing")

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
) -> dict[str, Any]:
    """GET-only rollover preflight: readiness gate + live object resolution."""
    readiness = build_readiness(from_quarter, from_week, to_quarter, to_week, today=today)
    plan = readiness["manifest"]
    blockers = list(readiness["blockers"])
    warnings: list[str] = []
    live: dict[str, Any] = {"academic": {}, "homeroom": {}}

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

    # Homeroom target.
    h = plan["homeroom"]
    hres = _resolve_target(client, h["course_id"], h["to_page_slug"], "Homeroom", plan["to_week"])
    live["homeroom"] = hres
    blockers.extend(hres["blockers"])
    h["page_id"] = hres["page_id"]
    h["already_front_page"] = hres["front_page"]
    h["front_page_action"] = "SKIP" if hres["front_page"] else "SET_FRONT_PAGE"

    # Announcement duplicate classification (week-aware).
    for a in plan.get("weekly_announcements", []):
        cid = a["course_id"]
        if cid is None:
            continue
        try:
            existing = client.list_announcements(int(cid))
        except Exception:  # noqa: BLE001
            existing = []
        a["classification"] = deploy_preflight.classify_weekly_announcement(a, existing)
        if a["classification"] == "BODY_CHANGED_SAME_WEEK":
            blockers.append(f"{a['subject']}: weekly update body changed within the same week (owner review required)")

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
        "homeroom": {},
        "weekly_announcements": [],
        "failures": [],
        "notes": [],
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

    # ---- C. Homeroom rollover --------------------------------------------
    h = manifest["homeroom"]
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
    proposed = h.get("proposed_content")
    proposed_hash = h.get("proposed_content_hash")
    if not proposed:
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
                body=homeroom_mod.render_proposed(proposed), published=True, front_page=False,
            )
            counts["PUT"] += 1
        except Exception as exc:  # noqa: BLE001
            report["failures"].append(f"homeroom: copy-forward write failed: {type(exc).__name__}")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
    if not hres["front_page"]:
        try:
            client.set_front_page(h["course_id"], hres["page_id"])
            counts["PUT"] += 1
        except Exception as exc:  # noqa: BLE001
            report["failures"].append(f"homeroom: front-page write failed: {type(exc).__name__}")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
    try:
        hread = client.get_page(h["course_id"], h["to_page_slug"])
        counts["GET"] += 1
    except Exception as exc:  # noqa: BLE001
        report["failures"].append(f"homeroom: readback failed: {type(exc).__name__}")
        return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
    h_ok = str(hread.get("page_id")) == str(hres["page_id"]) and bool(hread.get("front_page"))
    report["homeroom"] = {
        "course_id": h["course_id"], "page_id": hres["page_id"],
        "disposition": "PUBLISHED_VERIFIED" if h_ok else "FAILED", "verified": h_ok,
    }
    if not h_ok:
        report["failures"].append("homeroom: front-page readback mismatch")

    # ---- D. Weekly update announcements ----------------------------------
    for a in manifest.get("weekly_announcements", []):
        cid = a["course_id"]
        if a.get("classification") == "EXACT_MATCH":
            report["weekly_announcements"].append(
                {"subject": a["subject"], "disposition": "ALREADY_EXISTS", "verified": True})
            continue
        try:
            created = client.create_announcement(
                cid, title=a["title"], message=a["message"], published=True,
                delayed_post_at=a.get("delayed_post_at"))
            counts["POST"] += 1
            tid = created.get("id")
        except Exception as exc:  # noqa: BLE001
            report["failures"].append(f"{a['subject']}: announcement write failed: {type(exc).__name__}")
            return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
        # Verify scheduling/visibility (HELD_SCHEDULED when future + not active).
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
        ok = state == sched.HELD_SCHEDULED
        report["weekly_announcements"].append({
            "subject": a["subject"], "title": a["title"], "announcement_id": tid,
            "delayed_post_at": a.get("delayed_post_at"), "state": state,
            "disposition": "PUBLISHED_VERIFIED" if ok else "FAILED", "verified": ok,
        })
        if not ok:
            report["failures"].append(f"{a['subject']}: announcement visibility mismatch ({state})")

    # ---- E. Finalize ------------------------------------------------------
    report["finished_at"] = _now()
    if report["failures"]:
        return _finish(to_quarter, to_week, report, schedule.BLOCKED, counts)
    report["lifecycle"] = schedule.PUBLISHED_VERIFIED
    report["communication"] = {"email_sends": 0, "canvas_inbox_sends": 0}
    ledger.write_rollover_ledger(to_quarter, to_week, report)
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
