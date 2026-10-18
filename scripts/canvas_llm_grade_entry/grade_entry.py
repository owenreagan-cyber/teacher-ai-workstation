#!/usr/bin/env python3
"""Bounded Canvas grade-entry capability (disabled by default).

Reads:  course metadata, assignments, /enrollments roster, /students/submissions
Write:  PUT /courses/:id/assignments/:aid/submissions/:uid  -> submission[posted_grade]

Hard rules enforced here:
- disabled unless ``GRADE_ENTRY_ENABLED=1``
- must be enabled by the human owner (``enable(owner=...)``) before any write
- every write must match a signed approval packet exactly
- student matching is exact after normalization; the roster itself must be
  free of duplicate normalized names (otherwise everything fails closed)
- only ``posted_grade`` is ever sent; no comments, status, missing/late/excused
- only one assignment and one course are ever touched
- never logs tokens/secrets

Usage:
    python3 -m scripts.canvas_llm_grade_entry.cli packet --request request.json
    python3 -m scripts.canvas_llm_grade_entry.cli self-test
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:  # pragma: no cover - import convenience
    sys.path.insert(0, str(REPO_ROOT))

ENABLE_ENV = "GRADE_ENTRY_ENABLED"
ENABLE_VALUE = "1"
ALLOWED_COURSE_IDS = frozenset({28171})  # ELA4 (Language Arts 4th Grade)
PACKET_SCHEMA = "grade_entry_approval_packet_v1"
REQUEST_SCHEMA = "grade_entry_request_v1"
PACKET_VERSION = 1

# Only these submission attributes may ever appear in a write payload.
ALLOWED_SUBMISSION_FIELDS = ("posted_grade",)
FORBIDDEN_SUBMISSION_FIELDS = (
    "comment",
    "text_comment",
    "group_comment",
    "excuse",
    "late",
    "missing",
    "seconds_late_override",
    "rubric_assessment",
    "submission_type",
)
TOKEN_PATTERNS = (
    re.compile(r"Bearer\s+\S+", re.I),
    re.compile(r"access_token[=:]\s*\S+", re.I),
    re.compile(r"token[=:]\s*\S+", re.I),
)


class GradeEntryError(RuntimeError):
    """Raised when a grade-entry operation must fail closed."""


def redact(text: str) -> str:
    out = text
    for pattern in TOKEN_PATTERNS:
        out = pattern.sub("[REDACTED]", out)
    return out


def normalize_name(value: str) -> str:
    """Case/punctuation-insensitive name key used for exact matching."""
    text = unicodedata.normalize("NFKD", value or "").casefold()
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[&]", " and ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_grade(value: Any) -> float:
    """Parse an explicitly supplied numeric grade. No rounding, no conversion."""
    if isinstance(value, bool):
        raise GradeEntryError("grade must be numeric, not boolean")
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not re.fullmatch(r"-?\d+(\.\d+)?", text):
        raise GradeEntryError(f"grade is not an explicit plain number: {value!r}")
    return float(text)


def grades_equal(left: float | None, right: float) -> bool:
    if left is None:
        return False
    return abs(float(left) - float(right)) < 1e-9


def format_grade(value: float | None) -> str:
    if value is None:
        return "(blank)"
    text = f"{float(value):.2f}".rstrip("0").rstrip(".")
    return text or "0"


# --------------------------------------------------------------------------
# Enablement (disabled by default)
# --------------------------------------------------------------------------

_enabled = False
_enabled_by: str | None = None

# Active approved write scope. Set only while applying a specific packet so
# that direct write calls cannot exceed the approved student/assignment pairs.
_active_scope: dict[str, Any] | None = None


class approved_write_scope:
    """Context manager restricting writes to one approved packet's exact pairs."""

    def __init__(self, packet: "ApprovalPacket") -> None:
        self.packet = packet

    def __enter__(self) -> "approved_write_scope":
        global _active_scope
        course_id = int(self.packet.course["course_id"])
        assignment_id = int(self.packet.assignment["assignment_id"])
        _active_scope = {
            "course_id": course_id,
            "assignment_id": assignment_id,
            "student_ids": frozenset(int(c["student_id"]) for c in self.packet.proposed_changes),
            "packet_hash": self.packet.packet_hash,
        }
        return self

    def __exit__(self, *exc_info: Any) -> None:
        global _active_scope
        _active_scope = None


def feature_enabled() -> bool:
    """Environment gate. Absent or any value other than '1' means disabled."""
    return os.environ.get(ENABLE_ENV, "").strip() == ENABLE_VALUE


def enable(*, owner: str) -> None:
    """Explicit human enablement. Required in addition to the env gate."""
    global _enabled, _enabled_by
    if not feature_enabled():
        raise GradeEntryError(
            f"{ENABLE_ENV}={ENABLE_VALUE} is required before grade writes can be enabled"
        )
    if not (owner or "").strip():
        raise GradeEntryError("grade entry requires a named human owner to enable it")
    _enabled = True
    _enabled_by = owner.strip()


def disable() -> None:
    global _enabled, _enabled_by
    _enabled = False
    _enabled_by = None


def is_enabled() -> bool:
    return _enabled


def enabled_by() -> str | None:
    return _enabled_by


# --------------------------------------------------------------------------
# Request + packet data model
# --------------------------------------------------------------------------


@dataclass
class CourseRef:
    course_id: int
    course_code: str | None = None
    name: str | None = None


@dataclass
class AssignmentRef:
    assignment_id: int
    name: str


@dataclass
class GradeChange:
    student_label: str
    student_id: int
    student_name: str
    current_grade: float | None
    proposed_grade: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SkippedStudent:
    student_label: str
    student_id: int | None
    student_name: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ApprovalPacket:
    course: dict[str, Any]
    assignment: dict[str, Any]
    proposed_changes: list[dict[str, Any]]
    skipped: list[dict[str, Any]]
    total_writes: int
    other_assignments_touched: int
    other_courses_touched: int
    packet_hash: str = ""
    schema: str = PACKET_SCHEMA
    version: int = PACKET_VERSION
    created_at: str = ""
    status: str = "AWAITING_APPROVAL"

    def compute_hash(self) -> str:
        payload = {
            "schema": self.schema,
            "version": self.version,
            "course": self.course,
            "assignment": self.assignment,
            "proposed_changes": self.proposed_changes,
            "skipped": self.skipped,
            "total_writes": self.total_writes,
            "other_assignments_touched": self.other_assignments_touched,
            "other_courses_touched": self.other_courses_touched,
        }
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()

    def seal(self) -> "ApprovalPacket":
        self.created_at = self.created_at or datetime.now(timezone.utc).isoformat()
        self.packet_hash = self.compute_hash()
        return self

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return path

    @classmethod
    def load(cls, path: Path) -> "ApprovalPacket":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        packet = cls(**data)
        if packet.packet_hash != packet.compute_hash():
            raise GradeEntryError("approval packet hash mismatch (packet was altered)")
        return packet

    def render(self) -> str:
        lines = [
            "COURSE / ASSIGNMENT",
            f"COURSE: {self.course.get('name')} (id {self.course.get('course_id')}, "
            f"code {self.course.get('course_code')})",
            f"ASSIGNMENT: {self.assignment.get('name')} "
            f"(id {self.assignment.get('assignment_id')})",
            "",
            "PROPOSED GRADE CHANGES:",
            "Student | Canvas student id | Current grade | Proposed grade",
        ]
        for change in self.proposed_changes:
            lines.append(
                f"{change['student_name']} | {change['student_id']} | "
                f"{format_grade(change.get('current_grade'))} | "
                f"{format_grade(change['proposed_grade'])}"
            )
        lines += ["", "STUDENTS SKIPPED:"]
        if self.skipped:
            for row in self.skipped:
                sid = row.get("student_id")
                lines.append(
                    f"{row['student_name']} | {sid if sid is not None else '(unmatched)'} | "
                    f"{row['reason']}"
                )
        else:
            lines.append("(none)")
        lines += [
            "",
            f"TOTAL WRITES: {self.total_writes}",
            f"OTHER ASSIGNMENTS TOUCHED: {self.other_assignments_touched}",
            f"OTHER COURSES TOUCHED: {self.other_courses_touched}",
            "",
            f"PACKET HASH: {self.packet_hash}",
            f"STATUS: {self.status}",
        ]
        return "\n".join(lines)


# --------------------------------------------------------------------------
# Canvas transport (read + the single bounded write)
# --------------------------------------------------------------------------


class CanvasGradeClient:
    """Minimal Canvas client: roster/submission reads and one grade write."""

    def __init__(self, base_url: str, token: str, *, timeout: int = 60,
                 transport: Callable[[str, str, dict[str, Any] | None], Any] | None = None) -> None:
        self.base_url = (base_url or "").rstrip("/")
        self.token = token or ""
        self.timeout = timeout
        self._injected = transport

    @classmethod
    def from_env(cls) -> "CanvasGradeClient":
        base = os.environ.get("CANVAS_BASE_URL", "").strip()
        token = os.environ.get("CANVAS_TOKEN", "").strip() or os.environ.get("CANVAS_API_TOKEN", "").strip()
        if not base or not token:
            raise GradeEntryError("BLOCKED: CANVAS_BASE_URL and CANVAS_TOKEN are required")
        return cls(base, token)

    def request(self, method: str, path: str, data: dict[str, Any] | None = None) -> Any:
        if self._injected is not None:
            return self._injected(method, path, data)
        url = f"{self.base_url}{path}"
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/json"}
        body = None
        if data is not None:
            body = urllib.parse.urlencode(data, doseq=True).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        req = urllib.request.Request(url, data=body, headers=headers, method=method.upper())
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                text = response.read().decode("utf-8")
                return json.loads(text) if text else {}
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = (exc.read() or b"").decode("utf-8", "replace")[:300]
            except Exception:  # noqa: BLE001
                detail = ""
            raise GradeEntryError(
                redact(f"{method.upper()} {path} -> HTTP {exc.code}: {detail or exc.reason}")
            ) from exc
        except urllib.error.URLError as exc:
            raise GradeEntryError(redact(f"{method.upper()} {path} -> network: {exc.reason}")) from exc

    def _absolute(self, url_or_path: str) -> str:
        """Canvas Link headers are absolute; paths are relative to base_url."""
        if url_or_path.startswith("http://") or url_or_path.startswith("https://"):
            return url_or_path
        return f"{self.base_url}{url_or_path}"

    def _paginate(self, path: str, params: dict[str, Any] | None = None) -> list[Any]:
        merged = {"per_page": 100}
        merged.update(params or {})
        url = f"{path}?{urllib.parse.urlencode(merged, doseq=True)}"
        items: list[Any] = []
        for _ in range(200):
            if self._injected is not None:
                data = self._injected("GET", url, None)
                rows = data if isinstance(data, list) else [data]
                if len(rows) >= int(merged["per_page"]):
                    raise GradeEntryError(
                        "BLOCKED: injected transport returned a full page; it cannot "
                        "follow Canvas Link-header pagination, so readback would be "
                        "silently truncated"
                    )
                items.extend(rows)
                break
            req = urllib.request.Request(
                self._absolute(url),
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
                raise GradeEntryError(redact(f"GET {url} -> HTTP {exc.code}: {detail}")) from exc
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

    # --- reads ---------------------------------------------------------
    def get_course(self, course_id: int) -> dict[str, Any]:
        return self.request("GET", f"/api/v1/courses/{course_id}") or {}

    def list_assignments(self, course_id: int) -> list[dict[str, Any]]:
        return self._paginate(f"/api/v1/courses/{course_id}/assignments")

    def list_roster(self, course_id: int) -> list[dict[str, Any]]:
        rows = self._paginate(
            f"/api/v1/courses/{course_id}/enrollments",
            {"type[]": "StudentEnrollment", "state[]": "active"},
        )
        roster: list[dict[str, Any]] = []
        for row in rows:
            user = row.get("user") or {}
            uid = user.get("id")
            if uid is None:
                continue
            roster.append(
                {
                    "student_id": int(uid),
                    "name": user.get("name") or "",
                    "sortable_name": user.get("sortable_name") or "",
                }
            )
        return roster

    def list_submissions(self, course_id: int) -> list[dict[str, Any]]:
        rows = self._paginate(
            f"/api/v1/courses/{course_id}/students/submissions",
            {"student_ids[]": "all"},
        )
        return [
            {
                "student_id": int(r["user_id"]),
                "assignment_id": int(r["assignment_id"]),
                "score": r.get("score"),
                "grade": r.get("grade"),
                "workflow_state": r.get("workflow_state"),
            }
            for r in rows
            if r.get("user_id") is not None and r.get("assignment_id") is not None
        ]

    # --- the single bounded write --------------------------------------
    def write_grade(
        self,
        *,
        course_id: int,
        assignment_id: int,
        student_id: int,
        grade: float,
        approved: bool = False,
        approval_packet_hash: str | None = None,
        expected_packet_hash: str | None = None,
    ) -> dict[str, Any]:
        """Write exactly one submission's posted_grade. Fails closed otherwise."""
        if not feature_enabled():
            raise GradeEntryError(f"BLOCKED: grade entry disabled ({ENABLE_ENV} != {ENABLE_VALUE})")
        if not is_enabled():
            raise GradeEntryError("BLOCKED: grade entry not enabled (human enablement required)")
        if not approved:
            raise GradeEntryError("BLOCKED: missing human approval for this write")
        if not expected_packet_hash or approval_packet_hash != expected_packet_hash:
            raise GradeEntryError("BLOCKED: approval packet hash mismatch")
        if int(course_id) not in ALLOWED_COURSE_IDS:
            raise GradeEntryError(f"BLOCKED: course {course_id} is not allowlisted for grade entry")
        scope = _active_scope
        if not scope:
            raise GradeEntryError(
                "BLOCKED: no approved write scope is active (apply an approved packet)"
            )
        if (
            int(course_id) != scope["course_id"]
            or int(assignment_id) != scope["assignment_id"]
            or int(student_id) not in scope["student_ids"]
        ):
            raise GradeEntryError(
                "BLOCKED: write target is outside the approved student/assignment scope"
            )
        if approval_packet_hash != scope["packet_hash"]:
            raise GradeEntryError("BLOCKED: approval packet hash does not match the active scope")
        numeric = parse_grade(grade)
        data = {"submission[posted_grade]": format_grade(numeric)}
        path = (
            f"/api/v1/courses/{int(course_id)}/assignments/{int(assignment_id)}"
            f"/submissions/{int(student_id)}"
        )
        payload = self.request("PUT", path, data)
        return payload if isinstance(payload, dict) else {}


def assert_write_payload_is_bounded(data: dict[str, Any]) -> None:
    """Guard: payload may only carry posted_grade."""
    for key in data:
        attr = key.split("[")[-1].rstrip("]")
        if attr in FORBIDDEN_SUBMISSION_FIELDS:
            raise GradeEntryError(f"BLOCKED: write payload may not set submission[{attr}]")
        if attr not in ALLOWED_SUBMISSION_FIELDS:
            raise GradeEntryError(f"BLOCKED: unexpected write field submission[{attr}]")


# --------------------------------------------------------------------------
# Packet build + apply
# --------------------------------------------------------------------------


def _roster_index(roster: Iterable[dict[str, Any]]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[str]]]:
    """Return (name -> entries, normalized name -> colliding raw names)."""
    index: dict[str, list[dict[str, Any]]] = {}
    raw_by_key: dict[str, set[str]] = {}
    for entry in roster:
        key = normalize_name(entry.get("name") or entry.get("sortable_name") or "")
        if not key:
            continue
        index.setdefault(key, []).append(entry)
        raw_by_key.setdefault(key, set()).add(entry.get("name") or "")
    collisions = {k: sorted(v) for k, v in raw_by_key.items() if len(v) > 1}
    return index, collisions


def build_packet(
    *,
    request: dict[str, Any],
    client: CanvasGradeClient,
) -> ApprovalPacket:
    """Read Canvas state and build the named-student approval packet."""
    course_spec = request.get("course") or {}
    course_id = int(course_spec.get("course_id"))
    if course_id not in ALLOWED_COURSE_IDS:
        raise GradeEntryError(f"BLOCKED: course {course_id} is not allowlisted for grade entry")

    assignment_title = (request.get("assignment_title") or "").strip()
    if not assignment_title:
        raise GradeEntryError("BLOCKED: exact assignment title is required")

    course = client.get_course(course_id)
    assignments = client.list_assignments(course_id)
    exact = [a for a in assignments if (a.get("name") or "") == assignment_title]
    if len(exact) != 1:
        raise GradeEntryError(
            f"BLOCKED: expected exactly 1 assignment titled {assignment_title!r}, found {len(exact)}"
        )
    assignment = exact[0]
    assignment_id = int(assignment["id"])

    roster = client.list_roster(course_id)
    index, collisions = _roster_index(roster)

    submissions = {
        (int(s["student_id"]), int(s["assignment_id"])): s
        for s in client.list_submissions(course_id)
    }

    requested = request.get("grades") or []
    skip_names = [normalize_name(n) for n in (request.get("skip") or [])]

    changes: list[GradeChange] = []
    skipped: list[SkippedStudent] = []
    seen_keys: set[str] = set()

    for row in requested:
        label = (row.get("student") or "").strip()
        key = normalize_name(label)
        if not label:
            raise GradeEntryError("BLOCKED: grade row without a student name")
        if key in seen_keys:
            raise GradeEntryError(f"BLOCKED: student listed more than once: {label}")
        seen_keys.add(key)

        matches = index.get(key, [])
        if len(matches) == 0:
            raise GradeEntryError(f"BLOCKED: no roster match for {label!r}")
        if len(matches) > 1 or key in collisions:
            raise GradeEntryError(f"BLOCKED: ambiguous roster match for {label!r}")
        entry = matches[0]
        student_id = int(entry["student_id"])
        submission = submissions.get((student_id, assignment_id)) or {}
        current = submission.get("score")
        current_grade = float(current) if current not in (None, "") else None
        proposed = parse_grade(row.get("grade"))
        changes.append(
            GradeChange(
                student_label=label,
                student_id=student_id,
                student_name=entry.get("name") or label,
                current_grade=current_grade,
                proposed_grade=proposed,
            )
        )

    for name in skip_names:
        if not name:
            continue
        matches = index.get(name, [])
        if len(matches) > 1 or name in collisions:
            raise GradeEntryError(f"BLOCKED: ambiguous skipped-student match for {name!r}")
        if len(matches) == 1:
            entry = matches[0]
            submission = submissions.get((int(entry["student_id"]), assignment_id)) or {}
            current = submission.get("score")
            skipped.append(
                SkippedStudent(
                    student_label=name,
                    student_id=int(entry["student_id"]),
                    student_name=entry.get("name") or name,
                    reason="explicitly skipped; must remain unchanged",
                )
            )
        else:
            skipped.append(
                SkippedStudent(
                    student_label=name, student_id=None, student_name=name,
                    reason="explicitly skipped; not present on roster",
                )
            )

    write_count = sum(
        1 for c in changes if not grades_equal(c.current_grade, c.proposed_grade)
    )
    packet = ApprovalPacket(
        course={
            "course_id": course_id,
            "name": course.get("name"),
            "course_code": course.get("course_code"),
        },
        assignment={"assignment_id": assignment_id, "name": assignment_title},
        proposed_changes=[c.to_dict() for c in changes],
        skipped=[s.to_dict() for s in skipped],
        total_writes=write_count,
        other_assignments_touched=0,
        other_courses_touched=0,
    )
    return packet.seal()


def apply_packet(
    *,
    packet: ApprovalPacket,
    client: CanvasGradeClient,
    approved: bool = False,
    approved_by: str | None = None,
    readback_client: CanvasGradeClient | None = None,
) -> dict[str, Any]:
    """Apply an approved packet. Reads back and verifies every written grade.

    ``readback_client`` should be a pagination-capable live client whenever
    ``client`` is transport-injected (guarded/tripwire), so verification is
    never silently truncated to a single page.
    """
    if not feature_enabled():
        raise GradeEntryError(
            f"BLOCKED: grade entry disabled ({ENABLE_ENV} != {ENABLE_VALUE})"
        )
    if not is_enabled():
        raise GradeEntryError("BLOCKED: grade entry not enabled (human enablement required)")
    if not approved:
        raise GradeEntryError("BLOCKED: packet has not been explicitly approved")
    if not (approved_by or "").strip():
        raise GradeEntryError("BLOCKED: approval must name the approving teacher")
    if packet.status == "REJECTED":
        raise GradeEntryError("BLOCKED: packet was rejected")
    if packet.packet_hash != packet.compute_hash():
        raise GradeEntryError("BLOCKED: approval packet hash mismatch")
    return _apply_packet_inner(packet=packet, client=client, approved_by=approved_by,
                               readback_client=readback_client)


def _apply_packet_inner(
    *,
    packet: ApprovalPacket,
    client: CanvasGradeClient,
    approved_by: str,
    readback_client: CanvasGradeClient | None = None,
) -> dict[str, Any]:
    with approved_write_scope(packet):
        return _apply_packet_scoped(packet=packet, client=client, approved_by=approved_by,
                                    readback_client=readback_client)


def _apply_packet_scoped(
    *,
    packet: ApprovalPacket,
    client: CanvasGradeClient,
    approved_by: str,
    readback_client: CanvasGradeClient | None = None,
) -> dict[str, Any]:
    course_id = int(packet.course["course_id"])
    assignment_id = int(packet.assignment["assignment_id"])
    verifier = readback_client or client
    if course_id not in ALLOWED_COURSE_IDS:
        raise GradeEntryError(f"BLOCKED: course {course_id} is not allowlisted")

    # Re-verify live title/roster before writing (fail closed on drift).
    course = client.get_course(course_id)
    assignments = client.list_assignments(course_id)
    exact = [a for a in assignments if (a.get("name") or "") == packet.assignment["name"]]
    if len(exact) != 1 or int(exact[0]["id"]) != assignment_id:
        raise GradeEntryError("BLOCKED: assignment identity drifted since packet build")

    roster = client.list_roster(course_id)
    index, collisions = _roster_index(roster)
    submissions = {
        (int(s["student_id"]), int(s["assignment_id"])): s
        for s in client.list_submissions(course_id)
    }

    results: list[dict[str, Any]] = []
    for change in packet.proposed_changes:
        student_id = int(change["student_id"])
        proposed = parse_grade(change["proposed_grade"])
        entry = next((r for r in roster if int(r["student_id"]) == student_id), None)
        if entry is None:
            raise GradeEntryError(f"BLOCKED: student {student_id} no longer on roster")
        key = normalize_name(entry.get("name") or "")
        if len(index.get(key, [])) != 1 or key in collisions:
            raise GradeEntryError(f"BLOCKED: ambiguous roster match for student {student_id}")

        submission = submissions.get((student_id, assignment_id)) or {}
        current = submission.get("score")
        current_grade = float(current) if current not in (None, "") else None
        if grades_equal(current_grade, proposed):
            results.append(
                {
                    "student_id": student_id,
                    "student_name": change["student_name"],
                    "previous_grade": current_grade,
                    "requested_grade": proposed,
                    "action": "ALREADY_CORRECT",
                    "canvas_response": None,
                    "readback_grade": current_grade,
                    "verified": True,
                }
            )
            continue

        response = client.write_grade(
            course_id=course_id,
            assignment_id=assignment_id,
            student_id=student_id,
            grade=proposed,
            approved=True,
            approval_packet_hash=packet.packet_hash,
            expected_packet_hash=packet.packet_hash,
        )
        results.append(
            {
                "student_id": student_id,
                "student_name": change["student_name"],
                "previous_grade": current_grade,
                "requested_grade": proposed,
                "action": "WRITTEN",
                "canvas_response": {
                    k: response.get(k) for k in ("id", "score", "grade", "workflow_state", "posted_at")
                },
                "readback_grade": None,
                "verified": False,
            }
        )

    # Post-write readback of the full assignment list (via a pagination-capable client).
    readback = {
        (int(s["student_id"]), int(s["assignment_id"])): s
        for s in verifier.list_submissions(course_id)
    }
    mismatches: list[str] = []
    for record in results:
        submission = readback.get((int(record["student_id"]), assignment_id)) or {}
        score = submission.get("score")
        live = float(score) if score not in (None, "") else None
        record["readback_grade"] = live
        record["verified"] = grades_equal(live, parse_grade(record["requested_grade"]))
        if not record["verified"]:
            mismatches.append(
                f"{record['student_name']} (id {record['student_id']}): "
                f"requested {format_grade(record['requested_grade'])}, live {format_grade(live)}"
            )

    return {
        "course": packet.course,
        "course_code": course.get("course_code"),
        "assignment": packet.assignment,
        "approved_by": approved_by,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "packet_hash": packet.packet_hash,
        "results": results,
        "readback_mismatches": mismatches,
        "readback_verified": not mismatches,
        "writes_performed": sum(1 for r in results if r["action"] == "WRITTEN"),
        "already_correct": sum(1 for r in results if r["action"] == "ALREADY_CORRECT"),
        "other_assignments_touched": 0,
        "other_courses_touched": 0,
    }


def assert_untouched(
    *,
    before: dict[int, float | None],
    after: dict[int, float | None],
    expected_changed: dict[int, float],
) -> None:
    """Guard used by tests: nothing outside expected_changed may move."""
    for student_id, was in before.items():
        if student_id in expected_changed:
            continue
        now = after.get(student_id)
        if was is None and now is None:
            continue
        if was is None or now is None:
            raise GradeEntryError(f"BLOCKED: untouched student {student_id} changed")
        if not grades_equal(was, now):
            raise GradeEntryError(f"BLOCKED: untouched student {student_id} changed")
