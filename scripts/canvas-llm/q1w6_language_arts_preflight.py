#!/usr/bin/env python3
"""Q1W6 Language Arts preflight — READ-ONLY (GET only, zero Canvas writes).

Verifies the guarded-workflow preconditions for the Week 6 Language Arts weekly
page update and Classroom Practice assignment plan without writing anything:

1. fresh-GET the current authenticated user (/users/self);
2. fresh-GET Language Arts course 28171 and the self enrollment;
3. fresh-GET the full page list and locate the Week 6 weekly page
   (url/title "q1w6" or "August 24", or title "Q1W6 - August 24–28, 2026");
4. dump that page's full existing HTML to .local/canvas-llm/ for inspection;
5. fresh-GET assignment groups and list the "Classwork" group id;
6. fresh-GET assignments and run the duplicate check for
   "ELA4A: Classroom Practice 13" / "ELA4A: Classroom Practice 14".

Credentials resolve via canvas_credentials.load_credentials() (env-first, then
the 0600 private config). The token is never printed.
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

LANGUAGE_ARTS_COURSE_ID = 28171
PAGE_TITLE = "Q1W6 - August 24–28, 2026"
CLASSWORK_GROUP = "Classwork"
ASSIGNMENT_TITLES = (
    "ELA4A: Classroom Practice 13",
    "ELA4A: Classroom Practice 14",
)
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
    for _ in range(50):
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


def _page_is_week6(page: dict[str, Any]) -> bool:
    url = (page.get("url") or "").lower()
    title = (page.get("title") or "").lower()
    return any(token in url for token in ("q1w6", "week-6", "august-24")) or (
        "q1w6" in title or "week 6" in title or "august 24" in title
    )


def main() -> int:
    credentials.load_credentials()
    base_url = os.environ["CANVAS_BASE_URL"].strip().rstrip("/")
    token = os.environ["CANVAS_TOKEN"]

    print("Q1W6 LANGUAGE ARTS PREFLIGHT (read-only)")
    print(f"base host: {urllib.parse.urlparse(base_url).hostname}")
    print()

    blockers: list[str] = []

    # 1. Current user.
    me = _get(base_url, token, "/api/v1/users/self")
    print("USER (self):")
    if isinstance(me, dict) and "__error__" in me:
        print(f"  ERROR {me['__error__']}")
        blockers.append("user_self_read_failed")
    else:
        print(f"  id={me.get('id')} name={me.get('name')!r}")
    print()

    # 2. Course 28171.
    course = _get(base_url, token, f"/api/v1/courses/{LANGUAGE_ARTS_COURSE_ID}")
    print(f"COURSE {LANGUAGE_ARTS_COURSE_ID}:")
    if isinstance(course, dict) and "__error__" in course:
        print(f"  ERROR {course['__error__']}")
        blockers.append("course_read_failed")
    else:
        print(f"  name={course.get('name')!r}")
        print(f"  course_code={course.get('course_code')!r}")
        print(f"  workflow_state={course.get('workflow_state')!r}")
    print()

    # 3. Enrollment.
    enrollment = _get(
        base_url,
        token,
        f"/api/v1/courses/{LANGUAGE_ARTS_COURSE_ID}/enrollments?user_id=self",
    )
    print("ENROLLMENT (self):")
    if isinstance(enrollment, dict) and "__error__" in enrollment:
        print(f"  ERROR {enrollment['__error__']}")
        blockers.append("enrollment_read_failed")
    elif isinstance(enrollment, list):
        for e in enrollment:
            print(
                f"  type={e.get('type')!r} role={e.get('role')!r} "
                f"state={e.get('enrollment_state')!r}"
            )
    print()

    # 4. Page list + locate Week 6 page.
    pages = _paginate(base_url, token, f"/api/v1/courses/{LANGUAGE_ARTS_COURSE_ID}/pages")
    print(f"PAGES ({len(pages)}):")
    week6_candidates: list[dict[str, Any]] = []
    for p in pages:
        marker = ""
        if _page_is_week6(p):
            week6_candidates.append(p)
            marker = " <== WEEK6"
        print(
            f"  url={p.get('url')!r} title={p.get('title')!r} "
            f"updated_at={p.get('updated_at')!r} published={p.get('published')!r}{marker}"
        )
    print()

    # 5. Resolve the target page and dump its full HTML.
    target = None
    if week6_candidates:
        target = max(week6_candidates, key=lambda p: p.get("updated_at") or "")
    if target is None:
        print("BLOCKED: no Week 6 Language Arts page found live.")
        blockers.append("week6_page_missing")
    else:
        url = target.get("url")
        detail = target
        if url:
            fetched = _get(base_url, token, f"/api/v1/courses/{LANGUAGE_ARTS_COURSE_ID}/pages/{url}")
            if isinstance(fetched, dict) and "__error__" not in fetched:
                detail = fetched
        body = detail.get("body") or ""
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        dump = OUT_DIR / "q1w6-la-before.html"
        dump.write_text(body)
        print("WEEK6 PAGE SOURCE:")
        print(f"  url={detail.get('url')!r} title={detail.get('title')!r}")
        print(f"  updated_at={detail.get('updated_at')!r} published={detail.get('published')!r}")
        print(f"  body dumped: {dump} ({len(body)} chars)")
        print(f"  has kl_wrapper: {'kl_wrapper' in body}")
        print(f"  has Reminders: {'Reminders' in body}")
        print(f"  has Monday block: {'Monday' in body}")
    print()

    # 6. Assignment groups.
    groups = _paginate(
        base_url, token, f"/api/v1/courses/{LANGUAGE_ARTS_COURSE_ID}/assignment_groups"
    )
    print(f"ASSIGNMENT GROUPS ({len(groups)}):")
    classwork_id = None
    for g in groups:
        name = g.get("name") or ""
        is_cw = name.strip() == CLASSWORK_GROUP
        if is_cw:
            classwork_id = g.get("id")
        print(f"  id={g.get('id')} name={name!r}{' <== CLASSWORK' if is_cw else ''}")
    if classwork_id is None:
        print("  WARN: 'Classwork' assignment group not found")
    print()

    # 7. Assignments + duplicate check.
    assignments = _paginate(
        base_url, token, f"/api/v1/courses/{LANGUAGE_ARTS_COURSE_ID}/assignments"
    )
    print(f"ASSIGNMENTS ({len(assignments)}):")
    for a in assignments:
        name = a.get("name") or ""
        flag = ""
        if name in ASSIGNMENT_TITLES:
            flag = " <== DUP"
        print(
            f"  id={a.get('id')} name={name!r} due_at={a.get('due_at')!r} "
            f"published={a.get('published')!r}{flag}"
        )
    print()
    print("DUPLICATE CHECK (CP 13/14):")
    for title in ASSIGNMENT_TITLES:
        matches = [a for a in assignments if (a.get("name") or "") == title]
        if matches:
            print(f"  {title}: EXISTS (id={matches[0].get('id')})")
        else:
            print(f"  {title}: absent (create)")
    print()

    print("BLOCKERS:", len(blockers) if not blockers else ", ".join(blockers))
    return 0 if not blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
