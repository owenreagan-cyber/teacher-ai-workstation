"""Canvas transport adapter for guarded deployment.

This module defines a single normalized ``DeployClient`` protocol used by the
preflight and coordinator. It is a THIN adapter — it delegates to the existing
canonical Canvas helpers (``Phase22LiveCanvasClient`` for writes/readback and
``CanvasReadOnly`` for GET-only listings) and never re-implements them.

Two implementations:

- ``LiveDeployClient`` — real Canvas (production). Loads credentials via the
  canonical loader and requires the canonical live-prerequisites gate.
- ``FakeDeployClient`` — in-memory store for tests. Mirrors the normalized
  return shapes exactly, so coordinator logic is exercised without any network.

Normalized object shapes (the coordinator depends on these only):

    course      {id, name, workflow_state}
    page        {page_id, url, title, body, published, front_page}
    assignment  {id, name, points_possible, grading_type, submission_types,
                 due_at, omit_from_final_grade, assignment_group_id}
    announcement{id, title, message, published, delayed_post_at, posted_at}
"""
from __future__ import annotations

from typing import Any


class DeployClientError(RuntimeError):
    """Raised by a client when a write/read is blocked or fails cleanly."""


class DeployClient:
    """Abstract protocol. Subclasses implement the concrete transport."""

    transport = "abstract"

    # ---- GET-only (preflight) ----
    def get_course(self, course_id: int) -> dict[str, Any]:
        raise NotImplementedError

    def find_page(self, course_id: int, slug: str) -> dict[str, Any] | None:
        raise NotImplementedError

    def list_pages(self, course_id: int) -> list[dict[str, Any]]:
        raise NotImplementedError

    def list_assignments(self, course_id: int) -> list[dict[str, Any]]:
        raise NotImplementedError

    def list_assignment_groups(self, course_id: int) -> list[dict[str, Any]]:
        raise NotImplementedError

    def list_announcements(self, course_id: int) -> list[dict[str, Any]]:
        raise NotImplementedError

    def list_active_announcements(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    # ---- readback + writes ----
    def get_page(self, course_id: int, page_ref: str) -> dict[str, Any]:
        raise NotImplementedError

    def update_page(self, course_id: int, page_ref: str, *, body: str,
                    published: bool = True, front_page: bool = False) -> dict[str, Any]:
        raise NotImplementedError

    def set_front_page(self, course_id: int, page_id: Any) -> dict[str, Any]:
        """Make the given page the course front page (homepage).

        A course has exactly one front page; Canvas unsets the previous one.
        """
        raise NotImplementedError

    def get_assignment(self, course_id: int, assignment_id: str) -> dict[str, Any]:
        raise NotImplementedError

    def create_assignment(self, course_id: int, *, title: str, description: str,
                          assignment_group: str, points: int = 100,
                          grading_type: str = "percent", submission_type: str = "on_paper",
                          due_at: str = "", counts_toward_final_grade: bool = True,
                          published: bool = True) -> dict[str, Any]:
        raise NotImplementedError

    def get_announcement(self, course_id: int, topic_id: str) -> dict[str, Any]:
        raise NotImplementedError

    def create_announcement(self, course_id: int, *, title: str, message: str = "",
                            published: bool = True,
                            delayed_post_at: str | None = None) -> dict[str, Any]:
        raise NotImplementedError


class LiveDeployClient(DeployClient):
    """Real Canvas transport (production). Delegates to canonical helpers."""

    transport = "live"

    def __init__(self) -> None:
        from scripts.canvas_llm_phase22 import canvas_credentials as credentials
        from scripts.canvas_llm_phase22 import canvas_connection_manager as transport
        from scripts.canvas_llm_intake import canvas_readonly

        credentials.load_credentials()  # exports into os.environ for the live client
        self._transport = transport
        self._write = transport.Phase22LiveCanvasClient.from_env()
        self._read = canvas_readonly.CanvasReadOnly.from_env()

    # ---- GET-only ----
    def get_course(self, course_id: int) -> dict[str, Any]:
        return self._write.get_course(course_id)

    def find_page(self, course_id: int, slug: str) -> dict[str, Any] | None:
        return self._read.find_page(course_id, slug)

    def list_pages(self, course_id: int) -> list[dict[str, Any]]:
        return [self._norm_page(p) for p in self._read.list_pages(course_id)]

    def list_assignments(self, course_id: int) -> list[dict[str, Any]]:
        return self._read.list_assignments(course_id)

    def list_assignment_groups(self, course_id: int) -> list[dict[str, Any]]:
        return self._read.list_assignment_groups(course_id)

    def list_announcements(self, course_id: int) -> list[dict[str, Any]]:
        return self._read.list_announcements(course_id)

    def list_active_announcements(self) -> list[dict[str, Any]]:
        return self._read.list_active_announcements()

    # ---- readback + writes ----
    def _norm_page(self, page: dict[str, Any]) -> dict[str, Any]:
        return {
            "page_id": page.get("page_id") or page.get("id"),
            "url": page.get("url"),
            "title": page.get("title"),
            "body": page.get("body") or "",
            "published": page.get("published"),
            "front_page": page.get("front_page"),
        }

    def _norm_assignment(self, a: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": a.get("id"),
            "name": a.get("name") or a.get("title"),
            "points_possible": a.get("points_possible"),
            "grading_type": a.get("grading_type"),
            "submission_types": a.get("submission_types") or [],
            "due_at": a.get("due_at"),
            "omit_from_final_grade": a.get("omit_from_final_grade"),
            "assignment_group_id": a.get("assignment_group_id"),
        }

    def _norm_announcement(self, a: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": a.get("id"),
            "title": a.get("title"),
            "message": a.get("message") or "",
            "published": a.get("published"),
            "delayed_post_at": a.get("delayed_post_at"),
            "posted_at": a.get("posted_at"),
        }

    def get_page(self, course_id: int, page_ref: str) -> dict[str, Any]:
        return self._norm_page(self._write.get_page(course_id, page_ref))

    def update_page(self, course_id: int, page_ref: str, *, body: str,
                    published: bool = True, front_page: bool = False) -> dict[str, Any]:
        return self._norm_page(self._write.update_page(
            course_id, page_ref, body=body, published=published, front_page=front_page))

    def set_front_page(self, course_id: int, page_id: Any) -> dict[str, Any]:
        # Canonical Canvas endpoint: PUT /courses/:id/front_page {wiki_page_id}.
        # This unsets the prior front page and marks the target page as front.
        self._write.request(
            "PUT", f"/api/v1/courses/{course_id}/front_page",
            data={"wiki_page_id": str(page_id)},
        )
        return {"course_id": course_id, "page_id": str(page_id), "front_page": True}

    def get_assignment(self, course_id: int, assignment_id: str) -> dict[str, Any]:
        return self._norm_assignment(self._write.get_assignment(course_id, assignment_id))

    def create_assignment(self, course_id: int, *, title: str, description: str,
                          assignment_group: str, points: int = 100,
                          grading_type: str = "percent", submission_type: str = "on_paper",
                          due_at: str = "", counts_toward_final_grade: bool = True,
                          published: bool = True) -> dict[str, Any]:
        created = self._write.create_assignment(
            course_id, title=title, description=description, assignment_group=assignment_group,
            points=points, grading_type=grading_type, submission_type=submission_type,
            due_at=due_at, counts_toward_final_grade=counts_toward_final_grade,
            published=published)
        return self._norm_assignment(created)

    def get_announcement(self, course_id: int, topic_id: str) -> dict[str, Any]:
        return self._norm_announcement(self._write.get_announcement(course_id, topic_id))

    def create_announcement(self, course_id: int, *, title: str, message: str = "",
                            published: bool = True,
                            delayed_post_at: str | None = None) -> dict[str, Any]:
        created = self._write.create_announcement(
            course_id, title=title, message=message, published=published,
            delayed_post_at=delayed_post_at)
        return self._norm_announcement(created)


class FakeDeployClient(DeployClient):
    """In-memory Canvas store for tests. Mirrors normalized shapes exactly."""

    transport = "fake"

    def __init__(self, *, courses: dict[int, dict[str, Any]] | None = None) -> None:
        self.courses: dict[int, dict[str, Any]] = courses or {}
        self.pages: dict[tuple[int, str], dict[str, Any]] = {}
        self.assignments: dict[str, dict[str, Any]] = {}
        self.assignment_groups: dict[int, list[dict[str, Any]]] = {}
        self.announcements: dict[str, dict[str, Any]] = {}
        self._write_counts = {"POST": 0, "PUT": 0, "PATCH": 0, "DELETE": 0, "GET": 0}

    # ---- GET-only ----
    def get_course(self, course_id: int) -> dict[str, Any]:
        if course_id not in self.courses:
            raise DeployClientError(f"course not found: {course_id}")
        return self.courses[course_id]

    def find_page(self, course_id: int, slug: str) -> dict[str, Any] | None:
        return self.pages.get((course_id, slug))

    def list_pages(self, course_id: int) -> list[dict[str, Any]]:
        return [p for (cid, _slug), p in self.pages.items() if cid == course_id]

    def list_assignments(self, course_id: int) -> list[dict[str, Any]]:
        return [a for a in self.assignments.values() if a.get("course_id") == course_id]

    def list_assignment_groups(self, course_id: int) -> list[dict[str, Any]]:
        return self.assignment_groups.get(course_id, [])

    def list_announcements(self, course_id: int) -> list[dict[str, Any]]:
        return [a for a in self.announcements.values() if a.get("course_id") == course_id]

    def list_active_announcements(self) -> list[dict[str, Any]]:
        # Active = not future-scheduled (delayed_post_at None or in the past).
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        out = []
        for a in self.announcements.values():
            dp = a.get("delayed_post_at")
            if not dp:
                out.append(a)
                continue
            try:
                if datetime.fromisoformat(dp.replace("Z", "+00:00")) <= now:
                    out.append(a)
            except ValueError:
                out.append(a)
        return out

    # ---- readback + writes ----
    def get_page(self, course_id: int, page_ref: str) -> dict[str, Any]:
        key = (course_id, page_ref)
        if key not in self.pages:
            # allow lookup by page_id too
            for k, v in self.pages.items():
                if str(v.get("page_id")) == str(page_ref):
                    return v
            raise DeployClientError(f"page not found: {page_ref}")
        return self.pages[key]

    def update_page(self, course_id: int, page_ref: str, *, body: str,
                    published: bool = True, front_page: bool = False) -> dict[str, Any]:
        self._write_counts["PUT"] += 1
        page = self.get_page(course_id, page_ref)
        page["body"] = body
        page["published"] = published
        page["front_page"] = front_page
        return page

    def set_front_page(self, course_id: int, page_id: Any) -> dict[str, Any]:
        self._write_counts["PUT"] += 1
        target = None
        for (cid, _slug), page in self.pages.items():
            if cid == course_id:
                if str(page.get("page_id")) == str(page_id):
                    target = page
                    page["front_page"] = True
                else:
                    page["front_page"] = False
        if target is None:
            raise DeployClientError(f"page not found for set_front_page: {page_id}")
        return target

    def get_assignment(self, course_id: int, assignment_id: str) -> dict[str, Any]:
        a = self.assignments.get(str(assignment_id))
        if not a or a.get("course_id") != course_id:
            raise DeployClientError(f"assignment not found: {assignment_id}")
        return a

    def create_assignment(self, course_id: int, *, title: str, description: str,
                          assignment_group: str, points: int = 100,
                          grading_type: str = "percent", submission_type: str = "on_paper",
                          due_at: str = "", counts_toward_final_grade: bool = True,
                          published: bool = True) -> dict[str, Any]:
        gid = None
        for g in self.list_assignment_groups(course_id):
            if g.get("name") == assignment_group:
                gid = g.get("id")
                break
        if gid is None:
            raise DeployClientError(f"assignment group not found: {assignment_group}")
        self._write_counts["POST"] += 1
        aid = f"asn-{len(self.assignments) + 1}"
        a = {
            "id": aid, "course_id": course_id, "name": title,
            "assignment_group_id": gid, "assignment_group": assignment_group,
            "points_possible": points, "grading_type": grading_type,
            "submission_types": [submission_type], "due_at": due_at,
            "omit_from_final_grade": not counts_toward_final_grade,
            "published": published,
        }
        self.assignments[aid] = a
        return a

    def get_announcement(self, course_id: int, topic_id: str) -> dict[str, Any]:
        a = self.announcements.get(str(topic_id))
        if not a or a.get("course_id") != course_id:
            raise DeployClientError(f"announcement not found: {topic_id}")
        return a

    def create_announcement(self, course_id: int, *, title: str, message: str = "",
                            published: bool = True,
                            delayed_post_at: str | None = None) -> dict[str, Any]:
        self._write_counts["POST"] += 1
        tid = f"topic-{len(self.announcements) + 1}"
        a = {
            "id": tid, "course_id": course_id, "title": title, "message": message,
            "published": published, "delayed_post_at": delayed_post_at,
            "posted_at": None if delayed_post_at else "now",
        }
        self.announcements[tid] = a
        return a

    def seed_page(self, course_id: int, slug: str, *, title: str, body: str,
                  published: bool = True, front_page: bool = False) -> dict[str, Any]:
        page = {"page_id": f"page-{course_id}-{slug}", "url": slug, "course_id": course_id,
                "title": title, "body": body, "published": published, "front_page": front_page}
        self.pages[(course_id, slug)] = page
        return page

    def seed_assignment(self, course_id: int, name: str, *, assignment_group: str) -> dict[str, Any]:
        gid = None
        for g in self.list_assignment_groups(course_id):
            if g.get("name") == assignment_group:
                gid = g.get("id")
                break
        if gid is None:
            gid = f"grp-{assignment_group}"
            self.assignment_groups.setdefault(course_id, []).append({"id": gid, "name": assignment_group})
        aid = f"asn-{len(self.assignments) + 1}"
        a = {"id": aid, "course_id": course_id, "name": name,
             "assignment_group_id": gid, "assignment_group": assignment_group,
             "points_possible": 100, "grading_type": "percent",
             "submission_types": ["on_paper"], "due_at": "", "omit_from_final_grade": False}
        self.assignments[aid] = a
        return a


def build_client(*, production: bool = False, fake: DeployClient | None = None) -> DeployClient:
    """Return a live client (production) or a fake client (tests/dry-run default)."""
    if fake is not None:
        return fake
    if production:
        return LiveDeployClient()
    # Non-production: fake client with a minimal sandbox course is NOT safe to
    # write against; callers must explicitly request production for real writes.
    raise DeployClientError(
        "no Canvas transport: set production=True for real writes (or pass a fake client for tests)")


def command_self_test() -> int:
    fake = FakeDeployClient(courses={26404: {"id": 26404, "name": "Math", "workflow_state": "available"}})
    fake.assignment_groups[26404] = [{"id": "60321", "name": "Homework/Class Work"}]
    fake.seed_page(26404, "q2w3-october-26-30-2026", title="Q2W3", body="<div id='kl_wrapper_3'>x</div>")
    # page lookup + update + readback
    p = fake.get_page(26404, "q2w3-october-26-30-2026")
    assert p["page_id"] and "kl_wrapper_3" in p["body"]
    fake.update_page(26404, "q2w3-october-26-30-2026", body="<div id='kl_wrapper_3'>y</div>")
    assert "y" in fake.get_page(26404, "q2w3-october-26-30-2026")["body"]
    # assignment create + readback
    a = fake.create_assignment(26404, title="SM5: Lesson 39 Homework", description="",
                               assignment_group="Homework/Class Work", due_at="2026-10-27T03:59:00Z")
    assert fake.get_assignment(26404, a["id"])["name"] == "SM5: Lesson 39 Homework"
    # announcement create + readback
    ann = fake.create_announcement(26404, title="Math Canvas Weekly Update", message="<p>hi</p>",
                                   delayed_post_at="2026-10-23T20:00:00Z")
    assert fake.get_announcement(26404, ann["id"])["delayed_post_at"].startswith("2026-10-23")
    print("PASS canvas-deploy client self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
