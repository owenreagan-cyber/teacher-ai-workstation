#!/usr/bin/env python3
"""Q1W6 Homeroom preflight — READ-ONLY (GET only, zero Canvas writes).

Verifies the guarded-workflow preconditions for the Week 6 Homeroom newsletter
update without writing anything:

1. fresh-GET the current authenticated user (/users/self);
2. fresh-GET Homeroom course 26429;
3. fresh-GET the current user's enrollment (Teacher-level write access);
4. fresh-GET the front page and full page list;
5. identify the last correct HTML newsletter page (``Hound Families`` marker);
6. dump that page's full existing HTML to ``.local/canvas-llm/`` for inspection.

Credentials are resolved by ``canvas_credentials.load_credentials()`` (env-first,
then the 0600 private config). The token is never printed.
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
NEWSLETTER_MARKER = "Hound Families"
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


def _paginate(base_url: str, token: str, path: str) -> list[Any]:
    url = f"{base_url}{path}?per_page=100"
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

    print("Q1W6 HOMEROOM PREFLIGHT (read-only)")
    print(f"base host: {urllib.parse.urlparse(base_url).hostname}")
    print()

    # 1. Current user.
    me = _get(base_url, token, "/api/v1/users/self")
    print("USER (self):")
    if isinstance(me, dict) and "__error__" in me:
        print(f"  ERROR {me['__error__']}")
    else:
        print(f"  id={me.get('id')} name={me.get('name')!r} short_name={me.get('short_name')!r}")
    print()

    # 2. Course 26429.
    course = _get(base_url, token, f"/api/v1/courses/{HOMEROOM_COURSE_ID}")
    print(f"COURSE {HOMEROOM_COURSE_ID}:")
    if isinstance(course, dict) and "__error__" in course:
        print(f"  ERROR {course['__error__']}")
    else:
        print(f"  name={course.get('name')!r}")
        print(f"  course_code={course.get('course_code')!r}")
        print(f"  workflow_state={course.get('workflow_state')!r}")
        print(f"  default_view={course.get('default_view')!r}")
    print()

    # 3. Enrollment (write access).
    enrollment = _get(
        base_url,
        token,
        f"/api/v1/courses/{HOMEROOM_COURSE_ID}/enrollments?user_id=self",
    )
    print("ENROLLMENT (self):")
    if isinstance(enrollment, dict) and "__error__" in enrollment:
        print(f"  ERROR {enrollment['__error__']}")
    elif isinstance(enrollment, list):
        if not enrollment:
            print("  (none returned)")
        for e in enrollment:
            print(
                f"  type={e.get('type')!r} role={e.get('role')!r} "
                f"state={e.get('enrollment_state')!r}"
            )
    else:
        print(f"  {enrollment}")
    print()

    # 4. Front page.
    front = _get(base_url, token, f"/api/v1/courses/{HOMEROOM_COURSE_ID}/front_page")
    print("FRONT PAGE:")
    if isinstance(front, dict) and "__error__" in front:
        print(f"  ERROR {front['__error__']}")
    else:
        fb = front.get("body") or ""
        print(f"  url={front.get('url')!r} title={front.get('title')!r}")
        print(f"  updated_at={front.get('updated_at')!r} published={front.get('published')!r}")
        print(f"  has 'Hound Families' marker: {NEWSLETTER_MARKER in fb}")
        print(f"  has 'Week six' content: {'Week six' in fb}")
        print(f"  has 'Room 203': {'Room 203' in fb}")
    print()

    # 5. Page list.
    pages = _paginate(base_url, token, f"/api/v1/courses/{HOMEROOM_COURSE_ID}/pages")
    print(f"PAGES ({len(pages)}):")
    newsletter_candidates: list[dict[str, Any]] = []
    for p in pages:
        has_marker = NEWSLETTER_MARKER in (p.get("body") or "")
        front_flag = bool(p.get("front_page"))
        marker = " <== NEWSLETTER" if has_marker else ""
        fp = " <== FRONT_PAGE" if front_flag else ""
        print(
            f"  url={p.get('url')!r} title={p.get('title')!r} "
            f"updated_at={p.get('updated_at')!r} published={p.get('published')!r}{marker}{fp}"
        )
        if has_marker:
            newsletter_candidates.append(p)
    print()

    # 6. Identify and dump the newsletter page.
    target = None
    if isinstance(front, dict) and NEWSLETTER_MARKER in (front.get("body") or ""):
        target = front
    elif newsletter_candidates:
        target = max(newsletter_candidates, key=lambda p: p.get("updated_at") or "")
    if target is None:
        print("BLOCKED: no HTML newsletter page found live.")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dump = OUT_DIR / "q1w6-newsletter-before.html"
    dump.write_text(target.get("body") or "")
    print(f"NEWSLETTER SOURCE: url={target.get('url')!r} title={target.get('title')!r}")
    print(f"  updated_at={target.get('updated_at')!r}")
    print(f"  body dumped to: {dump} ({len(target.get('body') or '')} chars)")
    print()
    print("BLOCKERS: 0" if not any(
        isinstance(x, dict) and "__error__" in x for x in (me, course, enrollment)
    ) else "BLOCKERS: see above")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
