#!/usr/bin/env python3
"""Publish the four Q1W7 subject Weekly Update announcements (guarded).

Sequence (each stage fresh-GETs Canvas; no write happens unless every
precondition passes):

1. RECONCILE  (read-only; raw urllib GET)
   - for each subject, fresh-GET the live front page and confirm its
     ``kl_wrapper_3`` agenda block is byte-identical to the announcement's
     embedded agenda (the manifest page body);
   - fresh-GET course announcements and confirm NO same-week Weekly Update
     already exists (duplicate) and no same-week update with a different
     agenda (drift);
   - for History, confirm the moved-test notice is still present.

2. PUBLISH  (only if reconcile is clean)
   - create each announcement through the controlled live writer
     ``create_announcement_live(approved=True)``, published immediately, NOT
     delayed. This is the same guarded path used for prior live writes.

3. VERIFY  (read-only)
   - fresh-GET each announcement; confirm exactly one Q1W7 weekly update,
     published, with Week in Review, Week Ahead, embedded agenda matching the
     live front page, and (History) the schedule-change note.

Usage:
    python3 scripts/canvas-llm/q1w7_subject_weekly_publish.py --reconcile-only
    CANVAS_LLM_DEPLOYMENT_MODE=live CANVAS_LLM_LIVE_Q1W2_APPROVED=1 \
        python3 scripts/canvas-llm/q1w7_subject_weekly_publish.py

Credentials resolve via canvas_credentials.load_credentials(). Token never printed.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_credentials as credentials  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_writer as writer  # noqa: E402
from scripts.canvas_llm_phase22 import subject_weekly_update as swu  # noqa: E402

OUT_DIR = REPO_ROOT / ".local" / "canvas-llm" / "q1w7-audit"
DRIVER = REPO_ROOT / "scripts" / "canvas-llm" / "q1w7_subject_weekly_announcements.py"
WEEK_MARKER = "August 31\u2013September 4, 2026"


def _load_driver() -> Any:
    spec = importlib.util.spec_from_file_location("q1w7_subject_weekly_announcements", DRIVER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _page_bodies() -> dict[str, str]:
    manifest = json.loads((OUT_DIR / "q1w7-manifest.json").read_text(encoding="utf-8"))
    bodies: dict[str, str] = {}
    for action in manifest.get("actions", []):
        if action.get("object_type") == "page" and action.get("course") in {
            "Math", "Reading/Spelling", "Language Arts", "History",
        }:
            bodies[action["course"]] = action.get("body") or ""
    return bodies


def _get(base_url: str, token: str, path: str) -> Any:
    req = urllib.request.Request(
        f"{base_url}{path}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            text = response.read().decode("utf-8")
            return json.loads(text) if text else None
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = (exc.read() or b"").decode("utf-8", "replace")[:200]
        except Exception:  # noqa: BLE001
            detail = ""
        return {"__error__": f"HTTP {exc.code}: {detail or exc.reason}"}
    except urllib.error.URLError as exc:
        return {"__error__": f"network: {exc.reason}"}


def _paginate(base_url: str, token: str, path: str) -> list[Any]:
    url = f"{base_url}{path}?only_announcements=true&per_page=100"
    items: list[Any] = []
    for _ in range(20):
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            text = response.read().decode("utf-8")
            link = response.headers.get("Link", "")
        data = json.loads(text) if text else []
        if isinstance(data, list):
            items.extend(data)
        else:
            items.append(data)
            break
        nxt = None
        for part in link.split(","):
            if 'rel="next"' in part:
                s = part.find("<")
                e = part.find(">")
                if 0 <= s < e:
                    nxt = part[s + 1 : e]
        if not nxt:
            break
        url = nxt
    return items


def reconcile(driver: Any, base_url: str, token: str) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Fresh GET-only reconciliation. Returns (state, blockers)."""
    bodies = _page_bodies()
    blockers: list[str] = []
    state: dict[str, dict[str, Any]] = {}
    for subject_key in ("math", "reading_spelling", "language_arts", "history"):
        course = driver.DRAFTS[subject_key]["course"]
        cid = swu.SUBJECTS[subject_key]["course_id"]
        title = swu.SUBJECTS[subject_key]["title"]
        manifest_body = bodies[course]
        expected_core = swu.agenda_core(manifest_body)

        front = _get(base_url, token, f"/api/v1/courses/{cid}/front_page")
        if isinstance(front, dict) and "__error__" in front:
            blockers.append(f"{course}: front_page GET failed: {front['__error__']}")
            continue
        live_core = swu.agenda_core(front.get("body") or "")
        agenda_match = live_core == expected_core
        if not agenda_match:
            blockers.append(
                f"{course}: front-page agenda does not match announcement-embedded agenda "
                f"(live {len(live_core)} chars vs embedded {len(expected_core)} chars)"
            )

        anns = _paginate(base_url, token, f"/api/v1/courses/{cid}/discussion_topics")
        status, match_id = swu.classify_duplicate(
            anns, title=title, week_marker=WEEK_MARKER, expected_core=expected_core
        )
        if status == "DRIFT":
            blockers.append(f"{course}: existing Q1W7 Weekly Update has a different embedded agenda (id={match_id})")

        state[subject_key] = {
            "course": course,
            "course_id": cid,
            "title": title,
            "front_url": front.get("url") if isinstance(front, dict) else None,
            "front_page": front.get("front_page") if isinstance(front, dict) else None,
            "agenda_match": agenda_match,
            "duplicate_status": status,
            "existing_id": match_id,
        }

    hist_anns = _paginate(base_url, token, "/api/v1/courses/28165/discussion_topics")
    moved_notice = any(
        "World Mountains Test Moved" in (a.get("title") or "") for a in hist_anns
    )
    state["history_moved_notice_present"] = moved_notice
    if not moved_notice:
        blockers.append("History: moved-test notice ('Update - World Mountains Test Moved to Wednesday') is missing")

    return state, blockers


def verify(driver: Any, base_url: str, token: str) -> tuple[dict[str, str], bool]:
    bodies = _page_bodies()
    verify_map: dict[str, str] = {}
    all_live = True
    for subject_key in ("math", "reading_spelling", "language_arts", "history"):
        course = driver.DRAFTS[subject_key]["course"]
        cid = swu.SUBJECTS[subject_key]["course_id"]
        title = swu.SUBJECTS[subject_key]["title"]

        anns = _paginate(base_url, token, f"/api/v1/courses/{cid}/discussion_topics")
        matches = swu.find_weekly_update(anns, title=title, week_marker=WEEK_MARKER)

        if len(matches) != 1:
            verify_map[course] = "FAIL"
            all_live = False
            print(f"{course} Weekly Update: FAIL (found {len(matches)} matches)")
            continue

        topic_id = matches[0].get("id")
        full = _get(base_url, token, f"/api/v1/courses/{cid}/discussion_topics/{topic_id}")
        if isinstance(full, dict) and "__error__" in full:
            verify_map[course] = "FAIL"
            all_live = False
            print(f"{course} Weekly Update: FAIL ({full['__error__']})")
            continue
        msg = full.get("message") or ""
        published = bool(full.get("published"))
        delayed = full.get("delayed_post_at")
        front = _get(base_url, token, f"/api/v1/courses/{cid}/front_page")
        live_core = swu.agenda_core((front or {}).get("body") or "")

        review_ok = driver.DRAFTS[subject_key]["week_in_review"] in msg
        ahead_ok = driver.DRAFTS[subject_key]["week_ahead"] in msg
        agenda_ok = swu.agenda_core(msg) == live_core
        change_ok = True
        if subject_key == "history":
            change_ok = "originally scheduled for Friday, August 28, was moved to Wednesday, September 2" in msg

        ok = published and not delayed and review_ok and ahead_ok and agenda_ok and change_ok
        verify_map[course] = "LIVE" if ok else "FAIL"
        if not ok:
            all_live = False
        print(f"{course} Weekly Update: {'LIVE' if ok else 'FAIL'} "
              f"(published={published} delayed={bool(delayed)} review={review_ok} "
              f"ahead={ahead_ok} agenda_match={agenda_ok} change_note={change_ok})")
    return verify_map, all_live


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish Q1W7 subject Weekly Update announcements")
    parser.add_argument("--reconcile-only", action="store_true", help="GET-only reconcile, no writes")
    args = parser.parse_args()

    driver = _load_driver()
    credentials.load_credentials()
    base_url = os.environ["CANVAS_BASE_URL"].strip().rstrip("/")
    token = os.environ["CANVAS_TOKEN"]

    print("=== Q1W7 SUBJECT WEEKLY UPDATE — RECONCILE (GET-only) ===")
    state, blockers = reconcile(driver, base_url, token)
    for subject_key in ("math", "reading_spelling", "language_arts", "history"):
        s = state[subject_key]
        print(f"{s['course']:18} agenda_match={s['agenda_match']} "
              f"duplicate={s['duplicate_status']} front={s['front_url']!r}")
    print(f"History moved-test notice present: {state.get('history_moved_notice_present')}")

    if blockers:
        print("\nBLOCKERS:")
        for b in blockers:
            print(f"  - {b}")
        print("STOPPED: no writes performed.")
        print("WRITES PERFORMED: 0")
        return 1

    if args.reconcile_only:
        print("\nRECONCILE CLEAN — no writes performed (--reconcile-only).")
        print("WRITES PERFORMED: 0")
        return 0

    print("\nRECONCILE CLEAN — proceeding to publish.")

    # PUBLISH
    writes = 0
    results: dict[str, str] = {}
    bodies = _page_bodies()
    for subject_key in ("math", "reading_spelling", "language_arts", "history"):
        s = state[subject_key]
        if s["duplicate_status"] == "ALREADY_APPLIED":
            print(f"SKIP (already applied): {s['course']}")
            results[s["course"]] = "ALREADY_APPLIED"
            continue
        draft = driver.DRAFTS[subject_key]
        message = swu.build_message(
            subject_key,
            draft["week_in_review"],
            draft["week_ahead"],
            bodies[s["course"]],
            schedule_change=draft["schedule_change"],
        )
        res = writer.create_announcement_live(
            course_id=s["course_id"],
            title=s["title"],
            message=message,
            published=True,
            delayed_post_at=None,
            approved=True,
            approved_by="Owen Reagan",
        )
        if getattr(res, "write_status", "BLOCKED") == "WRITTEN":
            writes += 1
            results[s["course"]] = "WRITTEN"
            print(f"WRITTEN: {s['course']} '{s['title']}'")
        else:
            results[s["course"]] = "BLOCKED:" + ",".join(getattr(res, "blockers", []) or ["blocked"])
            print(f"BLOCKED: {s['course']} ({results[s['course']]})")

    print(f"\nWRITES PERFORMED: {writes}")

    # VERIFY
    print("\n=== Q1W7 SUBJECT WEEKLY UPDATE — VERIFY (GET-only) ===")
    verify_map, all_live = verify(driver, base_url, token)

    print("\n=== REPORT ===")
    for course in ("Math", "Reading/Spelling", "Language Arts", "History"):
        print(f"{course} Weekly Update: {verify_map.get(course, 'FAIL')}")
    print(f"WRITES PERFORMED: {writes}")
    remaining = [c for c, v in verify_map.items() if v != "LIVE"]
    print(f"REMAINING WRITE ACTIONS: {len(remaining)}")
    blockers_count = len([r for r in results.values() if r.startswith("BLOCKED")])
    print(f"BLOCKERS: {blockers_count}")
    if all_live:
        print("Q1W7 SUBJECT WEEKLY UPDATES: COMPLETE")
    return 0 if all_live else 1


if __name__ == "__main__":
    raise SystemExit(main())
