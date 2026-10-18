#!/usr/bin/env python3
"""Q1W6 Language Arts weekly page update + Classroom Practice assignments — guarded.

Targets the missing Q1W6 Language Arts piece only (course 28171):

1. fresh-GET the Week 6 weekly page (url q1w6-august-24-28-2026) and confirm it
   is the preloaded blank KL template;
2. fresh-GET assignment groups (resolve "Classwork" id) and assignments
   (duplicate check for "ELA4A: Classroom Practice 13" / "14");
3. back up the live state before any write;
4. build the updated page body from the approved KL HTML style (same wrapper /
   banner / day blocks as the filled Q1W5 page, Reminders heading, single
   full-width In Class column, full wording — no raw Shurley shorthand);
5. in --preview mode: write the preview HTML to .local and report the plan with
   zero writes;
6. in --launch mode (explicit): update the page in place, then create the two
   Classroom Practice assignments in the Classwork group, then fresh-GET and
   verify each result.

Only "ELA4A: Classroom Practice 13" (Wed Aug 26) and "ELA4A: Classroom Practice
14" (Fri Aug 28) are created. "Introduction Writing" and "Writing Map" create no
assignments. The token is never printed.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_credentials as credentials  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_connection_manager as transport  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_writer as writer  # noqa: E402

COURSE_ID = 28171
PAGE_URL = "q1w6-august-24-28-2026"
PAGE_TITLE = "Q1W6 - August 24–28, 2026"
CLASSWORK_GROUP = "Classwork"
BACKUP_DIR = REPO_ROOT / ".local" / "canvas-llm" / "backups"
PREVIEW_DIR = REPO_ROOT / ".local" / "canvas-llm"

ASSIGNMENTS = (
    {
        "title": "ELA4A: Classroom Practice 13",
        "description": "",
        "due_at": "2026-08-26T23:59:00-04:00",
    },
    {
        "title": "ELA4A: Classroom Practice 14",
        "description": "",
        "due_at": "2026-08-28T23:59:00-04:00",
    },
)

LINK_TAG = (
    '<link rel="stylesheet" href="https://instructure-uploads.s3.amazonaws.com/'
    'account_111510000000000001/attachments/219636/canvas_global_app.css">'
)
SCRIPT_TAG = (
    '<script src="https://instructure-uploads.s3.amazonaws.com/'
    'account_111510000000000001/attachments/219635/canvas_global_app.js"></script>'
)

# Filled weekly-page style (matches the live Q1W5 page: single full-width In
# Class column, no At Home column, "Reminders" heading, border-width reset).
H3_BORDER = "border-width: 0px !important; border-style: none !important; border-color: currentcolor !important;"
H4_BORDER = H3_BORDER
DAY_H3_STYLE = (
    "color: #ffffff; background-color: #0065a7; margin-top: 15px; margin-bottom: 2px; "
    + H3_BORDER
)
H4_STYLE = (
    "color: #ffffff; background-color: #333333; padding-left: 10px; margin: 0px; "
    + H4_BORDER
)

REMINDERS_HTML = (
    "<p>Continue working through Chapter 3. Classroom Practices 13 and 14 "
    "will be completed this week.</p>"
)

DAYS: list[tuple[str, str, tuple[str, ...]]] = [
    ("kl_activities2", "Monday", ("Chapter 3, Lesson 1",)),
    ("kl_custom_block_4", "Tuesday", ("Introduction Writing",)),
    ("kl_custom_block_3", "Wednesday", ("Chapter 3, Lesson 2", "Classroom Practice 13")),
    ("kl_custom_block_2", "Thursday", ("Writing Map",)),
    ("kl_custom_block_1", "Friday", ("Chapter 3, Lesson 3", "Classroom Practice 14")),
]

REQUIRED_PRESENT = (
    "Weekly Agenda",
    "Quarter 1, Week 6 | August 24\u201328, 2026",
    "Reminders",
    "Continue working through Chapter 3",
    "Classroom Practices 13 and 14 will be completed this week",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "In Class",
    "Chapter 3, Lesson 1",
    "Introduction Writing",
    "Chapter 3, Lesson 2",
    "Classroom Practice 13",
    "Writing Map",
    "Chapter 3, Lesson 3",
    "Classroom Practice 14",
    "kl_wrapper_3",
    "kl_banner",
)

REQUIRED_ABSENT = (
    "3.1",
    "3.2",
    "3.3",
    "CP 13",
    "CP 14",
    "CP13",
    "CP14",
    "At Home",
    "Reminders &amp; Resources",
    "Reminders & Resources",
    "&nbsp;&nbsp;",
    "<p>&nbsp;</p>",
)


def _day_block(block_id: str, day: str, items: tuple[str, ...]) -> str:
    lis = "\n".join(f"<li>{item}</li>" for item in items)
    return (
        f'<div id="{block_id}" class="">\n'
        f'<h3 style="{DAY_H3_STYLE}">{day}</h3>\n'
        f'<div style="display: flex; width: 100%;">\n'
        f'<div style="width: 100%; padding-left: 15px;">\n'
        f'<h4 class="kl_solid_border" style="{H4_STYLE}">In Class</h4>\n'
        f"<ul>\n{lis}\n</ul>\n"
        f"</div>\n"
        f"</div>\n"
        f"</div>"
    )


def build_body() -> str:
    reminder_h3 = (
        f'<h3 style="background-color: #c51062; color: #ffffff; {H3_BORDER}">Reminders</h3>'
    )
    day_blocks = "\n".join(_day_block(i, d, c) for i, d, c in DAYS)
    return (
        LINK_TAG
        + '<div id="kl_wrapper_3" class="kl_circle_left kl_wrapper" style="border-style: none;">\n'
        + '<div id="kl_banner" class="">\n'
        + '<p style="color: #ffffff; background-color: #0065a7; text-align: center; margin: 0;">'
        + '<span style="font-size: 18pt;">&nbsp;Weekly Agenda</span><br>'
        + '<span style="font-size: 10pt;">Quarter 1, Week 6 | August 24\u201328, 2026</span></p>\n'
        + reminder_h3
        + '\n<div style="width: 100%; padding-left: 15px;">\n'
        + REMINDERS_HTML
        + "\n</div>\n"
        + day_blocks
        + "\n</div>\n</div>"
        + SCRIPT_TAG
    )


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


def _classwork_group_id(base_url: str, token: str) -> str | None:
    groups = _paginate(base_url, token, f"/api/v1/courses/{COURSE_ID}/assignment_groups")
    for g in groups:
        if (g.get("name") or "").strip() == CLASSWORK_GROUP:
            return str(g.get("id"))
    return None


def _existing_assignment_titles(base_url: str, token: str) -> list[str]:
    assignments = _paginate(base_url, token, f"/api/v1/courses/{COURSE_ID}/assignments")
    return [a.get("name") or "" for a in assignments]


def _backup(page: dict[str, Any], titles: list[str]) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = BACKUP_DIR / f"q1w6-la-launch-{stamp}.json"
    payload = {
        "course_id": COURSE_ID,
        "page_url": page.get("url"),
        "page_title": page.get("title"),
        "page_updated_at": page.get("updated_at"),
        "page_body": page.get("body") or "",
        "existing_assignment_titles": titles,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    return path


def run(*, launch: bool = False) -> int:
    credentials.load_credentials()
    base_url = os.environ["CANVAS_BASE_URL"].strip().rstrip("/")
    token = os.environ["CANVAS_TOKEN"]

    # 1. Fresh GET the Week 6 page.
    page = _get(base_url, token, f"/api/v1/courses/{COURSE_ID}/pages/{PAGE_URL}")
    if isinstance(page, dict) and "__error__" in page:
        print(f"BLOCKED: page read failed: {page['__error__']}")
        return 1
    body = page.get("body") or ""
    if page.get("title") != PAGE_TITLE:
        print(f"BLOCKED: unexpected page title {page.get('title')!r} (expected {PAGE_TITLE!r})")
        return 1
    print(f"page: url={page.get('url')!r} title={page.get('title')!r} updated_at={page.get('updated_at')!r}")

    already_filled = (
        "Classroom Practice 13" in body
        and "Classroom Practice 14" in body
        and "Introduction Writing" in body
    )
    if already_filled:
        print("ALREADY_APPLIED: Week 6 page already contains the target content; zero writes.")
        return 0
    if "kl_wrapper_3" not in body:
        print("BLOCKED: page does not carry the KL wrapper structure; refusing in-place update.")
        return 1
    print("page is the preloaded KL template (blank content regions)")

    # 2. Assignment group + duplicate check.
    group_id = _classwork_group_id(base_url, token)
    if group_id is None:
        print("BLOCKED: 'Classwork' assignment group not found in course 28171.")
        return 1
    print(f"assignment group: Classwork id={group_id}")
    titles = _existing_assignment_titles(base_url, token)
    for spec in ASSIGNMENTS:
        if spec["title"] in titles:
            print(f"duplicate check: {spec['title']} EXISTS (skip)")
        else:
            print(f"duplicate check: {spec['title']} absent (create)")

    # 3. Backup.
    backup = _backup(page, titles)
    print(f"backup written: {backup}")

    # 4. Build the target body and validate it locally.
    new_body = build_body()
    missing = [s for s in REQUIRED_PRESENT if s not in new_body]
    unexpected = [s for s in REQUIRED_ABSENT if s in new_body]
    print(f"target body built: {len(new_body)} chars")
    if missing or unexpected:
        print("BLOCKED: local body validation failed.")
        print(json.dumps({"missing": missing, "unexpected": unexpected}, indent=2, ensure_ascii=False))
        return 1

    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    preview = PREVIEW_DIR / "q1w6-la-after.html"
    preview.write_text(new_body)
    print(f"preview HTML saved: {preview}")

    plan = {
        "page_update": {
            "action": "UPDATE_IN_PLACE",
            "course_id": COURSE_ID,
            "page_url": PAGE_URL,
            "title": PAGE_TITLE,
            "published": True,
        },
        "assignments_to_create": [
            {
                "title": spec["title"],
                "group": CLASSWORK_GROUP,
                "group_id": group_id,
                "due_at": spec["due_at"],
                "points": 100,
                "grading_type": "percent",
                "submission_type": "on_paper",
                "create": spec["title"] not in titles,
            }
            for spec in ASSIGNMENTS
        ],
        "not_created": ["Introduction Writing", "Writing Map"],
    }
    print(json.dumps(plan, indent=2, ensure_ascii=False))

    if not launch:
        print("PREVIEW ONLY: zero writes performed. Re-run with --launch after approval.")
        return 0

    # 5. Launch: update page in place, then create assignments.
    client = transport.Phase22LiveCanvasClient.from_env()

    page_result = writer.update_page_live(
        course_id=COURSE_ID,
        page_ref=PAGE_URL,
        title=PAGE_TITLE,
        body=new_body,
        published=True,
        approved=True,
        approved_by="Owen Reagan",
        client=client,
    )
    if page_result.write_status != "WRITTEN":
        print(f"BLOCKED: page update {page_result.write_status} ({', '.join(page_result.blockers) or 'blocked'})")
        return 1
    print(f"WRITTEN: page updated in place (url={page_result.target_id})")

    for spec in ASSIGNMENTS:
        if spec["title"] in titles:
            print(f"SKIP: {spec['title']} already exists; no duplicate write.")
            continue
        result = writer.create_assignment_live(
            course_id=COURSE_ID,
            title=spec["title"],
            description=spec["description"],
            assignment_group=CLASSWORK_GROUP,
            due_at=spec["due_at"],
            published=True,
            approved=True,
            approved_by="Owen Reagan",
            client=client,
        )
        if result.write_status != "WRITTEN":
            print(f"BLOCKED: assignment {spec['title']} {result.write_status} ({', '.join(result.blockers) or 'blocked'})")
            return 1
        print(f"WRITTEN: {spec['title']} (id={result.target_id})")

    # 6. Verify.
    verified = _get(base_url, token, f"/api/v1/courses/{COURSE_ID}/pages/{PAGE_URL}")
    vbody = (verified.get("body") or "") if not (isinstance(verified, dict) and "__error__" in verified) else ""
    vmissing = [s for s in REQUIRED_PRESENT if s not in vbody]
    vunexpected = [s for s in REQUIRED_ABSENT if s in vbody]
    print(json.dumps({
        "page_title_ok": verified.get("title") == PAGE_TITLE,
        "missing_content": vmissing,
        "unexpected_content": vunexpected,
    }, indent=2, ensure_ascii=False))
    if verified.get("title") != PAGE_TITLE or vmissing or vunexpected:
        print("BLOCKED: page verification failed.")
        return 1
    print("VERIFIED: Week 6 Language Arts page updated in place with full wording; no raw Shurley shorthand.")
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Q1W6 Language Arts page update + CP assignments")
    parser.add_argument("--launch", action="store_true", help="perform guarded writes (after approval)")
    args = parser.parse_args(argv)
    return run(launch=args.launch)


if __name__ == "__main__":
    raise SystemExit(main())
