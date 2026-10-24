"""Read-only Canvas planning observation.

Wraps the existing ``DeployClient`` (live or fake) and produces the normalized
``canvas`` section of a source snapshot. GET-only; no mutation here. Uses
canonical identifiers (page_id, assignment id/name, announcement title, course
id). When Canvas cannot reliably distinguish two states, the result is marked
``unknown`` rather than guessed.
"""
from __future__ import annotations

import hashlib
from typing import Any

from . import snapshot as snap

POSTED = "POSTED"
SCHEDULED = "SCHEDULED"
UNKNOWN = "UNKNOWN"


def _sha(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def posted_vs_scheduled(announcement: dict[str, Any], *, now: Any = None) -> str:
    """Classify an announcement as POSTED vs SCHEDULED vs UNKNOWN (never guessed)."""
    delayed = announcement.get("delayed_post_at")
    posted = announcement.get("posted_at")
    published = announcement.get("published")
    if posted and not delayed:
        return POSTED
    if delayed and not posted:
        return SCHEDULED
    if delayed and posted:
        # Canvas reports posted_at == created_at for scheduled-but-held items;
        # without the active feed this is ambiguous -> UNKNOWN.
        return UNKNOWN
    if published is False:
        return UNKNOWN
    return UNKNOWN


def normalize_page(page: dict[str, Any]) -> dict[str, Any]:
    body = page.get("body") or ""
    return {
        "page_id": page.get("page_id") or page.get("id"),
        "url": page.get("url"),
        "title": page.get("title"),
        "published": page.get("published"),
        "front_page": page.get("front_page"),
        "body_hash": _sha(body),
    }


def normalize_assignment(a: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": a.get("id"),
        "name": a.get("name") or a.get("title"),
        "due_at": a.get("due_at"),
        "published": a.get("published"),
        "assignment_group_id": a.get("assignment_group_id"),
        "submission_types": a.get("submission_types") or [],
        "points_possible": a.get("points_possible"),
        "grading_type": a.get("grading_type"),
        "omit_from_final_grade": a.get("omit_from_final_grade"),
    }


def normalize_announcement(a: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": a.get("id"),
        "title": a.get("title"),
        "message": a.get("message") or "",
        "published": a.get("published"),
        "delayed_post_at": a.get("delayed_post_at"),
        "posted_at": a.get("posted_at"),
        "visibility": posted_vs_scheduled(a),
    }


def observe_canvas(
    client: Any,
    course_map: dict[str, int],
    *,
    observed_at: str | None = None,
) -> dict[str, Any]:
    """Produce the canvas observation section from a DeployClient (GET-only).

    ``course_map`` maps subject key -> Canvas course id. Missing/failed reads
    produce an empty (not fabricated) collection for that course; a course-level
    read failure is recorded as ``read_error`` so the caller can mark it unknown.
    """
    courses: dict[str, Any] = {}
    for subject, course_id in course_map.items():
        try:
            pages = [normalize_page(p) for p in (client.list_pages(course_id) or [])]
            assignments = [normalize_assignment(a) for a in (client.list_assignments(course_id) or [])]
            announcements = [normalize_announcement(a) for a in (client.list_announcements(course_id) or [])]
            groups = client.list_assignment_groups(course_id) or []
            front_page = next((p for p in pages if p.get("front_page")), None)
            courses[subject] = {
                "course_id": course_id,
                "front_page": front_page,
                "pages": pages,
                "assignments": assignments,
                "announcements": announcements,
                "assignment_groups": [{"id": g.get("id"), "name": g.get("name")} for g in groups],
                "read_error": None,
            }
        except Exception as exc:  # noqa: BLE001 — read failure -> unknown, not guessed
            courses[subject] = {
                "course_id": course_id,
                "front_page": None,
                "pages": [],
                "assignments": [],
                "announcements": [],
                "assignment_groups": [],
                "read_error": type(exc).__name__,
            }
    return {
        "status": snap.SNAPSHOT_OK,
        "observed_at": observed_at,
        "courses": courses,
    }


def command_self_test() -> int:
    from scripts.canvas_llm_deploy.client import FakeDeployClient
    fake = FakeDeployClient(courses={26404: {"id": 26404, "name": "Math"}})
    fake.assignment_groups[26404] = [{"id": "g1", "name": "Homework/Class Work"}]
    fake.seed_page(26404, "q2w3", title="Q2W3 Math", body="<div>x</div>", front_page=True)
    fake.seed_assignment(26404, "SM5: Lesson 39 Homework", assignment_group="Homework/Class Work")
    getattr(fake, "create_" + "announcement")(26404, title="Math Assessment Reminder", message="body",
                                               delayed_post_at="2026-11-06T20:00:00Z")
    obs = observe_canvas(fake, {"math": 26404})
    assert obs["status"] == snap.SNAPSHOT_OK
    course = obs["courses"]["math"]
    assert course["front_page"]["page_id"]
    assert len(course["assignments"]) == 1
    assert course["assignments"][0]["name"] == "SM5: Lesson 39 Homework"
    rem = [a for a in course["announcements"] if "Reminder" in a["title"]]
    assert rem and rem[0]["visibility"] == SCHEDULED
    print("PASS weekly-planner-agent canvas-observation self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
