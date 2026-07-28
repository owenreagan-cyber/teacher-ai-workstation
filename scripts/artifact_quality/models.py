from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Optional


class CheckStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"

    @property
    def rank(self) -> int:
        return {CheckStatus.PASS: 0, CheckStatus.WARN: 1, CheckStatus.FAIL: 2}[self]


@dataclass
class CheckResult:
    status: CheckStatus
    message: str
    details: Optional[str] = None
    page: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        payload = {"status": self.status.value, "message": self.message}
        if self.details:
            payload["details"] = self.details
        if self.page is not None:
            payload["page"] = self.page
        return payload


@dataclass
class PreflightReport:
    input_path: str
    profile_name: str
    subject: Optional[str] = None
    artifact_type: str = "pdf"
    checks: list[CheckResult] = field(default_factory=list)
    output_dir: Optional[str] = None
    render_paths: list[str] = field(default_factory=list)
    student_path: Optional[str] = None
    teacher_path: Optional[str] = None

    @property
    def final_status(self) -> CheckStatus:
        if any(check.status == CheckStatus.FAIL for check in self.checks):
            return CheckStatus.FAIL
        if any(check.status == CheckStatus.WARN for check in self.checks):
            return CheckStatus.WARN
        return CheckStatus.PASS

    def add(self, status: CheckStatus, message: str, *, details: str | None = None, page: int | None = None) -> None:
        self.checks.append(CheckResult(status=status, message=message, details=details, page=page))

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_path": self.input_path,
            "profile_name": self.profile_name,
            "subject": self.subject,
            "artifact_type": self.artifact_type,
            "final_status": self.final_status.value,
            "checks": [check.to_dict() for check in self.checks],
            "output_dir": self.output_dir,
            "render_paths": self.render_paths,
            "student_path": self.student_path,
            "teacher_path": self.teacher_path,
        }

    def exit_code(self, strict: bool = False) -> int:
        if self.final_status == CheckStatus.FAIL:
            return 1
        if strict and self.final_status == CheckStatus.WARN:
            return 2
        return 0


POINTS_PER_INCH = 72.0
LETTER_WIDTH_PT = 612.0
LETTER_HEIGHT_PT = 792.0
A4_WIDTH_PT = 595.0
A4_HEIGHT_PT = 842.0

PLACEHOLDER_PATTERNS = (
    "[SOURCE INFORMATION NEEDED]",
    "TODO",
    "TBD",
    "PLACEHOLDER",
    "{{",
    "}}",
    "[INSERT",
    "XXX",
)
