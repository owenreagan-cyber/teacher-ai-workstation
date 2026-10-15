#!/usr/bin/env python3
"""Read-only Canvas grade data source.

Only GET requests are ever issued. The live reader loads credentials through
``canvas_credentials.load_credentials()`` and never prints the token. A
``GradeReader`` is injectable so deterministic tests can supply synthetic
student/grade fixtures without touching Canvas.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_credentials as credentials  # noqa: E402


class ReaderError(RuntimeError):
    """Raised when a read-only Canvas fetch fails."""


@dataclass(frozen=True)
class Student:
    user_id: int
    name: str
    sortable_name: str | None = None
    current_score: float | None = None
    current_grade: str | None = None
    final_score: float | None = None
    eligible_from: str | None = None

    @property
    def first_name(self) -> str:
        if self.name and self.name.strip():
            return self.name.strip().split()[0]
        if self.sortable_name and self.sortable_name.strip():
            # "Alpha, Student" -> "Student"
            parts = [p for p in self.sortable_name.split(",") if p.strip()]
            if len(parts) > 1 and parts[1].strip():
                return parts[1].strip().split()[0]
        return "Student"

    @property
    def average(self) -> float | None:
        """Current overall course average (current_score preferred)."""
        if self.current_score is not None:
            return self.current_score
        return self.final_score


@dataclass(frozen=True)
class Assignment:
    id: int
    name: str
    due_at: str | None = None
    assignment_group_id: int | None = None
    grading_type: str | None = None


@dataclass(frozen=True)
class AssignmentGroup:
    id: int
    name: str


@dataclass(frozen=True)
class Submission:
    id: int
    user_id: int
    assignment_id: int
    score: float | None = None
    grade: str | None = None
    missing: bool = False
    late: bool = False
    excused: bool = False
    workflow_state: str | None = None


class GradeReader(Protocol):
    def list_students(self, course_id: int) -> list[Student]: ...

    def list_assignments(self, course_id: int) -> list[Assignment]: ...

    def list_assignment_groups(self, course_id: int) -> list[AssignmentGroup]: ...

    def list_submissions(self, course_id: int) -> list[Submission]: ...


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class LiveGradeReader:
    """GET-only Canvas reader. No write methods exist."""

    def __init__(self, base_url: str, token: str, *, timeout: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    @classmethod
    def from_env(cls) -> "LiveGradeReader":
        credentials.load_credentials()
        return cls(
            os.environ["CANVAS_BASE_URL"],
            os.environ["CANVAS_TOKEN"],
        )

    def _get(self, path: str) -> Any:
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                text = response.read().decode("utf-8")
                return json.loads(text) if text else None
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = (exc.read() or b"").decode("utf-8", "replace")[:300]
            except Exception:  # noqa: BLE001
                detail = ""
            raise ReaderError(f"GET {path} -> HTTP {exc.code}: {detail or exc.reason}") from exc
        except urllib.error.URLError as exc:
            raise ReaderError(f"GET {path} -> network: {exc.reason}") from exc

    def _request_url(self, url: str) -> str:
        return url if url.startswith("http") else f"{self.base_url}{url}"

    def _paginate(self, path: str, params: dict[str, Any]) -> list[Any]:
        merged = {"per_page": 100}
        merged.update(params)
        url = f"{path}?{urllib.parse.urlencode(merged, doseq=True)}"
        items: list[Any] = []
        for _ in range(200):
            req = urllib.request.Request(
                self._request_url(url),
                headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"},
                method="GET",
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    text = response.read().decode("utf-8")
                    link = response.headers.get("Link", "")
            except urllib.error.HTTPError as exc:
                detail = ""
                try:
                    detail = (exc.read() or b"").decode("utf-8", "replace")[:300]
                except Exception:  # noqa: BLE001
                    detail = ""
                raise ReaderError(f"GET {url} -> HTTP {exc.code}: {detail or exc.reason}") from exc
            except urllib.error.URLError as exc:
                raise ReaderError(f"GET {url} -> network: {exc.reason}") from exc

            data = json.loads(text) if text else []
            items.extend(data if isinstance(data, list) else [data])
            nxt = None
            for part in link.split(","):
                if 'rel="next"' in part:
                    s, e = part.find("<"), part.find(">")
                    if 0 <= s < e:
                        nxt = part[s + 1 : e]
            if not nxt:
                break
            url = nxt
        return items

    def list_students(self, course_id: int) -> list[Student]:
        # Enrollments with computed grades: the source of student names + averages.
        enrollments = self._paginate(
            f"/api/v1/courses/{course_id}/enrollments",
            {
                "type[]": "StudentEnrollment",
                "state[]": "active",
                "include[]": "grades",
            },
        )
        students: list[Student] = []
        for e in enrollments:
            user = e.get("user") or {}
            grades = e.get("grades") or {}
            # Effective enrollment eligibility date: prefer the authoritative
            # enrollment start_at; fall back to the enrollment record creation
            # date. A local teacher override can supersede this if configured.
            eligible_from = e.get("start_at") or e.get("created_at")
            students.append(
                Student(
                    user_id=int(e.get("user_id") or user.get("id") or 0),
                    name=user.get("name") or "",
                    sortable_name=user.get("sortable_name"),
                    current_score=_as_float(grades.get("current_score")),
                    current_grade=grades.get("current_grade"),
                    final_score=_as_float(grades.get("final_score")),
                    eligible_from=eligible_from,
                )
            )
        return students

    def list_assignments(self, course_id: int) -> list[Assignment]:
        rows = self._paginate(f"/api/v1/courses/{course_id}/assignments", {})
        return [
            Assignment(
                id=int(a["id"]),
                name=a.get("name") or "",
                due_at=a.get("due_at"),
                assignment_group_id=int(a["assignment_group_id"])
                if a.get("assignment_group_id") is not None
                else None,
                grading_type=a.get("grading_type"),
            )
            for a in rows
            if a.get("id") is not None
        ]

    def list_assignment_groups(self, course_id: int) -> list[AssignmentGroup]:
        rows = self._paginate(f"/api/v1/courses/{course_id}/assignment_groups", {})
        return [
            AssignmentGroup(id=int(g["id"]), name=g.get("name") or "")
            for g in rows
            if g.get("id") is not None
        ]

    def list_submissions(self, course_id: int) -> list[Submission]:
        # One call per course: all students' submissions in a single paginated GET.
        rows = self._paginate(
            f"/api/v1/courses/{course_id}/students/submissions",
            {"student_ids[]": "all"},
        )
        submissions: list[Submission] = []
        for s in rows:
            submissions.append(
                Submission(
                    id=int(s["id"]),
                    user_id=int(s["user_id"]),
                    assignment_id=int(s["assignment_id"]),
                    score=_as_float(s.get("score")),
                    grade=s.get("grade"),
                    missing=bool(s.get("missing")),
                    late=bool(s.get("late")),
                    excused=bool(s.get("excused")),
                    workflow_state=s.get("workflow_state"),
                )
            )
        return submissions


def reader_has_no_writes() -> bool:
    source = Path(__file__).read_text().lower()
    marker = "def reader_has_no_writes"
    idx = source.find(marker)
    scan = source[:idx] if idx >= 0 else source
    forbidden = ("requests.post", "requests.put", "requests.delete", "requests.patch")
    return not any(t in scan for t in forbidden)


def command_self_test() -> int:
    assert reader_has_no_writes()
    s = Student(user_id=1, name="Student Alpha", current_score=84.5)
    assert s.first_name == "Student"
    assert s.average == 84.5
    assert s.eligible_from is None  # default: eligible from the beginning
    s2 = Student(user_id=2, name="", sortable_name="Alpha, Student", current_score=None, final_score=88)
    assert s2.first_name == "Student"
    assert s2.average == 88
    s3 = Student(user_id=3, name="Student Gamma", eligible_from="2026-09-12T07:42:42Z")
    assert s3.eligible_from == "2026-09-12T07:42:42Z"
    assert _as_float("84.99") == 84.99
    assert _as_float("MI") is None
    print("PASS grade-check reader self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
