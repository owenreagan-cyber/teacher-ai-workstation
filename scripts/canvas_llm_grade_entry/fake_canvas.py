#!/usr/bin/env python3
"""Deterministic offline Canvas fake for grade-entry tests and packet previews.

This fake never touches the network. It stores a tiny in-memory course with
rosters, assignments, and submission grades, and it enforces that only
``submission[posted_grade]`` may be written.
"""
from __future__ import annotations

import copy
from typing import Any

from . import grade_entry as ge


class FakeCanvas:
    """In-memory Canvas subset: roster, assignments, submissions, grade writes."""

    def __init__(self, *, course_id: int, course_name: str, course_code: str,
                 assignments: list[dict[str, Any]], roster: list[dict[str, Any]],
                 grades: dict[tuple[int, int], float | None] | None = None) -> None:
        self.course = {"id": course_id, "name": course_name, "course_code": course_code}
        self.assignments = copy.deepcopy(assignments)
        self.roster = copy.deepcopy(roster)
        self.grades = dict(grades or {})
        self.write_log: list[dict[str, Any]] = []
        self.write_attempts: list[dict[str, Any]] = []

    # --- transport -----------------------------------------------------
    def transport(self, method: str, path: str, data: dict[str, Any] | None) -> Any:
        method = method.upper()
        if path == f"/api/v1/courses/{self.course['id']}":
            return dict(self.course)
        if path.startswith(f"/api/v1/courses/{self.course['id']}/assignments?"):
            return copy.deepcopy(self.assignments)
        if path.startswith(f"/api/v1/courses/{self.course['id']}/enrollments?"):
            return [{"user": {"id": r["student_id"], "name": r["name"],
                              "sortable_name": r.get("sortable_name", "")}} for r in self.roster]
        if path.startswith(f"/api/v1/courses/{self.course['id']}/students/submissions?"):
            rows = []
            for (sid, aid), score in self.grades.items():
                rows.append({"user_id": sid, "assignment_id": aid, "score": score})
            return rows
        if method == "PUT":
            return self._write(path, data or {})
        raise AssertionError(f"fake canvas: unexpected {method} {path}")

    def _write(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        self.write_attempts.append({"path": path, "data": dict(data)})
        ge.assert_write_payload_is_bounded(data)
        parts = path.rstrip("/").split("/")
        course_id = int(parts[4])
        assignment_id = int(parts[6])
        student_id = int(parts[8])
        if course_id != self.course["id"]:
            raise ge.GradeEntryError(f"fake canvas: wrong course {course_id}")
        if not any(int(a["id"]) == assignment_id for a in self.assignments):
            raise ge.GradeEntryError(f"fake canvas: unknown assignment {assignment_id}")
        if not any(int(r["student_id"]) == student_id for r in self.roster):
            raise ge.GradeEntryError(f"fake canvas: unknown student {student_id}")
        grade = ge.parse_grade(data["submission[posted_grade]"])
        self.grades[(student_id, assignment_id)] = grade
        record = {"id": f"sub-{student_id}-{assignment_id}", "user_id": student_id,
                  "assignment_id": assignment_id, "score": grade,
                  "grade": ge.format_grade(grade), "workflow_state": "graded"}
        self.write_log.append(record)
        return record

    def client(self) -> ge.CanvasGradeClient:
        return ge.CanvasGradeClient("https://fake.invalid", "fake-token",
                                    transport=self.transport)

    # --- helpers -------------------------------------------------------
    def grade_of(self, student_id: int, assignment_id: int) -> float | None:
        return self.grades.get((student_id, assignment_id))

    def snapshot(self) -> dict[tuple[int, int], float | None]:
        return dict(self.grades)


def ela4_course() -> FakeCanvas:
    """Deterministic ELA4-like course for tests."""
    assignments = [
        {"id": 1042766, "name": "ELA4A: Personal Narrative Outline"},
        {"id": 1042767, "name": "ELA4A: Personal Narrative Rough Draft"},
        {"id": 1042769, "name": "ELA4A: Personal Narrative Final Draft"},
        {"id": 1042770, "name": "ELA4A: Ch. 3 Test"},
    ]
    roster = [
        {"student_id": 9001, "name": "Hannah Bradshaw"},
        {"student_id": 9002, "name": "Jasmin Brar"},
        {"student_id": 9003, "name": "Ava Venne"},
        {"student_id": 9004, "name": "Nathan Snapp"},
    ]
    grades = {
        (9001, 1042769): 88.0,   # will need an update to 94
        (9002, 1042769): 89.0,   # already correct
        (9003, 1042769): 90.0,   # will need an update to 97
        (9004, 1042769): None,   # skipped, must remain untouched
        (9001, 1042770): 75.0,   # other assignment, must remain untouched
        (9003, 1042770): 82.0,   # other assignment, must remain untouched
    }
    return FakeCanvas(course_id=28171, course_name="Language Arts - 4th Grade",
                      course_code="15-ELA4", assignments=assignments,
                      roster=roster, grades=grades)
