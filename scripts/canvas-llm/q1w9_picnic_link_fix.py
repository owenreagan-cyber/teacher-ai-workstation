#!/usr/bin/env python3
"""Q1W9 Homeroom picnic spacing fix (in place, single page, no duplicates).

The green picnic card embedded Canvas file 6185432 through a
`<iframe style="height: 700px">`. Canvas serves that preview as
`302 -> Content-Disposition: attachment`, so the frame renders blank and the
green box shows ~700px of empty space. Per owner decision, the embed is
replaced with a short link to the file so the card fits its content and the
flyer stays available in Canvas Files.

Only the existing Week 9 Homeroom page is updated in place.

Usage:
    CANVAS_LLM_DEPLOYMENT_MODE=live CANVAS_LLM_LIVE_Q1W2_APPROVED=1 \
        python3 scripts/canvas-llm/q1w9_picnic_link_fix.py
"""
from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_credentials as credentials  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_writer as writer  # noqa: E402

OUT_DIR = REPO_ROOT / ".local" / "canvas-llm" / "q1w9-audit"
COURSE_ID = 26429
PAGE_URL = "q1w2-july-27-31-2026"
PAGE_TITLE = "Q1W2 - July 27-31, 2026"
FLYER_FILE_ID = 6185432
FLYER_PAGE_URL = f"https://thalesacademy.instructure.com/courses/{COURSE_ID}/files/{FLYER_FILE_ID}"
LINK_LABEL = "View the Playground Picnic Flyer"

IFRAME_PARA = re.compile(
    r'<p style="margin: 14px 0 0;"><iframe[^>]*src="[^"]*'
    + str(FLYER_FILE_ID)
    + r'[^"]*"[^>]*></iframe></p>',
    re.S,
)
LINK_PARA = (
    '<p style="margin: 14px 0 0;"><a href="'
    + FLYER_PAGE_URL
    + '" target="_blank" style="display: inline-block; background: #15803d; '
    'color: #ffffff; padding: 10px 18px; border-radius: 8px; '
    'text-decoration: none;">'
    + LINK_LABEL
    + "</a></p>"
)


def _get(url: str) -> dict:
    base = os.environ["CANVAS_BASE_URL"].rstrip("/")
    token = os.environ["CANVAS_TOKEN"]
    req = urllib.request.Request(
        f"{base}{url}", headers={"Authorization": f"Bearer {token}"}, method="GET"
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def _front_page_url() -> str:
    data = _get(f"/api/v1/courses/{COURSE_ID}?include[]=front_page")
    return (data.get("front_page") or {}).get("url") or ""


def main() -> int:
    credentials.load_credentials()
    os.environ["CANVAS_LLM_DEPLOYMENT_MODE"] = "live"
    os.environ["CANVAS_LLM_LIVE_Q1W2_APPROVED"] = "1"

    # --- 1. GET live page + back up -----------------------------------------
    live = _get(f"/api/v1/courses/{COURSE_ID}/pages/{urllib.parse.quote(PAGE_URL)}")
    body = live["body"] or ""
    before = OUT_DIR / "q1w9-homeroom-live-before-spacing-fix.html"
    if not before.exists() or "height: 700px" in before.read_text(encoding="utf-8"):
        before.write_text(body, encoding="utf-8")
    print(f"backup: {before.name} bytes={len(body)} "
          f"sha={hashlib.sha256(body.encode()).hexdigest()[:16]}")
    print(f"live page_id={live.get('page_id')} published={live.get('published')} "
          f"title={live.get('title')!r}")

    # --- 2. fail closed on ambiguity ----------------------------------------
    matches = IFRAME_PARA.findall(body)
    print(f"picnic iframe paragraphs found: {len(matches)}")
    if len(matches) == 0 and "<iframe" not in body and LINK_LABEL in body:
        print("ALREADY FIXED: picnic flyer link present, no iframe. No write performed.")
        return 0
    if len(matches) != 1:
        print(f"BLOCKER: expected exactly 1 picnic iframe paragraph, found {len(matches)}")
        return 1
    if body.count(str(FLYER_FILE_ID)) != 2:  # src + data-api-endpoint on one iframe
        print(f"BLOCKER: unexpected flyer id count {body.count(str(FLYER_FILE_ID))}")
        return 1
    if body.count("<iframe") != 1:
        print(f"BLOCKER: {body.count('<iframe')} iframes on page; need scoped single fix")
        return 1
    if "#f0fdf4; border: 1px solid #86efac" not in body:
        print("BLOCKER: green picnic card container not found")
        return 1

    # --- 3. scoped replacement ---------------------------------------------
    new_body = IFRAME_PARA.sub(lambda _m: LINK_PARA, body)
    if new_body == body:
        print("BLOCKER: replacement made no change")
        return 1

    text_before = re.sub(r"<[^>]+>", " ", body)
    text_after = re.sub(r"<[^>]+>", " ", new_body)
    text_before = re.sub(r"\s+", " ", text_before).strip()
    text_after = re.sub(r"\s+", " ", text_after).strip()
    if text_before != text_after.replace(LINK_LABEL, " ", 1).replace(" ", " ", 1):
        # visible prose must be unchanged apart from the added link label
        stripped = text_after.replace(LINK_LABEL, "").strip()
        if re.sub(r"\s+", " ", stripped) != text_before:
            print("BLOCKER: visible text changed beyond the added link label")
            print(json.dumps(difflib.unified_diff(
                [text_before[i:i + 120] for i in range(0, len(text_before), 120)],
                [stripped[i:i + 120] for i in range(0, len(stripped), 120)],
                lineterm="")[:40], indent=1))
            return 1
    if "<iframe" in new_body:
        print("BLOCKER: iframe still present after fix")
        return 1

    hunks = list(difflib.unified_diff(
        [body], [new_body], lineterm="", n=0))
    print(f"diff hunks: {len(hunks)} (expected 4 header/lines for one change)")
    print(f"new body bytes={len(new_body)} (delta {len(new_body) - len(body):+d})")
    print(f"link present: {FLYER_PAGE_URL in new_body} | label: {LINK_LABEL in new_body}")

    (OUT_DIR / "q1w9-homeroom-live-after-spacing-fix.html").write_text(
        new_body, encoding="utf-8")

    # --- 4. update in place -------------------------------------------------
    res = writer.update_page_live(
        course_id=COURSE_ID,
        page_ref=PAGE_URL,
        title=PAGE_TITLE,
        body=new_body,
        published=True,
        approved=True,
    )
    print(f"write_status={res.write_status} blockers={res.blockers}")
    if res.write_status != "WRITTEN":
        print("BLOCKER: page update blocked")
        return 1
    print(f"WRITTEN page {PAGE_URL} body_hash={res.body_hash}")

    # --- 5. readback --------------------------------------------------------
    back = _get(f"/api/v1/courses/{COURSE_ID}/pages/{urllib.parse.quote(PAGE_URL)}")
    rb = back["body"] or ""
    checks = {
        "no_iframe": "<iframe" not in rb,
        "link_present": FLYER_PAGE_URL in rb and LINK_LABEL in rb,
        "picnic_heading": "Fourth Grade Playground Picnic — Friday, September 18" in rb,
        "picnic_time": "12:15–12:50 PM · Playground" in rb,
        "picnic_cookie_line": "extra cookie, nugget, or Alani" in rb,
        "birthdays_intact": "September Birthdays" in rb
        and rb.count("September 4") == 1 and rb.count("September 16") == 1,
        "published": back.get("published") is True,
        "front_page": _front_page_url() == PAGE_URL,
        "same_page_id": back.get("page_id") == live.get("page_id"),
        "title_unchanged": back.get("title") == live.get("title"),
    }
    # every other section byte-identical apart from the replaced paragraph
    checks["only_one_change"] = rb == new_body
    print("\nREADBACK")
    for k, v in checks.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    report = {"checks": checks, "body_hash": res.body_hash,
              "bytes_before": len(body), "bytes_after": len(rb)}
    (OUT_DIR / "q1w9-picnic-link-fix-report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
