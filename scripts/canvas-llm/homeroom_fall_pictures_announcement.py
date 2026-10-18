#!/usr/bin/env python3
"""Publish the Homeroom "Fall Pictures & Class Photos" announcement (immediate).

Single CREATE into Homeroom (course 26429). No existing announcement is touched.
Fails closed if an exact title or equivalent body already exists.

Usage:
    CANVAS_LLM_DEPLOYMENT_MODE=live CANVAS_LLM_LIVE_Q1W2_APPROVED=1 \
        python3 scripts/canvas-llm/homeroom_fall_pictures_announcement.py
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_credentials as credentials  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_writer as writer  # noqa: E402

OUT_DIR = REPO_ROOT / ".local" / "canvas-llm" / "q1w9-audit"
COURSE_ID = 26429
TITLE = "Fall Pictures & Class Photos"

WRAP_LINK = (
    '<link rel="stylesheet" href="https://instructure-uploads.s3.amazonaws.com/'
    'account_111510000000000001/attachments/219636/canvas_global_app.css">'
)
WRAP_SCRIPT = (
    '<script src="https://instructure-uploads.s3.amazonaws.com/'
    'account_111510000000000001/attachments/219635/canvas_global_app.js"></script>'
)

PARAGRAPHS = [
    "Families,",
    "Fall pictures and class photographs were sent home today. Please take a moment "
    "to look through them when you see your child\u2019s backpack this afternoon.",
    "If you would like to purchase either the class photo or individual prints, all "
    "orders and payments should be completed through www.strawbridge.net.",
    "Any photographs that you do not plan to purchase should be returned to me.",
    "If you would like your child to have a retake, please email me so I can make "
    "note of it.",
    "Thank you!",
]
MESSAGE = WRAP_LINK + "\n" + "\n".join(f"<p>{p}</p>" for p in PARAGRAPHS) + "\n" + WRAP_SCRIPT


def _get(path: str) -> dict:
    base = os.environ["CANVAS_BASE_URL"].rstrip("/")
    token = os.environ["CANVAS_TOKEN"]
    req = urllib.request.Request(
        f"{base}{path}", headers={"Authorization": f"Bearer {token}"}, method="GET"
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def _list_announcements(course_id: int) -> list[dict]:
    base = os.environ["CANVAS_BASE_URL"].rstrip("/")
    token = os.environ["CANVAS_TOKEN"]
    url = f"{base}/api/v1/courses/{course_id}/discussion_topics?only_announcements=true&per_page=100"
    items: list[dict] = []
    while url:
        req = urllib.request.Request(
            url, headers={"Authorization": f"Bearer {token}"}, method="GET"
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            items += json.loads(resp.read().decode())
            link = resp.headers.get("Link", "")
        url = None
        for part in link.split(","):
            if 'rel="next"' in part:
                url = part[part.find("<") + 1 : part.find(">")]
    return items


def _norm_text(raw: str) -> str:
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw or "", flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def main() -> int:
    credentials.load_credentials()
    os.environ["CANVAS_LLM_DEPLOYMENT_MODE"] = "live"
    os.environ["CANVAS_LLM_LIVE_Q1W2_APPROVED"] = "1"

    # --- 1. duplicate check (fail closed) -----------------------------------
    existing = _list_announcements(COURSE_ID)
    title_hits = [a for a in existing if (a.get("title") or "").strip() == TITLE]
    body_hits = []
    for a in existing:
        detail = _get(f"/api/v1/courses/{COURSE_ID}/discussion_topics/{a['id']}?include[]=body")
        if _norm_text(detail.get("message") or "") == _norm_text(MESSAGE):
            body_hits.append(a["id"])
    # cross-course title sweep
    cross = []
    for cid in (26404, 26442, 26444, 26446):
        try:
            cross += [
                (cid, a["id"])
                for a in _list_announcements(cid)
                if (a.get("title") or "").strip() == TITLE
            ]
        except Exception as exc:  # non-Homeroom course is informative only
            print(f"note: cross-course check skipped for {cid}: {exc}")
    print(f"existing Homeroom announcements: {len(existing)}")
    print(f"exact-title matches (Homeroom): {[a['id'] for a in title_hits]}")
    print(f"equivalent-body matches (Homeroom): {body_hits}")
    print(f"exact-title matches (other courses): {cross}")
    if title_hits or body_hits or cross:
        print("BLOCKER: duplicate announcement already exists; no write performed")
        return 1

    # --- 2. create immediately ----------------------------------------------
    res = writer.create_announcement_live(
        course_id=COURSE_ID,
        title=TITLE,
        message=MESSAGE,
        published=True,
        delayed_post_at=None,
        approved=True,
    )
    print(f"write_status={res.write_status} blockers={res.blockers}")
    if res.write_status != "WRITTEN":
        print("BLOCKER: announcement create blocked")
        return 1
    new_id = res.target_id
    print(f"CREATED announcement id={new_id} title={TITLE!r}")

    # --- 3. readback --------------------------------------------------------
    live = _get(f"/api/v1/courses/{COURSE_ID}/discussion_topics/{new_id}?include[]=body")
    course = _get(f"/api/v1/courses/{COURSE_ID}")
    rb = live.get("message") or ""
    checks = {
        "exists_in_course": (live.get("course_id") or COURSE_ID) == COURSE_ID,
        "course_name": course.get("name"),
        "title_exact": live.get("title") == TITLE,
        "body_exact": rb == MESSAGE,
        "body_text_exact": _norm_text(rb) == _norm_text(MESSAGE),
        "published": live.get("published") is True,
        "not_scheduled": not live.get("delayed_post_at"),
        "posted_now": bool(live.get("posted_at")),
        "no_wrapper_loss": WRAP_LINK in rb and WRAP_SCRIPT in rb,
        "unique_title_count": sum(
            1 for a in _list_announcements(COURSE_ID) if (a.get("title") or "").strip() == TITLE
        ),
    }
    print("\nREADBACK")
    for k, v in checks.items():
        ok = v is True or (k == "course_name" and v) or (k == "unique_title_count" and v == 1)
        print(f"  {'PASS' if ok else 'FAIL'}  {k}: {v}")
    ok_all = (
        checks["exists_in_course"]
        and checks["title_exact"]
        and checks["body_exact"]
        and checks["published"]
        and checks["not_scheduled"]
        and checks["posted_now"]
        and checks["no_wrapper_loss"]
        and checks["unique_title_count"] == 1
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "homeroom-fall-pictures-announcement.json").write_text(
        json.dumps(
            {
                "announcement_id": new_id,
                "title": TITLE,
                "message": MESSAGE,
                "posted_at": live.get("posted_at"),
                "published": live.get("published"),
                "delayed_post_at": live.get("delayed_post_at"),
                "checks": checks,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nannouncement id: {new_id}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
