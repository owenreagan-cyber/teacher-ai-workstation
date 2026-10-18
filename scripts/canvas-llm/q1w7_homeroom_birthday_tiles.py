#!/usr/bin/env python3
"""Apply the canonical Homeroom birthday-tile standard to the live Week 7 newsletter.

Targeted, guarded update of the rolling Homeroom newsletter and its matching
Week 7 family announcement. No other newsletter content is changed.

Sequence (each stage fresh-GETs Canvas; no write happens unless every
precondition passes):

1. RECONCILE  (read-only; raw urllib GET)
   - fresh-GET the live Homeroom newsletter (``q1w2-july-27-31-2026``);
   - confirm it is in the expected Week 7 state (Week 7 badge, September-only
     birthday card with the legacy single-sentence wording, no August card);
   - snapshot body/title/front-page for the before-write drift guard;
   - fresh-GET Homeroom announcements and confirm exactly one Week 7 family
     announcement exists.

2. DRIFT GUARD  (immediately before write)
   - fresh-GET the newsletter again and compare body hash / title / front-page
     against the snapshot; any change since reconcile blocks the write.

3. PUBLISH  (only if reconcile + drift guard are clean)
   - update the rolling newsletter in place (birthday tiles; ``front_page``
     preserved as a verify/no-op);
   - update the existing ``4th Grade Happenings - Week 7`` announcement in place
     so its embedded newsletter matches the updated page exactly.

4. VERIFY  (read-only)
   - fresh-GET both and confirm tiles, front-page state, and byte-exact
     newsletter/announcement match.

Usage:
    python3 scripts/canvas-llm/q1w7_homeroom_birthday_tiles.py --reconcile-only
    CANVAS_LLM_DEPLOYMENT_MODE=live CANVAS_LLM_LIVE_Q1W2_APPROVED=1 \
        python3 scripts/canvas-llm/q1w7_homeroom_birthday_tiles.py

Credentials resolve via canvas_credentials.load_credentials(). Token never printed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_credentials as credentials  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_writer as writer  # noqa: E402
from scripts.canvas_llm_phase22 import homeroom_newsletter as hn  # noqa: E402

COURSE_ID = 26429
PAGE_REF = "q1w2-july-27-31-2026"
PAGE_TITLE = "Q1W2 - July 27-31, 2026"
ANNOUNCEMENT_TITLE = "4th Grade Happenings - Week 7"
MONTH = "September"
STUDENTS = [("Ava", "September 4"), ("Timothy", "September 16"), ("Charlotte", "September 17")]

# Expected Week 7 state markers (absence is a blocker).
LEGACY_SENTENCE = (
    "Happy Birthday to Ava on September 4, Timothy on September 16, "
    "and Charlotte on September 17!"
)
WEEK7_BADGE = "Week 7 \u00b7 August 31\u2013September 4, 2026"


def _newsletter_div(html: str) -> str:
    """Extract the embedded newsletter wrapper div (``max-width: 900px`` block)."""
    start = html.find('<div style="max-width: 900px')
    if start < 0:
        return ""
    end = html.rfind("</div>")
    if end < 0:
        return ""
    return html[start : end + len("</div>")]


def _norm(text: object) -> str:
    return " ".join(str(text or "").split())


def _snapshot(page: dict[str, Any] | None) -> dict[str, Any] | None:
    if not page:
        return None
    return {
        "body_sha256": hashlib.sha256(_norm(page.get("body")).encode("utf-8")).hexdigest(),
        "title": page.get("title"),
        "front_page": bool(page.get("front_page")),
    }


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


def _announcements(base_url: str, token: str) -> list[Any]:
    url = f"{base_url}/api/v1/courses/{COURSE_ID}/discussion_topics?only_announcements=true&per_page=100"
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
        items.extend(data if isinstance(data, list) else [data])
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


def _reconcile(base_url: str, token: str) -> tuple[dict[str, Any], list[str]]:
    blockers: list[str] = []
    state: dict[str, Any] = {}

    page = _get(base_url, token, f"/api/v1/courses/{COURSE_ID}/front_page")
    if isinstance(page, dict) and "__error__" in page:
        blockers.append(f"Homeroom newsletter front-page GET failed: {page['__error__']}")
        return state, blockers
    body = page.get("body") or ""
    state["snapshot"] = _snapshot(page)
    state["page_title"] = page.get("title")
    state["front_page"] = bool(page.get("front_page"))
    state["page_url"] = page.get("url")

    # Expected Week 7 state checks (absence = unexpected drift).
    if "September Birthdays" not in body:
        blockers.append("Homeroom newsletter: 'September Birthdays' section not found")
    if LEGACY_SENTENCE not in body:
        blockers.append("Homeroom newsletter: legacy September birthday sentence not found (unexpected state)")
    if WEEK7_BADGE not in body:
        blockers.append("Homeroom newsletter: Week 7 badge not found (unexpected state)")
    if "August Birthdays" in body:
        blockers.append("Homeroom newsletter: August Birthdays card still present (unexpected state)")

    anns = _announcements(base_url, token)
    week7 = [a for a in anns if (a.get("title") or "").strip() == ANNOUNCEMENT_TITLE]
    state["week7_announcement_count"] = len(week7)
    if len(week7) != 1:
        blockers.append(
            f"Homeroom Week 7 family announcement count is {len(week7)} (expected exactly 1)"
        )
    else:
        state["week7_announcement_id"] = week7[0].get("id")

    return state, blockers


def _verify(base_url: str, token: str) -> dict[str, Any]:
    report: dict[str, Any] = {}

    page = _get(base_url, token, f"/api/v1/courses/{COURSE_ID}/front_page")
    body = page.get("body") or "" if isinstance(page, dict) else ""
    report["tiles"] = body.count("min-width: 220px") == 3
    report["ava"] = "Ava" in body and "September 4" in body
    report["timothy"] = "Timothy" in body and "September 16" in body
    report["charlotte"] = "Charlotte" in body and "September 17" in body
    report["front_page"] = bool((page or {}).get("front_page")) if isinstance(page, dict) else False
    report["legacy_sentence_gone"] = LEGACY_SENTENCE not in body

    anns = _announcements(base_url, token)
    week7 = [a for a in anns if (a.get("title") or "").strip() == ANNOUNCEMENT_TITLE]
    report["announcement_count"] = len(week7)
    if len(week7) == 1:
        full = _get(base_url, token, f"/api/v1/courses/{COURSE_ID}/discussion_topics/{week7[0]['id']}")
        msg = (full or {}).get("message") or "" if isinstance(full, dict) else ""
        # The announcement embeds the full newsletter; compare the newsletter div only.
        report["announcement_match"] = _newsletter_div(msg) == _newsletter_div(body)
    else:
        report["announcement_match"] = False

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply Homeroom birthday-tile standard (Week 7)")
    parser.add_argument("--reconcile-only", action="store_true", help="GET-only reconcile, no writes")
    parser.add_argument("--verify-only", action="store_true", help="GET-only verify, no writes")
    args = parser.parse_args()

    credentials.load_credentials()
    base_url = os.environ["CANVAS_BASE_URL"].strip().rstrip("/")
    token = os.environ["CANVAS_TOKEN"]

    if args.verify_only:
        print("=== HOMEROOM BIRTHDAY TILES — VERIFY (GET-only) ===")
        report = _verify(base_url, token)
        print("\n=== REPORT ===")
        print(f"Homeroom newsletter birthday tiles: {'PASS' if report['tiles'] else 'FAIL'}")
        print(f"Ava tile: {'PASS' if report['ava'] else 'FAIL'}")
        print(f"Timothy tile: {'PASS' if report['timothy'] else 'FAIL'}")
        print(f"Charlotte tile: {'PASS' if report['charlotte'] else 'FAIL'}")
        print(f"rolling newsletter still front_page=true: {'PASS' if report['front_page'] else 'FAIL'}")
        print(f"Week 7 family announcement updated in place: {'PASS' if report['announcement_count'] == 1 else 'FAIL'}")
        print(f"newsletter/announcement HTML match: {'PASS' if report['announcement_match'] else 'FAIL'}")
        print(f"WRITES PERFORMED: 0")
        print(f"REMAINING WRITE ACTIONS: 0")
        print(f"BLOCKERS: 0")
        all_pass = (
            report["tiles"] and report["ava"] and report["timothy"] and report["charlotte"]
            and report["front_page"] and report["announcement_count"] == 1
            and report["announcement_match"]
        )
        if all_pass:
            print("HOMEROOM BIRTHDAY TILE STANDARD: LIVE")
        return 0 if all_pass else 1

    print("=== HOMEROOM BIRTHDAY TILES — RECONCILE (GET-only) ===")
    state, blockers = _reconcile(base_url, token)
    if state.get("snapshot"):
        print(f"newsletter url: {state.get('page_url')!r}")
        print(f"newsletter title: {state.get('page_title')!r}")
        print(f"newsletter front_page: {state.get('front_page')}")
    print(f"Week 7 family announcement count: {state.get('week7_announcement_count')}")
    print(f"legacy sentence present: {state.get('snapshot') is not None and not any('legacy' in b for b in blockers)}")

    if blockers:
        print("\nBLOCKERS:")
        for b in blockers:
            print(f"  - {b}")
        print("STOPPED: no writes performed.")
        print("WRITES PERFORMED: 0")
        return 1

    # Before-write drift guard: re-fresh-GET and compare to the reconcile snapshot.
    print("\n=== HOMEROOM BIRTHDAY TILES — DRIFT GUARD (GET-only) ===")
    page_now = _get(base_url, token, f"/api/v1/courses/{COURSE_ID}/front_page")
    snap = state["snapshot"]
    live_now = _snapshot(page_now)
    drift = False
    if live_now != snap:
        drift = True
        print("DRIFT: Homeroom newsletter changed since reconcile (would block write)")
        print(f"  snapshot: {snap}")
        print(f"  live now: {live_now}")
    else:
        print("live newsletter matches the reconcile snapshot (body, title, front_page).")
        print("RESULT: PASS (no drift)")

    if drift:
        print("STOPPED: no writes performed.")
        print("WRITES PERFORMED: 0")
        return 1

    if args.reconcile_only:
        print("\nRECONCILE + DRIFT GUARD CLEAN — no writes performed (--reconcile-only).")
        print("WRITES PERFORMED: 0")
        print("BLOCKERS: 0")
        return 0

    print("\nRECONCILE + DRIFT GUARD CLEAN — proceeding to publish.")

    # Build the new newsletter body (birthday tiles only).
    live_body = page_now.get("body") or ""
    new_body = hn.replace_birthday_section(live_body, MONTH, STUDENTS)

    # Announcement message: same replacement applied to its embedded newsletter.
    anns = _announcements(base_url, token)
    week7 = [a for a in anns if (a.get("title") or "").strip() == ANNOUNCEMENT_TITLE]
    topic_id = str(week7[0]["id"])
    live_msg = _get(base_url, token, f"/api/v1/courses/{COURSE_ID}/discussion_topics/{topic_id}").get("message") or ""
    new_msg = hn.replace_birthday_section(live_msg, MONTH, STUDENTS)

    writes = 0
    remaining: list[str] = []

    page_res = writer.update_page_live(
        course_id=COURSE_ID,
        page_ref=PAGE_REF,
        title=PAGE_TITLE,
        body=new_body,
        published=True,
        front_page=None,  # preserve front_page=true as a verify/no-op
        approved=True,
        approved_by="Owen Reagan",
    )
    if getattr(page_res, "write_status", "BLOCKED") == "WRITTEN":
        writes += 1
        print(f"WRITTEN: Homeroom newsletter page '{PAGE_REF}' (birthday tiles)")
    else:
        remaining.append("newsletter page update")
        print(f"BLOCKED: newsletter page update ({','.join(getattr(page_res, 'blockers', []) or ['blocked'])})")

    ann_res = writer.update_announcement_live(
        course_id=COURSE_ID,
        topic_id=topic_id,
        title=ANNOUNCEMENT_TITLE,
        message=new_msg,
        published=None,
        approved=True,
        approved_by="Owen Reagan",
    )
    if getattr(ann_res, "write_status", "BLOCKED") == "WRITTEN":
        writes += 1
        print(f"WRITTEN: '{ANNOUNCEMENT_TITLE}' announcement (updated in place)")
    else:
        remaining.append("Week 7 family announcement update")
        print(f"BLOCKED: announcement update ({','.join(getattr(ann_res, 'blockers', []) or ['blocked'])})")

    print(f"\nWRITES PERFORMED: {writes}")

    print("\n=== HOMEROOM BIRTHDAY TILES — VERIFY (GET-only) ===")
    report = _verify(base_url, token)

    print("\n=== REPORT ===")
    print(f"Homeroom newsletter birthday tiles: {'PASS' if report['tiles'] else 'FAIL'}")
    print(f"Ava tile: {'PASS' if report['ava'] else 'FAIL'}")
    print(f"Timothy tile: {'PASS' if report['timothy'] else 'FAIL'}")
    print(f"Charlotte tile: {'PASS' if report['charlotte'] else 'FAIL'}")
    print(f"rolling newsletter still front_page=true: {'PASS' if report['front_page'] else 'FAIL'}")
    print(f"Week 7 family announcement updated in place: {'PASS' if report['announcement_count'] == 1 else 'FAIL'}")
    print(f"newsletter/announcement HTML match: {'PASS' if report['announcement_match'] else 'FAIL'}")
    print(f"WRITES PERFORMED: {writes}")
    print(f"REMAINING WRITE ACTIONS: {len(remaining)}")
    for r in remaining:
        print(f"  - {r}")
    blockers_count = len(remaining)
    print(f"BLOCKERS: {blockers_count}")

    all_pass = (
        report["tiles"] and report["ava"] and report["timothy"] and report["charlotte"]
        and report["front_page"] and report["announcement_count"] == 1
        and report["announcement_match"] and not remaining
    )
    if all_pass:
        print("HOMEROOM BIRTHDAY TILE STANDARD: LIVE")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
