"""Source authority hierarchy and conflict resolution.

Enforces the controlled authority priority and the "never silently guess" rule:

    1. Owen explicit instruction (owner override)
    2. current verified pacing source
    3. current verified Canvas state
    4. established subject rules
    5. historical inference/prediction

When two sources disagree, a conflict is surfaced; the plan is never silently
rewritten and predicted items are never promoted to approved/live.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import Authority, Confidence


@dataclass
class Conflict:
    subject: str
    field: str
    current: Any
    incoming: Any
    current_authority: Authority
    incoming_authority: Authority
    resolved_to: Any | None = None
    message: str = ""
    requires_teacher_review: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "field": self.field,
            "current": self.current,
            "incoming": self.incoming,
            "current_authority": int(self.current_authority),
            "incoming_authority": int(self.incoming_authority),
            "resolved_to": self.resolved_to,
            "message": self.message,
            "requires_teacher_review": self.requires_teacher_review,
        }


def stronger(authority: Authority, other: Authority) -> bool:
    """True if ``authority`` outranks ``other`` (lower value wins)."""
    return authority < other


def resolve(
    current: Any,
    incoming: Any,
    *,
    current_authority: Authority,
    incoming_authority: Authority,
    subject: str,
    field: str,
) -> Conflict | None:
    """Compare two values for the same field; return None when they agree.

    When they differ, return a Conflict whose ``resolved_to`` is the higher-
    authority value (never a silent guess from inference). Predicted/inferred
    values can never displace a confirmed value.
    """
    if current == incoming:
        return None
    conflict = Conflict(
        subject=subject,
        field=field,
        current=current,
        incoming=incoming,
        current_authority=current_authority,
        incoming_authority=incoming_authority,
    )
    if stronger(current_authority, incoming_authority):
        conflict.resolved_to = current
        conflict.message = (
            f"{subject} {field}: kept {current!r} ({current_authority.name}) over "
            f"{incoming!r} ({incoming_authority.name})."
        )
        conflict.requires_teacher_review = False
    elif stronger(incoming_authority, current_authority):
        conflict.resolved_to = incoming
        conflict.message = (
            f"{subject} {field}: {incoming!r} ({incoming_authority.name}) outranks "
            f"{current!r} ({current_authority.name}); surfaced for review."
        )
    else:
        conflict.resolved_to = None
        conflict.message = (
            f"{subject} {field}: conflicting equal-authority values "
            f"{current!r} vs {incoming!r}; needs Owen."
        )
    return conflict


def may_promote(confidence: str, target: str) -> bool:
    """Predicted/inferred elements must never auto-promote to approved/live."""
    if confidence == Confidence.PREDICTED:
        return target not in ("approved", "live", "verified")
    return True
