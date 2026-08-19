#!/usr/bin/env python3
"""Read-only Canvas live inventory — GET-only page/assignment/announcement listing.

Permanent, week-agnostic module that fetches the canonical allowlisted
courses' pages, assignments, and announcements via GET requests only and
shapes them into the preflight inventory the launcher reconciles against.

Safety guarantees:
- GET requests only. Never POST/PUT/PATCH/DELETE; never writes to Canvas.
- The token is never written to disk or stdout and never appears in an error.
- No week-specific hard-coding: course IDs come from
  ``scripts/canvas_llm_phase22/canvas_connection.COURSE_MAP``.
"""
from __future__ import annotations

import argparse
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

from scripts.canvas_llm_phase22 import canvas_connection as connection  # noqa: E402


class InventoryError(RuntimeError):
    """Raised when the live inventory cannot be fetched (token-free)."""


def live_course_ids() -> dict[str, int]:
    """Canonical subject -> course id mapping, sourced from the shared course map."""
    return dict(connection.COURSE_MAP)


def _credentials() -> tuple[str, str]:
    base_url = (os.environ.get("CANVAS_BASE_URL") or "").strip().rstrip("/")
    token = (
        os.environ.get("CANVAS_TOKEN") or os.environ.get("CANVAS_API_TOKEN") or ""
    ).strip()
    if not base_url or not token:
        raise InventoryError(
            "CANVAS_BASE_URL and CANVAS_TOKEN are required for a live inventory"
        )
    return base_url, token


def _redact(text: str, token: str) -> str:
    redacted = text
    if token:
        redacted = redacted.replace(token, "[REDACTED]")
        redacted = redacted.replace(f"Bearer {token}", "Bearer [REDACTED]")
    return redacted


def _get_raw(base_url: str, token: str, url: str) -> tuple[Any, str]:
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            text = response.read().decode("utf-8")
            link = response.headers.get("Link", "")
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = (exc.read() or b"").decode("utf-8", "replace")[:400]
        except Exception:  # noqa: BLE001 - best-effort body capture only
            detail = ""
        raise InventoryError(
            _redact(f"HTTP {exc.code} on GET {url}: {detail or exc.reason}", token)
        ) from exc
    except urllib.error.URLError as exc:
        raise InventoryError(
            _redact(f"network error on GET {url}: {exc.reason}", token)
        ) from exc
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


def _paginate(
    base_url: str,
    token: str,
    path: str,
    params: dict[str, Any] | None = None,
) -> list[Any]:
    merged = {"per_page": 100}
    if params:
        merged.update(params)
    url = f"{base_url}{path}?{urllib.parse.urlencode(merged, doseq=True)}"
    items: list[Any] = []
    for _ in range(50):  # hard cap on pages
        data, link = _get_raw(base_url, token, url)
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


def _get_one(base_url: str, token: str, path: str) -> Any:
    data, _ = _get_raw(base_url, token, f"{base_url}{path}")
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


def audit_course(base_url: str, token: str, course_id: int) -> dict[str, Any]:
    """Fetch and shape one course's pages, assignments, and announcements."""
    course = _get_one(base_url, token, f"/api/v1/courses/{course_id}")
    pages_raw = _paginate(base_url, token, f"/api/v1/courses/{course_id}/pages")
    assignments_raw = _paginate(base_url, token, f"/api/v1/courses/{course_id}/assignments")
    announcements_raw = _paginate(
        base_url,
        token,
        f"/api/v1/courses/{course_id}/discussion_topics",
        {"only_announcements": "true"},
    )

    pages: list[dict[str, Any]] = []
    for page in pages_raw:
        url = page.get("url")
        detail = page
        if url:
            try:
                detail = _get_one(base_url, token, f"/api/v1/courses/{course_id}/pages/{url}")
            except InventoryError:
                detail = page
        pages.append(_page_public(detail))

    front_page: dict[str, Any] | None = None
    try:
        front_page = _page_public(
            _get_one(base_url, token, f"/api/v1/courses/{course_id}/front_page")
        )
    except InventoryError:
        front_page = None

    return {
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
    }


def fetch_live_inventory() -> dict[str, Any]:
    """GET-only inventory for all canonical courses.

    Returns the launcher's ``{"courses": {str(course_id): {...}}}`` shape.
    """
    base_url, token = _credentials()
    report: dict[str, Any] = {"courses": {}}
    for _subject, course_id in live_course_ids().items():
        report["courses"][str(course_id)] = audit_course(base_url, token, course_id)
    return report


def has_no_week_specific_hardcoding() -> bool:
    source = Path(__file__).read_text().lower()
    marker = "def has_no_week_specific_hardcoding"
    idx = source.find(marker)
    scan_source = source[:idx] if idx >= 0 else source
    return "q1w5" not in scan_source and "august 17" not in scan_source


def command_self_test(_args: argparse.Namespace) -> int:
    # Course mappings are sourced from the shared map (no local hard-coding).
    assert live_course_ids() == dict(connection.COURSE_MAP)
    assert set(live_course_ids().values()) == {
        connection.MATH_COURSE_ID,
        connection.READING_COURSE_ID,
        connection.ELA_COURSE_ID,
        connection.HISTORY_COURSE_ID,
        connection.SCIENCE_COURSE_ID,
        connection.HOMEROOM_COURSE_ID,
    }
    assert has_no_week_specific_hardcoding()

    # Shaping functions emit the keys the launcher reconciles against.
    page = _page_public({"page_id": 1, "url": "u", "title": "t", "published": True, "body": "b"})
    assert page["page_id"] == 1 and page["url"] == "u" and page["body"] == "b"
    assignment = _assignment_public({"id": 2, "name": "n", "omit_from_final_grade": False})
    assert assignment["id"] == 2 and assignment["name"] == "n"
    announcement = _announcement_public({"id": 3, "title": "a", "message": "m"})
    assert announcement["id"] == 3 and announcement["message"] == "m"

    # Token redaction never leaks the token.
    assert _redact("Bearer tok123 data tok123", "tok123") == "Bearer [REDACTED] data [REDACTED]"

    # Missing credentials raise a token-free InventoryError.
    try:
        fetch_live_inventory()
    except InventoryError as exc:
        assert "CANVAS_BASE_URL" in str(exc) and "CANVAS_TOKEN" in str(exc)
    else:
        raise AssertionError("fetch_live_inventory should require credentials")

    print("PASS canvas live inventory self-test")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Canvas live inventory (read-only)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("self-test").set_defaults(func=command_self_test)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
