#!/usr/bin/env python3
"""Repair Playground Picnic flyer references to Final Flyer.pdf (6185432).

Guarded workflow:
1. Unhide file 6185432 (hidden=false)
2. Repair Q1W8 rolling newsletter (flyer id + approved copy)
3. Repair 4th Grade Happenings - Week 8 in place
4. Repair three scheduled picnic reminders in place
5. Verify — zero stale 6185178 references on live objects

Usage:
    python3 scripts/canvas-llm/q1w8_playground_picnic_repair.py --reconcile-only
    CANVAS_LLM_DEPLOYMENT_MODE=live CANVAS_LLM_LIVE_Q1W2_APPROVED=1 \
        python3 scripts/canvas-llm/q1w8_playground_picnic_repair.py
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
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
from scripts.canvas_llm_phase22 import playground_picnic as picnic  # noqa: E402

BUILD = REPO_ROOT / ".local" / "canvas-llm" / "q1w8-audit" / "build_q1w8_newsletter.py"

COURSE_ID = picnic.HOMEROOM_COURSE_ID
FILE_ID = picnic.FLYER_FILE_ID
PAGE_REF = "q1w2-july-27-31-2026"
PAGE_TITLE = "Q1W2 - July 27-31, 2026"
FAMILY_TITLE = "4th Grade Happenings - Week 8"

REMINDER_IDS = {
    picnic.REMINDERS[0]["title"]: "165330",
    picnic.REMINDERS[1]["title"]: "165331",
    picnic.REMINDERS[2]["title"]: "165332",
}


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


def _put_form(base_url: str, token: str, path: str, data: dict[str, str]) -> dict[str, Any]:
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}{path}",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="PUT",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        text = response.read().decode("utf-8")
        return json.loads(text) if text else {}


def _put_json(base_url: str, token: str, path: str, data: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}{path}",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="PUT",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        text = response.read().decode("utf-8")
        return json.loads(text) if text else {}


def _course_files_root_id(base_url: str, token: str) -> str | None:
    folders = _get(base_url, token, f"/api/v1/courses/{COURSE_ID}/folders?per_page=100")
    if not isinstance(folders, list):
        return None
    for folder in folders:
        if (folder.get("full_name") or "").strip() == "course files":
            return str(folder.get("id"))
    return None


def _ensure_file_visible(base_url: str, token: str) -> tuple[bool, str]:
    """Return (ok, detail). Canvas keeps hidden=true on files inside hidden folders."""
    updated = _put_form(base_url, token, f"/api/v1/files/{FILE_ID}", {"hidden": "false"})
    if updated.get("hidden") is False:
        return True, "hidden=false on file"

    root_id = _course_files_root_id(base_url, token)
    if not root_id:
        return False, "course files root folder not found"

    moved = _put_json(
        base_url,
        token,
        f"/api/v1/files/{FILE_ID}",
        {
            "parent_folder_id": root_id,
            "hidden": False,
            "visibility_level": "inherit",
            "on_duplicate": "rename",
        },
    )
    if moved.get("hidden") is False and str(moved.get("id")) == str(FILE_ID):
        return True, f"moved to course files (folder {root_id}) with hidden=false"
    return False, f"hidden still {moved.get('hidden')!r} after move"


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


def _file_refs(body: str) -> list[str]:
    return sorted(set(re.findall(r"/files/(\d+)/", body)))


def _reconcile(base_url: str, token: str) -> tuple[dict[str, Any], list[str]]:
    blockers: list[str] = []
    state: dict[str, Any] = {}

    meta = _get(base_url, token, f"/api/v1/files/{FILE_ID}")
    if isinstance(meta, dict) and "__error__" in meta:
        blockers.append(f"Final Flyer GET failed: {meta['__error__']}")
        return state, blockers
    state["file_hidden"] = bool(meta.get("hidden"))
    state["file_name"] = meta.get("display_name")
    state["file_id"] = meta.get("id")

    page = _get(base_url, token, f"/api/v1/courses/{COURSE_ID}/front_page")
    if isinstance(page, dict) and "__error__" in page:
        blockers.append(f"newsletter GET failed: {page['__error__']}")
        return state, blockers
    body = page.get("body") or ""
    state["week8_badge"] = "Week 8 \u00b7 September 7\u201311, 2026" in body
    state["front_page"] = bool(page.get("front_page"))
    state["newsletter_refs"] = _file_refs(body)
    state["stale_in_newsletter"] = str(picnic.STALE_FLYER_FILE_ID) in body

    if not state["week8_badge"]:
        blockers.append("DRIFT: newsletter missing Week 8 badge")
    if not state["front_page"]:
        blockers.append("DRIFT: newsletter not front_page=true")
    if picnic.SECTION_MARKER not in body:
        blockers.append("DRIFT: Playground Picnic section missing")

    anns = _announcements(base_url, token)
    by_title = {(a.get("title") or "").strip(): a for a in anns}
    family = by_title.get(FAMILY_TITLE)
    state["family_id"] = family.get("id") if family else None
    if not family:
        blockers.append(f"MISSING: {FAMILY_TITLE!r}")

    for title, expected_id in REMINDER_IDS.items():
        ann = by_title.get(title)
        if not ann:
            blockers.append(f"MISSING: reminder {title!r}")
        elif str(ann.get("id")) != expected_id:
            blockers.append(f"DRIFT: {title!r} id mismatch (expected {expected_id})")

    return state, blockers


def _verify(base_url: str, token: str, build: Any, expected_schedules: dict[str, str]) -> dict[str, Any]:
    r: dict[str, Any] = {}
    meta = _get(base_url, token, f"/api/v1/files/{FILE_ID}")
    r["visibility"] = (
        meta.get("hidden") is False
        and meta.get("display_name") == picnic.FLYER_DISPLAY_NAME
        and meta.get("id") == FILE_ID
    )

    page = _get(base_url, token, f"/api/v1/courses/{COURSE_ID}/front_page")
    body = page.get("body") or "" if isinstance(page, dict) else ""
    r["newsletter"] = (
        str(FILE_ID) in _file_refs(body)
        and str(picnic.STALE_FLYER_FILE_ID) not in body
        and picnic.APPROVED_PICNIC_COPY in body
        and bool((page or {}).get("front_page"))
    )

    anns = _announcements(base_url, token)
    by_title = {(a.get("title") or "").strip(): a for a in anns}

    family = by_title.get(FAMILY_TITLE)
    r["family"] = False
    if family:
        full = _get(base_url, token, f"/api/v1/courses/{COURSE_ID}/discussion_topics/{family['id']}")
        msg = (full or {}).get("message") or "" if isinstance(full, dict) else ""
        wrapper = body[len(build.CSS) : -len(build.JS)]
        r["family"] = (
            wrapper in msg
            and str(FILE_ID) in _file_refs(msg)
            and str(picnic.STALE_FLYER_FILE_ID) not in msg
        )

    def _rem(title: str) -> bool:
        a = by_title.get(title)
        if not a:
            return False
        full = _get(base_url, token, f"/api/v1/courses/{COURSE_ID}/discussion_topics/{a['id']}")
        msg = (full or {}).get("message") or "" if isinstance(full, dict) else ""
        sched_ok = (a.get("delayed_post_at") or "") == expected_schedules.get(title, "")
        return (
            sched_ok
            and str(FILE_ID) in _file_refs(msg)
            and str(picnic.STALE_FLYER_FILE_ID) not in msg
        )

    r["rem1"] = _rem(picnic.REMINDERS[0]["title"])
    r["rem2"] = _rem(picnic.REMINDERS[1]["title"])
    r["rem3"] = _rem(picnic.REMINDERS[2]["title"])

    stale_live = 0
    for obj in [body]:
        stale_live += obj.count(str(picnic.STALE_FLYER_FILE_ID))
    for title in list(REMINDER_IDS) + [FAMILY_TITLE]:
        a = by_title.get(title)
        if a:
            full = _get(base_url, token, f"/api/v1/courses/{COURSE_ID}/discussion_topics/{a['id']}")
            msg = (full or {}).get("message") or "" if isinstance(full, dict) else ""
            stale_live += msg.count(str(picnic.STALE_FLYER_FILE_ID))
    r["stale_live_count"] = stale_live

    files = _get(base_url, token, f"/api/v1/courses/{COURSE_ID}/files?per_page=100")
    picnic_files = [
        f for f in (files if isinstance(files, list) else [])
        if "flyer" in (f.get("display_name") or "").lower() or "picnic" in (f.get("display_name") or "").lower()
    ]
    r["duplicate_media"] = len(picnic_files)
    return r


def main() -> int:
    parser = argparse.ArgumentParser(description="Repair Playground Picnic flyer to Final Flyer.pdf")
    parser.add_argument("--reconcile-only", action="store_true")
    args = parser.parse_args()

    build = _load_build()
    credentials.load_credentials()
    base_url = os.environ["CANVAS_BASE_URL"].strip().rstrip("/")
    token = os.environ["CANVAS_TOKEN"]

    print("=== PLAYGROUND PICNIC REPAIR — RECONCILE (GET-only) ===")
    state, blockers = _reconcile(base_url, token)
    print(f"Final Flyer id={state.get('file_id')} hidden={state.get('file_hidden')} name={state.get('file_name')!r}")
    print(f"newsletter refs={state.get('newsletter_refs')} stale_6185178={state.get('stale_in_newsletter')}")
    print(f"front_page={state.get('front_page')} week8={state.get('week8_badge')}")

    if blockers:
        print("\nBLOCKERS:")
        for b in blockers:
            print(f"  - {b}")
        print("WRITES PERFORMED: 0")
        return 1

    if args.reconcile_only:
        print("\nRECONCILE CLEAN — no writes performed (--reconcile-only).")
        print("WRITES PERFORMED: 0")
        print("BLOCKERS: 0")
        return 0

    os.environ["CANVAS_LLM_DEPLOYMENT_MODE"] = "live"
    os.environ["CANVAS_LLM_LIVE_Q1W2_APPROVED"] = "1"

    writes = 0
    remaining: list[str] = []
    expected_schedules: dict[str, str] = {}

    # Step 1 — visibility
    if state.get("file_hidden"):
        ok, detail = _ensure_file_visible(base_url, token)
        if not ok:
            remaining.append("file visibility")
            print(f"BLOCKED: file visibility ({detail})")
        else:
            writes += 1
            print(f"WRITTEN: Final Flyer.pdf visible — {detail} (id {FILE_ID})")
    else:
        print("SKIP: Final Flyer.pdf already hidden=false")

    meta = _get(base_url, token, f"/api/v1/files/{FILE_ID}")
    print(
        f"VERIFY file: hidden={meta.get('hidden')} id={meta.get('id')} "
        f"name={meta.get('display_name')!r}"
    )

    # Step 2 — newsletter
    page = _get(base_url, token, f"/api/v1/courses/{COURSE_ID}/front_page")
    live_body = page.get("body") or ""
    new_body = picnic.repair_picnic_content(live_body)

    if new_body != live_body:
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
            print("WRITTEN: rolling newsletter repaired")
        else:
            remaining.append("newsletter repair")
            print(f"BLOCKED: newsletter ({','.join(getattr(page_res, 'blockers', []) or ['blocked'])})")
    else:
        print("SKIP: newsletter already repaired")
        new_body = live_body

    # Step 3 — family announcement
    family_msg = build.build_family_announcement(new_body)
    ann_res = writer.update_announcement_live(
        course_id=COURSE_ID,
        topic_id=str(state["family_id"]),
        title=FAMILY_TITLE,
        message=family_msg,
        published=None,
        approved=True,
        approved_by="Owen Reagan",
    )
    if getattr(ann_res, "write_status", "BLOCKED") == "WRITTEN":
        writes += 1
        print(f"WRITTEN: '{FAMILY_TITLE}' synced in place")
    else:
        remaining.append("Week 8 family announcement")
        print(f"BLOCKED: family announcement ({','.join(getattr(ann_res, 'blockers', []) or ['blocked'])})")

    # Step 4 — reminders
    anns = _announcements(base_url, token)
    by_title = {(a.get("title") or "").strip(): a for a in anns}
    for rem in picnic.REMINDERS:
        title = rem["title"]
        ann = by_title.get(title)
        if not ann:
            remaining.append(title)
            continue
        expected_schedules[title] = ann.get("delayed_post_at") or rem["delayed_post_at"]
        full = _get(base_url, token, f"/api/v1/courses/{COURSE_ID}/discussion_topics/{ann['id']}")
        msg = full.get("message") or ""
        repaired_msg = picnic.repair_flyer_references(msg)
        if repaired_msg == msg and str(FILE_ID) in _file_refs(msg):
            print(f"SKIP: '{title}' already repaired")
            continue
        res = writer.update_announcement_live(
            course_id=COURSE_ID,
            topic_id=str(ann["id"]),
            title=title,
            message=repaired_msg,
            published=None,
            approved=True,
            approved_by="Owen Reagan",
        )
        if getattr(res, "write_status", "BLOCKED") == "WRITTEN":
            writes += 1
            print(f"WRITTEN: '{title}' repaired in place")
        else:
            remaining.append(title)
            print(f"BLOCKED: {title} ({','.join(getattr(res, 'blockers', []) or ['blocked'])})")

    print(f"\nWRITES PERFORMED: {writes}")

    print("\n=== PLAYGROUND PICNIC REPAIR — VERIFY (GET-only) ===")
    r = _verify(base_url, token, build, expected_schedules)

    print("\n=== REPORT ===")
    print(f"Final Flyer visibility: {'PASS' if r['visibility'] else 'FAIL'}")
    print(f"Q1W8 newsletter repair: {'PASS' if r['newsletter'] else 'FAIL'}")
    print(f"Week 8 family announcement repair: {'PASS' if r['family'] else 'FAIL'}")
    print(f"Sept. 4 reminder repair: {'PASS' if r['rem1'] else 'FAIL'}")
    print(f"Sept. 11 reminder repair: {'PASS' if r['rem2'] else 'FAIL'}")
    print(f"Sept. 16 reminder repair: {'PASS' if r['rem3'] else 'FAIL'}")
    print(f"stale live references to 6185178: {r['stale_live_count']}")
    print(f"duplicate media count: {r['duplicate_media']}")
    print(f"WRITES PERFORMED: {writes}")
    print(f"REMAINING WRITE ACTIONS: {len(remaining)}")
    for item in remaining:
        print(f"  - {item}")
    print(f"BLOCKERS: {len(remaining)}")

    all_pass = (
        r["visibility"] and r["newsletter"] and r["family"]
        and r["rem1"] and r["rem2"] and r["rem3"]
        and r["stale_live_count"] == 0 and r["duplicate_media"] == 1
        and not remaining
    )
    if all_pass:
        print("FINAL PLAYGROUND PICNIC FLYER REPAIR: COMPLETE")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
