from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class BlueprintApprovalState(str, Enum):
    DRAFT = "draft"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    LOCKED = "locked"


ALLOWED_BLUEPRINT_TRANSITIONS: dict[BlueprintApprovalState, set[BlueprintApprovalState]] = {
    BlueprintApprovalState.DRAFT: {BlueprintApprovalState.NEEDS_REVIEW},
    BlueprintApprovalState.NEEDS_REVIEW: {BlueprintApprovalState.DRAFT, BlueprintApprovalState.APPROVED},
    BlueprintApprovalState.APPROVED: {BlueprintApprovalState.LOCKED, BlueprintApprovalState.NEEDS_REVIEW},
    BlueprintApprovalState.LOCKED: set(),
}


@dataclass
class BlueprintApprovalRecord:
    timestamp: str
    user: str
    reason: str
    notes: str
    from_state: BlueprintApprovalState
    to_state: BlueprintApprovalState

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["from_state"] = self.from_state.value
        payload["to_state"] = self.to_state.value
        return payload


@dataclass
class BlueprintApprovalWorkflow:
    state: BlueprintApprovalState = BlueprintApprovalState.DRAFT
    history: list[BlueprintApprovalRecord] = field(default_factory=list)

    @property
    def is_locked(self) -> bool:
        return self.state == BlueprintApprovalState.LOCKED

    def transition(
        self,
        to_state: BlueprintApprovalState,
        *,
        user: str,
        reason: str = "",
        notes: str = "",
        override: bool = False,
    ) -> BlueprintApprovalRecord:
        if self.state == BlueprintApprovalState.LOCKED and not override:
            raise ValueError("Locked blueprint cannot change without explicit override")
        if to_state not in ALLOWED_BLUEPRINT_TRANSITIONS.get(self.state, set()) and not override:
            raise ValueError(f"Transition {self.state.value} → {to_state.value} is not allowed")
        record = BlueprintApprovalRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            user=user,
            reason=reason,
            notes=notes,
            from_state=self.state,
            to_state=to_state,
        )
        self.state = to_state
        self.history.append(record)
        return record

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "history": [item.to_dict() for item in self.history],
        }
