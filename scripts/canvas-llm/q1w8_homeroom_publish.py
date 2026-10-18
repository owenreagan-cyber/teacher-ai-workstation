#!/usr/bin/env python3
"""Publish the approved Q1W8 Homeroom newsletter + Picture Day reminders.

Guarded workflow (each stage fresh-GETs Canvas; no write happens unless every
precondition passes):

1. RECONCILE  (read-only; raw urllib GET)
   - fresh-GET the rolling Homeroom newsletter (``q1w2-july-27-31-2026``);
   - drift guard: compare live body/title/front-page against the saved Week 7
     source snapshot (``q1w8-newsletter-source.html``);
   - fresh-GET Homeroom announcements; confirm the two Picture Day
     announcements and ``4th Grade Happenings - Week 8`` are absent.

2. PUBLISH  (only if reconcile is clean)
   - update the rolling newsletter in place to Week 8 (``front_page`` preserved
     as a verify/no-op);
   - create ``4th Grade Happenings - Week 8`` (intro + full Week 8 newsletter);
   - create/schedule the Friday and Monday Picture Day reminders.

3. VERIFY  (read-only)
   - fresh-GET all four live objects/states and report.

Usage:
    python3 scripts/canvas-llm/q1w8_homeroom_publish.py --reconcile-only
    CANVAS_LLM_DEPLOYMENT_MODE=live CANVAS_LLM_LIVE_Q1W2_APPROVED=1 \
        python3 scripts/canvas-llm/q1w8_homeroom_publish.py

Credentials resolve via canvas_credentials.load_credentials(). Token never printed.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
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

AUDIT = REPO_ROOT / ".local" / "canvas-llm" / "q1w8-audit"
BUILD = AUDIT / "build_q1w8_newsletter.py"
SOURCE = AUDIT / "q1w8-newsletter-source.html"

COURSE_ID = 26429
PAGE_REF = "q1w2-july-27-31-2026"
PAGE_TITLE = "Q1W2 - July 27-31, 2026"
FAMILY_TITLE = "4th Grade Happenings - Week 8"
FRIDAY_TITLE = "Picture Day Reminder - Tuesday, September 8"
MONDAY_TITLE = "Picture Day Tomorrow"
FRIDAY_POST_AT = "2026-09-04T20:00:00Z"  # Friday Sept 4, 4:00 PM ET
MONDAY_POST_AT = "2026-09-07T20:00:00Z"  # Monday Sept 7, 4:00 PM ET


def _load_build() -> Any:
    spec = importlib.util.spec_from_file_location("build_q1w8_newsletter", BUILD)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _norm(text: object) -> str:
    return " ".join(str(text or "").split())


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
    live_body = page.get("body") or ""
    state["front_page"] = bool(page.get("front_page"))
    state["page_url"] = page.get("url")
    state["page_title"] = page.get("title")

    # Drift guard vs saved Week 7 source snapshot.
    source_body = SOURCE.read_text(encoding="utf-8")
    source_hash = hashlib.sha256(_norm(source_body).encode("utf-8")).hexdigest()
    live_hash = hashlib.sha256(_norm(live_body).encode("utf-8")).hexdigest()
    state["drift"] = live_hash != source_hash
    if state["drift"]:
        blockers.append(
            "DRIFT: live Homeroom newsletter differs from the saved Week 7 source "
            "snapshot (newer teacher/manual edits may exist)"
        )

    anns = _announcements(base_url, token)
    titles = {(a.get("title") or "").strip() for a in anns}
    state["announcement_titles"] = sorted(titles)
    for expected_absent in (FRIDAY_TITLE, MONDAY_TITLE, FAMILY_TITLE):
        if expected_absent in titles:
            blockers.append(f"DUPLICATE: announcement already exists: {expected_absent!r}")

    return state, blockers


def _verify(base_url: str, token: str, build: Any) -> dict[str, Any]:
    r: dict[str, Any] = {}
    page = _get(base_url, token, f"/api/v1/courses/{COURSE_ID}/front_page")
    body = page.get("body") or "" if isinstance(page, dict) else ""
    r["week8_badge"] = "Week 8 \u00b7 September 7\u201311, 2026" in body
    r["front_page"] = bool((page or {}).get("front_page")) if isinstance(page, dict) else False
    r["picture_day_callout"] = "Picture Day \u2014 Tuesday, September 8" in body
    r["makeup_date"] = "Make-Up Picture Day" in body and "October 20" in body
    r["birthday_tiles"] = body.count("min-width: 220px") == 3
    r["emergency_alerts"] = "Emergency Text Alerts" in body and "833-519-6279" in body
    r["carpool_update"] = (
        "initially follow the purple arrows for afternoon carpool" in body
        and "Arrival order remains fair" in body
    )

    anns = _announcements(base_url, token)
    by_title = {(a.get("title") or "").strip(): a for a in anns}

    family = by_title.get(FAMILY_TITLE)
    r["family_count"] = 1 if family else 0
    r["family_match"] = False
    if family:
        full = _get(base_url, token, f"/api/v1/courses/{COURSE_ID}/discussion_topics/{family['id']}")
        msg = (full or {}).get("message") or "" if isinstance(full, dict) else ""
        # The announcement embeds the newsletter wrapper div; strip its CSS/JS.
        wrapper = body[len(build.CSS) : -len(build.JS)]
        r["family_match"] = wrapper in msg

    def _sched(title: str, expected_at: str) -> str:
        a = by_title.get(title)
        if not a:
            return "FAIL"
        dpa = (a.get("delayed_post_at") or "")
        if dpa:
            return f"SCHEDULED ({dpa})"
        return "FAIL"

    r["friday_sched"] = _sched(FRIDAY_TITLE, FRIDAY_POST_AT)
    r["monday_sched"] = _sched(MONDAY_TITLE, MONDAY_POST_AT)
    return r


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish Q1W8 Homeroom newsletter + Picture Day reminders")
    parser.add_argument("--reconcile-only", action="store_true", help="GET-only reconcile, no writes")
    args = parser.parse_args()

    build = _load_build()
    credentials.load_credentials()
    base_url = os.environ["CANVAS_BASE_URL"].strip().rstrip("/")
    token = os.environ["CANVAS_TOKEN"]

    print("=== Q1W8 HOMEROOM — RECONCILE (GET-only) ===")
    state, blockers = _reconcile(base_url, token)
    print(f"newsletter url: {state.get('page_url')!r}")
    print(f"newsletter title: {state.get('page_title')!r}")
    print(f"front_page: {state.get('front_page')}")
    print(f"drift: {state.get('drift')}")
    print(f"existing announcements: {state.get('announcement_titles')}")

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
        print("BLOCKERS: 0")
        return 0

    print("\nRECONCILE CLEAN — proceeding to publish.")

    # Build final content from the live body (single source of truth).
    live_body = _get(base_url, token, f"/api/v1/courses/{COURSE_ID}/front_page").get("body") or ""
    new_body, _changes = build.transform(live_body)
    family_msg = build.build_family_announcement(new_body)
    friday_msg = build.announcement_message(build.FRIDAY_ANNOUNCEMENT["body_paragraphs"])
    monday_msg = build.announcement_message(build.MONDAY_ANNOUNCEMENT["body_paragraphs"])

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
        print("WRITTEN: Homeroom newsletter page (Week 8)")
    else:
        remaining.append("newsletter page update")
        print(f"BLOCKED: newsletter page ({','.join(getattr(page_res, 'blockers', []) or ['blocked'])})")

    family_res = writer.create_announcement_live(
        course_id=COURSE_ID,
        title=FAMILY_TITLE,
        message=family_msg,
        published=True,
        delayed_post_at=None,
        approved=True,
        approved_by="Owen Reagan",
    )
    if getattr(family_res, "write_status", "BLOCKED") == "WRITTEN":
        writes += 1
        print(f"WRITTEN: '{FAMILY_TITLE}'")
    else:
        remaining.append("Week 8 family announcement")
        print(f"BLOCKED: family announcement ({','.join(getattr(family_res, 'blockers', []) or ['blocked'])})")

    friday_res = writer.create_announcement_live(
        course_id=COURSE_ID,
        title=FRIDAY_TITLE,
        message=friday_msg,
        published=True,
        delayed_post_at=FRIDAY_POST_AT,
        approved=True,
        approved_by="Owen Reagan",
    )
    if getattr(friday_res, "write_status", "BLOCKED") == "WRITTEN":
        writes += 1
        print(f"WRITTEN (scheduled): '{FRIDAY_TITLE}' @ {FRIDAY_POST_AT}")
    else:
        remaining.append("Friday Picture Day reminder")
        print(f"BLOCKED: Friday reminder ({','.join(getattr(friday_res, 'blockers', []) or ['blocked'])})")

    monday_res = writer.create_announcement_live(
        course_id=COURSE_ID,
        title=MONDAY_TITLE,
        message=monday_msg,
        published=True,
        delayed_post_at=MONDAY_POST_AT,
        approved=True,
        approved_by="Owen Reagan",
    )
    if getattr(monday_res, "write_status", "BLOCKED") == "WRITTEN":
        writes += 1
        print(f"WRITTEN (scheduled): '{MONDAY_TITLE}' @ {MONDAY_POST_AT}")
    else:
        remaining.append("Monday Picture Day reminder")
        print(f"BLOCKED: Monday reminder ({','.join(getattr(monday_res, 'blockers', []) or ['blocked'])})")

    print(f"\nWRITES PERFORMED: {writes}")

    print("\n=== Q1W8 HOMEROOM — VERIFY (GET-only) ===")
    r = _verify(base_url, token, build)

    print("\n=== REPORT ===")
    print(f"Week 8 newsletter: {'LIVE' if r['week8_badge'] else 'FAIL'}")
    print(f"Homeroom front page still true: {'PASS' if r['front_page'] else 'FAIL'}")
    print(f"Week 8 family announcement: {'LIVE' if r['family_count'] == 1 else 'FAIL'}")
    print(f"Friday Picture Day reminder: {r['friday_sched']}")
    print(f"Monday Picture Day reminder: {r['monday_sched']}")
    print(f"Picture Day callout: {'PASS' if r['picture_day_callout'] else 'FAIL'}")
    print(f"Make-Up Picture Day date: {'PASS' if r['makeup_date'] else 'FAIL'}")
    print(f"birthday tiles: {'PASS' if r['birthday_tiles'] else 'FAIL'}")
    print(f"Emergency Text Alerts: {'PASS' if r['emergency_alerts'] else 'FAIL'}")
    print(f"carpool update: {'PASS' if r['carpool_update'] else 'FAIL'}")
    print(f"newsletter/Week 8 family announcement HTML match: {'PASS' if r['family_match'] else 'FAIL'}")
    print(f"WRITES PERFORMED: {writes}")
    print(f"REMAINING WRITE ACTIONS: {len(remaining)}")
    for item in remaining:
        print(f"  - {item}")
    print(f"BLOCKERS: {len(remaining)}")

    all_pass = (
        r["week8_badge"] and r["front_page"] and r["family_count"] == 1
        and r["friday_sched"].startswith("SCHEDULED")
        and r["monday_sched"].startswith("SCHEDULED")
        and r["picture_day_callout"] and r["makeup_date"] and r["birthday_tiles"]
        and r["emergency_alerts"] and r["carpool_update"] and r["family_match"]
        and not remaining
    )
    if all_pass:
        print("Q1W8 HOMEROOM NEWSLETTER + PICTURE DAY REMINDERS: COMPLETE")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
