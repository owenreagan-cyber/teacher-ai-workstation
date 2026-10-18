#!/usr/bin/env python3
"""Publish the Playground Picnic communication plan to Homeroom Canvas.

Updates the live Week 8 rolling newsletter (and syncs the Week 8 family
announcement), then creates three scheduled picnic reminder announcements.
Reuses the existing Canvas-hosted flyer; no duplicate media uploads.

Usage:
    python3 scripts/canvas-llm/q1w8_playground_picnic_publish.py --reconcile-only
    CANVAS_LLM_DEPLOYMENT_MODE=live CANVAS_LLM_LIVE_Q1W2_APPROVED=1 \
        python3 scripts/canvas-llm/q1w8_playground_picnic_publish.py
"""
from __future__ import annotations

import argparse
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
from scripts.canvas_llm_phase22 import playground_picnic as picnic  # noqa: E402

BUILD = REPO_ROOT / ".local" / "canvas-llm" / "q1w8-audit" / "build_q1w8_newsletter.py"

COURSE_ID = picnic.HOMEROOM_COURSE_ID
PAGE_REF = "q1w2-july-27-31-2026"
PAGE_TITLE = "Q1W2 - July 27-31, 2026"
FAMILY_TITLE = "4th Grade Happenings - Week 8"


def _load_build() -> Any:
    spec = importlib.util.spec_from_file_location("build_q1w8_newsletter", BUILD)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


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
        blockers.append(f"Homeroom newsletter GET failed: {page['__error__']}")
        return state, blockers

    body = page.get("body") or ""
    state["picnic_present"] = picnic.has_picnic_section(body)
    state["week8_badge"] = "Week 8 \u00b7 September 7\u201311, 2026" in body
    state["front_page"] = bool(page.get("front_page"))

    if not state["week8_badge"]:
        blockers.append("DRIFT: live newsletter is not on Week 8 badge (unexpected state)")

    anns = _announcements(base_url, token)
    by_title = {(a.get("title") or "").strip(): a for a in anns}
    state["announcement_titles"] = sorted(by_title.keys())

    for rem in picnic.REMINDERS:
        title = rem["title"]
        if title in by_title:
            blockers.append(f"DUPLICATE: picnic reminder already exists: {title!r}")

    family = by_title.get(FAMILY_TITLE)
    state["family_id"] = family.get("id") if family else None
    if not family:
        blockers.append(f"MISSING: family announcement not found: {FAMILY_TITLE!r}")

    return state, blockers


def _verify(base_url: str, token: str, build: Any) -> dict[str, Any]:
    r: dict[str, Any] = {}
    page = _get(base_url, token, f"/api/v1/courses/{COURSE_ID}/front_page")
    body = page.get("body") or "" if isinstance(page, dict) else ""
    r["week8_picnic"] = picnic.has_picnic_section(body)
    r["front_page"] = bool((page or {}).get("front_page")) if isinstance(page, dict) else False
    r["flyer_reused"] = str(picnic.FLYER_FILE_ID) in body and picnic.FLYER_PREVIEW_URL in body

    anns = _announcements(base_url, token)
    by_title = {(a.get("title") or "").strip(): a for a in anns}

    family = by_title.get(FAMILY_TITLE)
    r["family_sync"] = False
    if family:
        full = _get(base_url, token, f"/api/v1/courses/{COURSE_ID}/discussion_topics/{family['id']}")
        msg = (full or {}).get("message") or "" if isinstance(full, dict) else ""
        wrapper = body[len(build.CSS) : -len(build.JS)]
        r["family_sync"] = wrapper in msg and picnic.has_picnic_section(msg)

    def _sched(title: str) -> str:
        a = by_title.get(title)
        if not a:
            return "FAIL"
        dpa = a.get("delayed_post_at") or ""
        if dpa:
            return f"SCHEDULED ({dpa})"
        return "FAIL"

    r["reminder_1"] = _sched(picnic.REMINDERS[0]["title"])
    r["reminder_2"] = _sched(picnic.REMINDERS[1]["title"])
    r["reminder_3"] = _sched(picnic.REMINDERS[2]["title"])
    return r


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish Playground Picnic communication plan")
    parser.add_argument("--reconcile-only", action="store_true")
    args = parser.parse_args()

    build = _load_build()
    credentials.load_credentials()
    base_url = os.environ["CANVAS_BASE_URL"].strip().rstrip("/")
    token = os.environ["CANVAS_TOKEN"]

    print("=== PLAYGROUND PICNIC — RECONCILE (GET-only) ===")
    state, blockers = _reconcile(base_url, token)
    print(f"week8 badge ok: {state.get('week8_badge')}")
    print(f"picnic already in newsletter: {state.get('picnic_present')}")
    print(f"front_page: {state.get('front_page')}")
    print(f"family announcement id: {state.get('family_id')}")

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

    page = _get(base_url, token, f"/api/v1/courses/{COURSE_ID}/front_page")
    live_body = page.get("body") or ""
    new_body = picnic.add_picnic_section(live_body)
    family_msg = build.build_family_announcement(new_body)

    writes = 0
    remaining: list[str] = []

    if not state.get("picnic_present"):
        page_res = writer.update_page_live(
            course_id=COURSE_ID,
            page_ref=PAGE_REF,
            title=PAGE_TITLE,
            body=new_body,
            published=True,
            front_page=None,
            approved=True,
            approved_by="Owen Reagan",
        )
        if getattr(page_res, "write_status", "BLOCKED") == "WRITTEN":
            writes += 1
            print("WRITTEN: Homeroom newsletter (Playground Picnic section added)")
        else:
            remaining.append("newsletter page update")
            print(f"BLOCKED: newsletter ({','.join(getattr(page_res, 'blockers', []) or ['blocked'])})")
    else:
        print("SKIP: picnic section already present in newsletter")
        new_body = live_body

    ann_res = writer.update_announcement_live(
        course_id=COURSE_ID,
        topic_id=str(state["family_id"]),
        title=FAMILY_TITLE,
        message=build.build_family_announcement(new_body),
        published=None,
        approved=True,
        approved_by="Owen Reagan",
    )
    if getattr(ann_res, "write_status", "BLOCKED") == "WRITTEN":
        writes += 1
        print(f"WRITTEN: '{FAMILY_TITLE}' synced in place")
    else:
        remaining.append("Week 8 family announcement sync")
        print(f"BLOCKED: family announcement ({','.join(getattr(ann_res, 'blockers', []) or ['blocked'])})")

    for rem in picnic.REMINDERS:
        msg = picnic.build_reminder_message(rem["paragraphs"])
        res = writer.create_announcement_live(
            course_id=COURSE_ID,
            title=rem["title"],
            message=msg,
            published=True,
            delayed_post_at=rem["delayed_post_at"],
            approved=True,
            approved_by="Owen Reagan",
        )
        if getattr(res, "write_status", "BLOCKED") == "WRITTEN":
            writes += 1
            print(f"WRITTEN (scheduled): '{rem['title']}' @ {rem['delayed_post_at']}")
        else:
            remaining.append(rem["title"])
            print(f"BLOCKED: {rem['title']} ({','.join(getattr(res, 'blockers', []) or ['blocked'])})")

    print(f"\nWRITES PERFORMED: {writes}")

    print("\n=== PLAYGROUND PICNIC — VERIFY (GET-only) ===")
    r = _verify(base_url, token, build)

    print("\n=== REPORT ===")
    print(f"Week 8 newsletter picnic section: {'LIVE' if r['week8_picnic'] else 'FAIL'}")
    print(f"Week 8 family announcement synced: {'PASS' if r['family_sync'] else 'FAIL'}")
    print(f"Sept 4 picnic reminder: {r['reminder_1']}")
    print(f"Sept 11 picnic reminder: {r['reminder_2']}")
    print(f"Sept 16 picnic reminder: {r['reminder_3']}")
    print(f"existing flyer reused: {'PASS' if r['flyer_reused'] else 'FAIL'}")
    print("duplicate media created: 0")
    print(f"WRITES PERFORMED: {writes}")
    print(f"REMAINING WRITE ACTIONS: {len(remaining)}")
    for item in remaining:
        print(f"  - {item}")
    print(f"BLOCKERS: {len(remaining)}")

    all_pass = (
        r["week8_picnic"] and r["family_sync"] and r["flyer_reused"]
        and r["reminder_1"].startswith("SCHEDULED")
        and r["reminder_2"].startswith("SCHEDULED")
        and r["reminder_3"].startswith("SCHEDULED")
        and not remaining
    )
    if all_pass:
        print("PLAYGROUND PICNIC COMMUNICATION PLAN: COMPLETE")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
