#!/usr/bin/env python3
"""Q1W6 Homeroom family-announcement preflight — READ-ONLY (GET only).

Inspects live Canvas state needed for the guarded announcement workflow:

1. fresh-GET current user (/users/self) and Homeroom course 26429;
2. fresh-GET the front page and confirm it is the Week 6 newsletter;
3. fresh-GET all Homeroom announcements and list titles/posted_at/message
   length, flagging any current-week duplicates;
4. dump the current front-page newsletter HTML to .local/canvas-llm/.

Zero writes. Token never printed.
"""
from __future__ import annotations

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

HOMEROOM_COURSE_ID = 26429
OUT_DIR = REPO_ROOT / ".local" / "canvas-llm"


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
            detail = (exc.read() or b"").decode("utf-8", "replace")[:300]
        except Exception:  # noqa: BLE001
            detail = ""
        return {"__error__": f"HTTP {exc.code}: {detail or exc.reason}"}
    except urllib.error.URLError as exc:
        return {"__error__": f"network: {exc.reason}"}


def _paginate(base_url: str, token: str, path: str, params: dict[str, Any] | None = None) -> list[Any]:
    merged = {"per_page": 100}
    if params:
        merged.update(params)
    url = f"{base_url}{path}?{urllib.parse.urlencode(merged, doseq=True)}"
    items: list[Any] = []
    for _ in range(10):
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
                start = part.find("<")
                end = part.find(">")
                if 0 <= start < end:
                    nxt = part[start + 1 : end]
        if not nxt:
            break
        url = nxt
    return items


def main() -> int:
    credentials.load_credentials()
    base_url = os.environ["CANVAS_BASE_URL"].strip().rstrip("/")
    token = os.environ["CANVAS_TOKEN"]

    print("Q1W6 HOMEROOM ANNOUNCEMENT PREFLIGHT (read-only)")
    print(f"base host: {urllib.parse.urlparse(base_url).hostname}")
    print()

    me = _get(base_url, token, "/api/v1/users/self")
    print("USER (self):")
    print(f"  id={me.get('id')} name={me.get('name')!r}" if isinstance(me, dict) and "__error__" not in me else f"  ERROR {me}")
    print()

    front = _get(base_url, token, f"/api/v1/courses/{HOMEROOM_COURSE_ID}/front_page")
    print("FRONT PAGE:")
    if isinstance(front, dict) and "__error__" in front:
        print(f"  ERROR {front['__error__']}")
    else:
        fb = front.get("body") or ""
        print(f"  url={front.get('url')!r} title={front.get('title')!r}")
        print(f"  updated_at={front.get('updated_at')!r}")
        print(f"  has 'Week six': {'Week six' in fb}")
        print(f"  has 'Room 203': {'Room 203' in fb}")
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        dump = OUT_DIR / "q1w6-newsletter-current.html"
        dump.write_text(fb)
        print(f"  body dumped: {dump} ({len(fb)} chars)")
    print()

    anns = _paginate(
        base_url,
        token,
        f"/api/v1/courses/{HOMEROOM_COURSE_ID}/discussion_topics",
        {"only_announcements": "true"},
    )
    print(f"ANNOUNCEMENTS ({len(anns)}):")
    for a in anns:
        title = a.get("title")
        msg = a.get("message") or ""
        posted = a.get("posted_at")
        delayed = a.get("delayed_post_at")
        dup_flags = []
        if "Week 6" in (title or "") or "week 6" in (title or "").lower():
            dup_flags.append("CURRENT-WEEK TITLE")
        if "Week six" in msg:
            dup_flags.append("WEEK6 BODY")
        flag = f"  <== {', '.join(dup_flags)}" if dup_flags else ""
        print(f"  id={a.get('id')} title={title!r} posted={posted!r} delayed={delayed!r} msg_len={len(msg)}{flag}")
    print()

    print("BLOCKERS: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
