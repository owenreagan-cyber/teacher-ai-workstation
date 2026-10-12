#!/usr/bin/env python3
"""GET-count instrumentation for the read-only mastery/grade-check transport.

Wraps any ``GradeReader`` and counts each read method invocation so a live
preview can report exact GET counts and endpoint families. It never issues
network itself; it delegates to the wrapped reader (which is proven GET-only).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from scripts.canvas_llm_grade_check.reader import (
    Assignment,
    AssignmentGroup,
    GradeReader,
    Student,
    Submission,
)


@dataclass
class NetworkSummary:
    get: int = 0
    errors: int = 0
    post: int = 0
    put: int = 0
    patch: int = 0
    delete: int = 0
    endpoint_families: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "GET": self.get,
            "errors": self.errors,
            "POST": self.post,
            "PUT": self.put,
            "PATCH": self.patch,
            "DELETE": self.delete,
            "endpoint_families": sorted(set(self.endpoint_families)),
        }


class CountingReader:
    """Counts read-method calls over an underlying GradeReader."""

    def __init__(self, inner: GradeReader):
        self.inner = inner
        self.network = NetworkSummary()

    def _record(self, family: str) -> None:
        self.network.get += 1
        self.network.endpoint_families.append(family)

    def list_students(self, course_id: int) -> list[Student]:
        self._record("enrollments(grades)")
        return self.inner.list_students(course_id)

    def list_assignments(self, course_id: int) -> list[Assignment]:
        self._record("assignments")
        return self.inner.list_assignments(course_id)

    def list_assignment_groups(self, course_id: int) -> list[AssignmentGroup]:
        self._record("assignment_groups")
        return self.inner.list_assignment_groups(course_id)

    def list_submissions(self, course_id: int) -> list[Submission]:
        self._record("submissions")
        return self.inner.list_submissions(course_id)


def command_self_test() -> int:
    class Stub:
        def list_students(self, c): return []
        def list_assignments(self, c): return []
        def list_assignment_groups(self, c): return []
        def list_submissions(self, c): return []

    cr = CountingReader(Stub())
    cr.list_students(26404)
    cr.list_assignments(26404)
    cr.list_assignment_groups(26404)
    cr.list_submissions(26404)
    assert cr.network.get == 4
    assert cr.network.post == 0 and cr.network.put == 0 and cr.network.patch == 0 and cr.network.delete == 0
    assert len(cr.network.endpoint_families) == 4

    print("PASS counting reader self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
