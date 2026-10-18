#!/usr/bin/env python3
"""Q1W7 weekly package preflight — READ-ONLY (GET only, zero Canvas writes).

Fresh GET-only Canvas preflight for the Week 7 (Aug 31 - Sep 4, 2026) build.
Verifies guarded-workflow preconditions for all active courses without writing:

For each active course (Math 26404, Reading/Spelling 26442, Language Arts 28171,
History 28165) and Homeroom (26429):

1. fresh-GET the authenticated user and course + self enrollment;
2. fresh-GET the full page list and locate the Q1W7 weekly page
   (url/title "q1w7" or "august 31" or "september 4");
3. dump that page's existing HTML to .local/canvas-llm/ for inspection;
4. fresh-GET the current front page and report its front-page state;
5. fresh-GET assignment groups (resolve "Homework/Class Work", "Homework",
   "Assessments" ids);
6. fresh-GET assignments and run the duplicate check for the 9 planned titles;
7. fresh-GET announcements and run the duplicate check for the 2 subject
   announcements + Homeroom Week 7 family announcement.

Science (28166) is reported only (inactive quarter, untouched).

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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_credentials as credentials  # noqa: E402

OUT_DIR = REPO_ROOT / ".local" / "canvas-llm"

Q1W7_TOKENS = ("q1w7", "august-31", "august 31", "september-4", "september 4")

# Subject courses to inspect (active builds).
SUBJECTS: list[tuple[str, int]] = [
    ("Math", 26404),
    ("Reading/Spelling", 26442),
    ("Language Arts", 28171),
    ("History", 28165),
]
HOMEROOM = ("Homeroom", 26429)
SCIENCE = ("Science", 28166)

# Planned assignment CREATE titles -> (course_id, expected group name).
PLANNED_ASSIGNMENTS: dict[int, list[tuple[str, str]]] = {
    26404: [
        ("SM5: Lesson 21 Homework", "Homework/Class Work"),
        ("SM5: Lesson 22", "Homework/Class Work"),
        ("SM5: Lesson 23 Homework", "Homework/Class Work"),
        ("SM5: Lesson 24", "Homework/Class Work"),
    ],
    26442: [
        ("RM4: Lesson 25 Workbook", "Homework"),
        ("RM4: Lesson 26 Workbook and Comprehension", "Homework"),
        ("RM4: Lesson 27 Workbook", "Homework"),
        ("RM4: Lesson 28 Workbook and Comprehension", "Homework"),
    ],
    28171: [
        ("ELA4A: Ch. 3 Test", "Assessments"),
    ],
}

# Planned announcement CREATE titles -> course_id.
PLANNED_ANNOUNCEMENTS: dict[int, list[str]] = {
    28171: ["Chapter 3 Shurley Test - Tuesday, September 1"],
    28165: ["Update - World Mountains Test Moved to Wednesday"],
    26429: ["4th Grade Happenings - Week 7"],
}

GROUP_NAMES: dict[int, set[str]] = {
    26404: {"Written Assessments", "Fact Assessments", "Homework/Class Work"},
    26442: {"Check Out", "Assessments", "Homework"},
    28171: {"Classwork", "Assessments"},
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


def _is_q1w7(page: dict[str, Any]) -> bool:
    url = (page.get("url") or "").lower()
    title = (page.get("title") or "").lower()
    blob = f"{url} {title}"
    return any(t in blob for t in Q1W7_TOKENS)


def main() -> int:
    credentials.load_credentials()
    base_url = os.environ["CANVAS_BASE_URL"].strip().rstrip("/")
    token = os.environ["CANVAS_TOKEN"]

    print("Q1W7 WEEKLY PACKAGE PREFLIGHT (read-only, GET only)")
    print(f"base host: {urllib.parse.urlparse(base_url).hostname}")
    print(f"generated_at_utc: {datetime.now(timezone.utc).isoformat()}")
    print()

    # 0. Current user.
    me = _get(base_url, token, "/api/v1/users/self")
    print("USER (self):")
    if isinstance(me, dict) and "__error__" in me:
        print(f"  ERROR {me['__error__']}")
    else:
        print(f"  id={me.get('id')} name={me.get('name')!r}")
    print()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {"courses": {}}

    for name, cid in SUBJECTS + [HOMEROOM, SCIENCE]:
        entry: dict[str, Any] = {"subject": name, "course_id": cid}
        print(f"===== {name} ({cid}) =====")

        course = _get(base_url, token, f"/api/v1/courses/{cid}")
        if isinstance(course, dict) and "__error__" in course:
            print(f"  COURSE ERROR {course['__error__']}")
            entry["course_error"] = course["__error__"]
        else:
            print(f"  course name={course.get('name')!r} state={course.get('workflow_state')!r}")
            entry["course_name"] = course.get("name")
            entry["workflow_state"] = course.get("workflow_state")

        # Permissions (read-only, informational only — NOT a write gate).
        #
        # The /permissions endpoint is not the capability gate for page writes.
        # Under a non-admin token it reports page permissions
        # (create_pages/update_pages/delete_pages/manage_wiki/update_course) as
        # null (or false when forced via permissions[]=), even though the
        # PUT /api/v1/courses/:id/pages/:url endpoint succeeds for the same user.
        # Proven precedent: Q1W6 page updates + front-page sets went through
        # Phase22LiveCanvasClient.update_page (PUT .../pages/:url, wiki_page[...])
        # using Owen's established credentials, and are live today.
        #
        # We probe the endpoint UNFILTERED and report values truthfully, but never
        # treat page keys as a blocker.
        perms = _get(base_url, token, f"/api/v1/courses/{cid}/permissions")
        if isinstance(perms, dict) and "__error__" in perms:
            print(f"  PERMISSIONS ERROR {perms['__error__']}")
            entry["permissions_error"] = perms["__error__"]
        elif isinstance(perms, dict):
            watched = [
                "manage_assignments_add", "manage_assignments_edit", "manage_assignments_delete",
                "create_pages", "update_pages", "delete_pages", "manage_wiki", "update_course",
                "create_forum", "post_to_forum",
            ]
            entry["permissions_informational"] = {k: perms.get(k) for k in watched}
            print(f"  PERMISSIONS (informational, non-gating):")
            for k in watched:
                print(f"    {k} = {perms.get(k)!r}")
            print(f"    NOTE: null/false page keys are not authoritative; page writes are "
                  f"proven by Q1W6 precedent via PUT /pages/:url.")

        # Front page (current).
        front = _get(base_url, token, f"/api/v1/courses/{cid}/front_page")
        if isinstance(front, dict) and "__error__" in front:
            print(f"  FRONT PAGE ERROR {front['__error__']}")
            entry["front_page_error"] = front["__error__"]
        else:
            print(f"  front_page url={front.get('url')!r} title={front.get('title')!r} front_page={front.get('front_page')!r}")
            entry["front_page"] = {
                "url": front.get("url"),
                "title": front.get("title"),
                "front_page": front.get("front_page"),
            }

        # Pages + Q1W7 locate.
        pages = _paginate(base_url, token, f"/api/v1/courses/{cid}/pages")
        q1w7_candidates = [p for p in pages if _is_q1w7(p)]
        entry["page_count"] = len(pages)
        entry["q1w7_page_count"] = len(q1w7_candidates)
        print(f"  PAGES ({len(pages)}) — Q1W7 candidates: {len(q1w7_candidates)}")
        for p in q1w7_candidates:
            print(f"    Q1W7? url={p.get('url')!r} title={p.get('title')!r} "
                  f"front_page={p.get('front_page')!r} published={p.get('published')!r} "
                  f"updated_at={p.get('updated_at')!r}")
        if q1w7_candidates:
            target = max(q1w7_candidates, key=lambda p: p.get("updated_at") or "")
            url = target.get("url")
            detail = target
            if url:
                fetched = _get(base_url, token, f"/api/v1/courses/{cid}/pages/{url}")
                if isinstance(fetched, dict) and "__error__" not in fetched:
                    detail = fetched
            body = detail.get("body") or ""
            safe = name.lower().replace("/", "-").replace(" ", "-")
            dump = OUT_DIR / f"q1w7-{safe}-before.html"
            dump.write_text(body)
            entry["q1w7_page"] = {
                "url": detail.get("url"),
                "title": detail.get("title"),
                "front_page": detail.get("front_page"),
                "published": detail.get("published"),
                "body_len": len(body),
                "has_kl_wrapper": "kl_wrapper_3" in body,
                "has_reminders": "Reminders" in body,
                "dump": str(dump),
            }
            print(f"    target url={detail.get('url')!r} title={detail.get('title')!r}")
            print(f"      kl_wrapper_3={ 'kl_wrapper_3' in body} Reminders={'Reminders' in body}")
            print(f"      body dumped: {dump} ({len(body)} chars)")
        else:
            print(f"    BLOCKED: no Q1W7 page found live for {name}.")

        # Assignment groups (only for assignment-bearing courses).
        if cid in GROUP_NAMES:
            groups = _paginate(base_url, token, f"/api/v1/courses/{cid}/assignment_groups")
            present = {g.get("name") for g in groups}
            entry["assignment_groups"] = sorted(present)
            missing = sorted(GROUP_NAMES[cid] - present)
            print(f"  ASSIGNMENT GROUPS: {sorted(present)}")
            if missing:
                print(f"    WARN: missing expected groups: {missing}")

        # Assignments + duplicate check.
        if cid in PLANNED_ASSIGNMENTS:
            assignments = _paginate(base_url, token, f"/api/v1/courses/{cid}/assignments")
            live_titles = {a.get("name") for a in assignments}
            print(f"  ASSIGNMENTS ({len(assignments)}) — planned duplicate check:")
            for title, group in PLANNED_ASSIGNMENTS[cid]:
                status = "EXISTS (dup)" if title in live_titles else "absent (create)"
                print(f"    {title!r} [{group}] -> {status}")
                entry.setdefault("planned_assignments", []).append(
                    {"title": title, "group": group, "duplicate": title in live_titles}
                )
        elif cid in (HOMEROOM[1], SCIENCE[1]):
            pass  # Homeroom/Science have no planned assignments.

        # Announcements + duplicate check.
        if cid in PLANNED_ANNOUNCEMENTS:
            anns = _paginate(
                base_url, token,
                f"/api/v1/courses/{cid}/discussion_topics",
                {"only_announcements": "true"},
            )
            ann_titles = [a.get("title") or "" for a in anns]
            ann_msgs = [a.get("message") or "" for a in anns]
            print(f"  ANNOUNCEMENTS ({len(anns)}) — planned duplicate check:")
            for title in PLANNED_ANNOUNCEMENTS[cid]:
                dup = any(
                    t == title or title in t or title in m
                    for t, m in zip(ann_titles, ann_msgs)
                )
                status = "EXISTS (dup)" if dup else "absent (create)"
                print(f"    {title!r} -> {status}")
                entry.setdefault("planned_announcements", []).append(
                    {"title": title, "duplicate": dup}
                )
            if cid == HOMEROOM[1]:
                for a in anns:
                    t = a.get("title") or ""
                    flag = ""
                    if "week 7" in t.lower() or "4th grade happenings - week 7" in t.lower():
                        flag = " <== WEEK7?"
                    print(f"    live: id={a.get('id')} title={t!r} posted={a.get('posted_at')!r}{flag}")

        # Homeroom newsletter marker check.
        if cid == HOMEROOM[1] and isinstance(front, dict) and "__error__" not in front:
            fb = front.get("body") or ""
            print(f"  NEWSLETTER: has 'Hound Families'={'Hound Families' in fb} "
                  f"has 'Week 6'={'Week 6' in fb} has 'Week six'={'Week six' in fb}")
            dump = OUT_DIR / "q1w7-newsletter-current.html"
            dump.write_text(fb)
            print(f"  newsletter dumped: {dump} ({len(fb)} chars)")
            entry["newsletter_has_hound_families"] = "Hound Families" in fb
            entry["homeroom_target"] = (
                "UPDATE rolling newsletter in place on front page (q1w2-july-27-31-2026); "
                "blank Q1W7 template page is NOT used for Homeroom"
            )
            print(f"  NOTE: Homeroom does not use the blank Q1W7 page; target is the "
                  f"rolling newsletter on the front page ({front.get('url')!r}), "
                  f"already front_page={front.get('front_page')!r} -> verification/no-op.")

        if cid == SCIENCE[1]:
            print("  (Science inactive quarter — reported only, will remain untouched)")

        report["courses"][str(cid)] = entry
        print()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = OUT_DIR / "q1w7-preflight-snapshot.json"
    snapshot.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"snapshot written: {snapshot}")

    print("WRITES PERFORMED: 0")
    print("READ-ONLY: GET requests only; no POST/PUT/PATCH/DELETE.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
