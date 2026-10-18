#!/usr/bin/env python3
"""GET-only audit of Reading/Spelling course 26442 for Q1W8.

Checks whether the Reading gradebook contains assignments corresponding to
Reading Mastery Test 30 / Mastery Test 30 and Fluency Checkout 30 / Checkout 30,
matching live pacing evidence (Tue 9/8 Reading Mastery Lesson 30; Wed 9/9 test;
pacing tracker lists CO (30): ___/21 and MT (30): ___/21).

READ-ONLY: no writes, no creates, no modification.
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

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_credentials as credentials  # noqa: E402

COURSE_ID = 26442
# Pacing evidence: Wed 9/9 test for Reading Mastery Lesson 30; tracker lists
# CO (30) and MT (30). Respect "Reading Mastery Test 30", "Mastery Test 30",
# "Fluency Checkout 30", "Checkout 30".
TARGETS = [
    "mastery test 30",
    "reading mastery test 30",
    "mastery 30",
    "checkout 30",
    "fluency checkout 30",
    "check out 30",
]


@dataclass
class AssignmentRow:
    id: int
    name: str
    assignment_group_id: int | None
    assignment_group_name: str | None
    published: bool
    due_at: str | None
    unlock_at: str | None
    lock_at: str | None
    grading_type: str | None
    html_url: str | None


class ReaderError(RuntimeError):
    pass


class AuditReader:
    """GET-only Canvas reader for the assignment audit.

    Only GET requests are issued; there are no write or create methods.
    """

    def __init__(self, base_url: str, token: str, *, timeout: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def _request_url(self, url: str) -> str:
        return url if url.startswith("http") else f"{self.base_url}{url}"

    def _paginate(self, path: str, params: dict[str, object] | None = None) -> list[dict]:
        merged = {"per_page": 100}
        if params:
            merged.update(params)  # type: ignore[arg-type]
        url = f"{path}?{urllib.parse.urlencode(merged, doseq=True)}"
        items: list[dict] = []
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

    def list_assignments(self, course_id: int) -> list[AssignmentRow]:
        rows = self._paginate(f"/api/v1/courses/{course_id}/assignments", {})
        return [
            AssignmentRow(
                id=int(a["id"]),
                name=a.get("name") or "",
                assignment_group_id=int(a["assignment_group_id"])
                if a.get("assignment_group_id") is not None
                else None,
                assignment_group_name=None,  # filled after group query
                published=bool(a.get("published")),
                due_at=a.get("due_at"),
                unlock_at=a.get("unlock_at"),
                lock_at=a.get("lock_at"),
                grading_type=a.get("grading_type"),
                html_url=a.get("html_url"),
            )
            for a in rows
            if a.get("id") is not None
        ]

    def list_assignment_groups(self, course_id: int) -> dict[int, str]:
        rows = self._paginate(f"/api/v1/courses/{course_id}/assignment_groups", {})
        return {int(g["id"]): g.get("name") or "" for g in rows if g.get("id") is not None}


def normalize_title(name: str) -> str:
    return " ".join(name.lower().split())


def title_matches(read_title: str, targets: list[str]) -> bool:
    n = normalize_title(read_title)
    for t in targets:
        # exact substring match on normalized title
        if t in n:
            return True
    return False


def main() -> int:
    credentials.load_credentials()
    reader = AuditReader(os.environ["CANVAS_BASE_URL"], os.environ["CANVAS_TOKEN"])

    groups = reader.list_assignment_groups(COURSE_ID)
    assignments = reader.list_assignments(COURSE_ID)
    for a in assignments:
        a.assignment_group_name = groups.get(a.assignment_group_id) if a.assignment_group_id else None

    print(f"Reading/Spelling course {COURSE_ID}: {len(assignments)} assignments, "
          f"{len(groups)} groups")
    print("=" * 72)

    found: dict[str, list[AssignmentRow]] = {"mastery_test_30": [], "checkout_30": []}
    all_matches: list[AssignmentRow] = []

    for a in sorted(assignments, key=lambda x: x.name.lower()):
        if title_matches(a.name, TARGETS):
            all_matches.append(a)
            if any(t in normalize_title(a.name) for t in ["mastery test 30", "reading mastery test 30", "mastery 30"]):
                found["mastery_test_30"].append(a)
            if any(t in normalize_title(a.name) for t in ["checkout 30", "fluency checkout 30", "check out 30"]):
                found["checkout_30"].append(a)

    def render(a: AssignmentRow) -> str:
        parts = [
            f"  title: {a.name!r}",
            f"  id: {a.id}",
            f"  group: {a.assignment_group_name or '(none)'}",
            f"  published: {a.published}",
            f"  due: {a.due_at or '(none)'}",
            f"  unlock: {a.unlock_at or '(none)'}",
            f"  lock: {a.lock_at or '(none)'}",
            f"  grading_type: {a.grading_type or '(none)'}",
            f"  url: {a.html_url or '(none)'}",
        ]
        return "\n".join(parts)

    print("ALL ASSIGNMENTS MATCHING '30' (Test / Checkout / Mastery / Check Out):")
    if all_matches:
        for a in all_matches:
            print("-" * 30)
            print(render(a))
    else:
        print("  (none)")

    print()
    print("-" * 72)
    print("COMPLETE ASSIGNMENT LIST (id | published | due | group | title):")
    for a in sorted(assignments, key=lambda x: (x.name or "").lower()):
        due = a.due_at or "(none)"
        print(f"  {a.id} | pub={a.published} | due={due} | "
              f"{a.assignment_group_name or '(none)'} | {a.name!r}")

    print()
    print("=" * 72)
    print("RESULT")
    print(f"Mastery Test 30: {'FOUND' if found['mastery_test_30'] else 'MISSING'}")
    print(f"Checkout 30: {'FOUND' if found['checkout_30'] else 'MISSING'}")

    print()
    print("CANVAS WRITES PERFORMED: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
