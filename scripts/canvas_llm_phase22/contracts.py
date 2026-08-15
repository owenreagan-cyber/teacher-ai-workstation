"""Phase 22 pure contracts (import-safe).

This module contains only pure data structures with no Canvas execution,
no connector, no writer, no token access, and no network/side effects.

Importing this module must never transitively import Canvas execution code.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class WeeklyAgendaPage:
    """Teacher-facing Canvas page representation (preview-safe)."""

    week_code: str
    title: str
    days: list[dict[str, Any]] = field(default_factory=list)
    assignments: list[str] = field(default_factory=list)
    assessments: list[str] = field(default_factory=list)
    reminders: list[str] = field(default_factory=list)
    schedule_summary: str | None = None
    content_hash: str | None = None
    approval_state: str = "draft"
    deployment_status: str = "draft"
    page_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
