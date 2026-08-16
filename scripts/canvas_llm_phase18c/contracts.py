"""Phase 18C read-only Teacher Preview contracts (import-safe).

These are pure data structures only. Importing this module must never import
Canvas execution code, writers, connectors, or token/network modules.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ReadinessState(str, Enum):
    """Overall preview readiness (never implies publish readiness)."""

    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    ADVISORY_ONLY = "ADVISORY_ONLY"
    BLOCKED_UNRESOLVED = "BLOCKED_UNRESOLVED"
    BLOCKED_PROTECTED = "BLOCKED_PROTECTED"
    BLOCKED_MISSING_CONFIG = "BLOCKED_MISSING_CONFIG"
    BLOCKED_POLICY = "BLOCKED_POLICY"


class Derivation(str, Enum):
    """Why a downstream field has the value it does."""

    CANONICAL = "canonical"
    DERIVED = "derived"
    CONFIGURED = "configured"
    PREDICTED = "predicted"
    UNRESOLVED = "unresolved"
    BLANK = "blank"
    PROTECTED = "protected"


@dataclass
class RuntimeContext:
    """Read-only runtime state for preview assembly.

    ``canvas_config`` carries resolved live/registry Canvas identifiers keyed by
    downstream subject key. Missing required IDs must block preview assembly with
    ``BLOCKED_MISSING_CONFIG`` (never guess). ``legacy_fixtures`` is a
    test/compatibility path only and must never override canonical data.
    """

    canvas_config: dict[str, Any] = field(default_factory=dict)
    due_time_policy: str = "resolved"  # owner-approved: same-day 11:59 p.m. local
    due_time_reason: str = ""  # empty: due-time is owner-resolved, no unresolved reason
    legacy_fixtures: dict[str, Any] = field(default_factory=dict)


@dataclass
class PreviewDay:
    weekday: str
    date: str
    in_class: str
    homework: str
    raw: str
    source: str
    derivation: str
    evidence: list[dict[str, Any]]
    status: str  # "content" | "blank" | "unresolved" | "protected"
    protected: bool


@dataclass
class PreviewCourse:
    course: str
    subject_key: str
    protected: bool
    days: list[PreviewDay]
    requested_artifacts: list[str]
    readiness: str
    assignment_policy: str


@dataclass
class DriftFinding:
    kind: str  # "exact_match" | "expected_derivation" | "unresolved_difference" | "invalid_drift"
    target: str
    detail: str


@dataclass
class DriftReport:
    exact_matches: int = 0
    expected_derivations: int = 0
    unresolved_differences: int = 0
    invalid_drift: list[str] = field(default_factory=list)
    findings: list[DriftFinding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.invalid_drift


@dataclass
class TeacherPreview:
    """Deterministic, read-only, human-review representation of the pipeline."""

    week_code: str
    monday_date: str
    friday_date: str
    timezone: str
    week_title: str
    courses: list[PreviewCourse]
    days: list[dict[str, Any]]
    agenda: dict[str, Any]
    prediction: dict[str, Any]
    workstation: dict[str, Any]
    unresolved: list[dict[str, Any]]
    protected: list[str]
    missing_config: list[str]
    unresolved_policy: list[str]
    warnings: list[str]
    blocked_reasons: list[str]
    readiness: str
    provenance: list[dict[str, Any]]
    drift: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
