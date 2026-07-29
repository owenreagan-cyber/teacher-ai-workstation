from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class WorkflowState(str, Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    ARCHIVED = "archived"


ALLOWED_TRANSITIONS: dict[WorkflowState, set[WorkflowState]] = {
    WorkflowState.DRAFT: {WorkflowState.IN_REVIEW, WorkflowState.ARCHIVED},
    WorkflowState.IN_REVIEW: {WorkflowState.DRAFT, WorkflowState.APPROVED, WorkflowState.ARCHIVED},
    WorkflowState.APPROVED: {WorkflowState.ARCHIVED},
    WorkflowState.ARCHIVED: set(),
}


@dataclass
class ApprovalRecord:
    timestamp: str
    user: str
    note: str
    from_state: WorkflowState
    to_state: WorkflowState

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["from_state"] = self.from_state.value
        payload["to_state"] = self.to_state.value
        return payload

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ApprovalRecord:
        return cls(
            timestamp=str(raw["timestamp"]),
            user=str(raw["user"]),
            note=str(raw.get("note") or ""),
            from_state=WorkflowState(str(raw["from_state"])),
            to_state=WorkflowState(str(raw["to_state"])),
        )


@dataclass
class ApprovalWorkflow:
    state: WorkflowState = WorkflowState.DRAFT
    history: list[ApprovalRecord] = field(default_factory=list)

    def transition(
        self,
        to_state: WorkflowState,
        *,
        user: str,
        note: str = "",
        override: bool = False,
    ) -> ApprovalRecord:
        if self.state == WorkflowState.APPROVED and to_state == WorkflowState.DRAFT and not override:
            raise ValueError("Approved lesson cannot return to Draft without explicit override")
        if to_state not in ALLOWED_TRANSITIONS.get(self.state, set()) and not override:
            raise ValueError(f"Transition {self.state.value} → {to_state.value} is not allowed")
        record = ApprovalRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            user=user,
            note=note,
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

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ApprovalWorkflow:
        workflow = cls(state=WorkflowState(str(raw.get("state", WorkflowState.DRAFT.value))))
        workflow.history = [ApprovalRecord.from_dict(item) for item in raw.get("history") or []]
        return workflow
