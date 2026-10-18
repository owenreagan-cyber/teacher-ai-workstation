#!/usr/bin/env python3
"""Read-only Q1W5 live Canvas audit.

GET requests only. Never POST/PUT/PATCH/DELETE. Never creates, updates,
publishes, unpublishes, or schedules anything in Canvas. Never writes the
token to disk or stdout. Output is written to a token-free JSON file under
.local/canvas-llm/q1w5-audit/ and a compact summary is printed to stdout.

Usage (run from repo root, token set locally via hidden prompt):
    export CANVAS_BASE_URL="https://thalesacademy.instructure.com"
    printf "Canvas token: "; stty -echo; IFS= read CANVAS_TOKEN; stty echo; echo; export CANVAS_TOKEN
    python3 scripts/canvas-llm/q1w5_live_audit.py
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_URL = os.environ.get("CANVAS_BASE_URL", "").strip().rstrip("/")
TOKEN = os.environ.get("CANVAS_TOKEN", "").strip()
if not BASE_URL or not TOKEN:
    raise SystemExit("FAIL: set CANVAS_BASE_URL and CANVAS_TOKEN before running.")

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / ".local" / "canvas-llm" / "q1w5-audit"
OUT_FILE = OUT_DIR / "q1w5-live-audit.json"

COURSES: dict[str, int] = {
    "Math": 26404,
    "Reading/Spelling": 26442,
    "Language Arts": 28171,
    "History": 28165,
    "Science": 28166,
    "Homeroom": 26427,
}

# Week under audit (America/New_York).
Q1W5_START = "2026-08-17"
Q1W5_END = "2026-08-22"  # exclusive


def _redact(text: str) -> str:
    redacted = text
    if TOKEN:
        redacted = redacted.replace(TOKEN, "[REDACTED]")
    redacted = redacted.replace(f"Bearer {TOKEN}", "Bearer [REDACTED]")
    return redacted


def _get_raw(url: str) -> tuple[Any, str]:
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            text = response.read().decode("utf-8")
            link = response.headers.get("Link", "")
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(_redact(f"{exc}")) from exc
    return (json.loads(text) if text else None), link


def _next_url(link: str) -> str | None:
    for part in link.split(","):
        if 'rel="next"' not in part:
            continue
        start = part.find("<")
        end = part.find(">")
        if 0 <= start < end:
            return part[start + 1 : end]
    return None


def _paginate(path: str, params: dict[str, Any] | None = None) -> list[Any]:
    merged = {"per_page": 100}
    if params:
        merged.update(params)
    url = f"{BASE_URL}{path}?{urllib.parse.urlencode(merged, doseq=True)}"
    items: list[Any] = []
    for _ in range(50):  # hard cap on pages
        data, link = _get_raw(url)
        if isinstance(data, list):
            items.extend(data)
        elif data is not None:
            items.append(data)
            break
        nxt = _next_url(link)
        if not nxt:
            break
        url = nxt
    return items


def _get_one(path: str) -> Any:
    data, _ = _get_raw(f"{BASE_URL}{path}")
    return data


def _page_public(page: dict[str, Any]) -> dict[str, Any]:
    return {
        "page_id": page.get("page_id"),
        "url": page.get("url"),
        "title": page.get("title"),
        "published": page.get("published"),
        "front_page": page.get("front_page"),
        "created_at": page.get("created_at"),
        "updated_at": page.get("updated_at"),
        "body": page.get("body"),
    }


def _assignment_public(assignment: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": assignment.get("id"),
        "name": assignment.get("name"),
        "due_at": assignment.get("due_at"),
        "unlock_at": assignment.get("unlock_at"),
        "lock_at": assignment.get("lock_at"),
        "published": assignment.get("published"),
        "workflow_state": assignment.get("workflow_state"),
        "points_possible": assignment.get("points_possible"),
        "grading_type": assignment.get("grading_type"),
        "submission_types": assignment.get("submission_types"),
        "assignment_group_id": assignment.get("assignment_group_id"),
        "omit_from_final_grade": assignment.get("omit_from_final_grade"),
        "description": assignment.get("description"),
    }


def _announcement_public(topic: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": topic.get("id"),
        "title": topic.get("title"),
        "message": topic.get("message"),
        "posted_at": topic.get("posted_at"),
        "delayed_post_at": topic.get("delayed_post_at"),
        "published": topic.get("published"),
        "discussion_type": topic.get("discussion_type"),
    }


def _in_q1w5(iso: str | None) -> bool:
    if not iso:
        return False
    date_part = iso[:10]
    return Q1W5_START <= date_part < Q1W5_END


def audit_course(subject: str, course_id: int) -> dict[str, Any]:
    course = _get_one(f"/api/v1/courses/{course_id}")
    pages_raw = _paginate(f"/api/v1/courses/{course_id}/pages")
    assignments_raw = _paginate(f"/api/v1/courses/{course_id}/assignments")
    announcements_raw = _paginate(
        f"/api/v1/courses/{course_id}/discussion_topics",
        {"only_announcements": "true"},
    )

    pages: list[dict[str, Any]] = []
    for page in pages_raw:
        url = page.get("url")
        detail = page
        if url:
            try:
                detail = _get_one(f"/api/v1/courses/{course_id}/pages/{url}")
            except RuntimeError:
                detail = page
        pages.append(_page_public(detail))

    front_page: dict[str, Any] | None = None
    try:
        front_page = _page_public(_get_one(f"/api/v1/courses/{course_id}/front_page"))
    except RuntimeError:
        front_page = None

    return {
        "subject": subject,
        "course_id": course_id,
        "course": {
            "id": course.get("id") if isinstance(course, dict) else course_id,
            "name": course.get("name") if isinstance(course, dict) else None,
            "course_code": course.get("course_code") if isinstance(course, dict) else None,
            "workflow_state": course.get("workflow_state") if isinstance(course, dict) else None,
            "default_view": course.get("default_view") if isinstance(course, dict) else None,
        },
        "front_page": front_page,
        "pages": pages,
        "assignments": [_assignment_public(a) for a in assignments_raw],
        "announcements": [_announcement_public(a) for a in announcements_raw],
        "q1w5_pages": [p for p in pages if "q1w5" in (p.get("url") or "").lower() or "q1w5" in (p.get("title") or "").lower() or "week 5" in (p.get("title") or "").lower() or "august" in (p.get("title") or "").lower()],
        "q1w5_assignments": [
            a for a in [_assignment_public(a) for a in assignments_raw]
            if _in_q1w5(a.get("due_at"))
        ],
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "audit": "Q1W5 LIVE CANVAS AUDIT",
        "week": "August 17-21, 2026",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_url_host": urllib.parse.urlparse(BASE_URL).hostname,
        "read_only": True,
        "courses": {},
    }
    for subject, course_id in COURSES.items():
        try:
            report["courses"][str(course_id)] = audit_course(subject, course_id)
        except Exception as exc:  # noqa: BLE001
            report["courses"][str(course_id)] = {
                "subject": subject,
                "course_id": course_id,
                "error": _redact(str(exc)),
            }

    OUT_FILE.write_text(json.dumps(report, indent=2) + "\n")

    # Compact, token-free stdout summary.
    print("Q1W5 LIVE CANVAS AUDIT — read-only, GET only")
    print(f"Output: {OUT_FILE}")
    print()
    for subject, course_id in COURSES.items():
        entry = report["courses"].get(str(course_id), {})
        if "error" in entry:
            print(f"{subject} ({course_id}): ERROR {entry['error']}")
            continue
        c = entry.get("course", {})
        print(
            f"{subject} ({course_id}): {c.get('name')} | "
            f"state={c.get('workflow_state')} | "
            f"pages={len(entry.get('pages', []))} | "
            f"assignments={len(entry.get('assignments', []))} | "
            f"announcements={len(entry.get('announcements', []))}"
        )
        qpages = entry.get("q1w5_pages", [])
        for p in qpages:
            print(f"  Q1W5 page? title={p.get('title')} url={p.get('url')} published={p.get('published')} updated_at={p.get('updated_at')}")
        qassign = entry.get("q1w5_assignments", [])
        for a in qassign:
            print(f"  Q1W5 assignment? name={a.get('name')} due_at={a.get('due_at')} published={a.get('published')}")
    print()
    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
