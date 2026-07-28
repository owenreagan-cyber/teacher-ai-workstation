from __future__ import annotations

from dataclasses import dataclass, field
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

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"status": self.status.value, "message": self.message}
        if self.details:
            payload["details"] = self.details
        return payload


@dataclass
class ValidationReport:
    scope: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def final_status(self) -> CheckStatus:
        if any(c.status == CheckStatus.FAIL for c in self.checks):
            return CheckStatus.FAIL
        if any(c.status == CheckStatus.WARN for c in self.checks):
            return CheckStatus.WARN
        return CheckStatus.PASS

    def add(self, status: CheckStatus, message: str, *, details: str | None = None) -> None:
        self.checks.append(CheckResult(status=status, message=message, details=details))

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope": self.scope,
            "final_status": self.final_status.value,
            "checks": [c.to_dict() for c in self.checks],
        }
