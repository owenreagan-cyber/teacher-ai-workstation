from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

ROLLBACK_TYPES = {"restore-prior-state", "archive-candidate", "unpublish-candidate", "delete-candidate", "restore-prior-placement"}
RISK_LEVELS = {"low", "medium", "high"}


class RollbackPlanError(ValueError):
    pass


@dataclass
class RollbackInstruction:
    operationId: str
    rollbackType: str
    priorState: dict[str, Any]
    requiredApprovals: list[str]
    risk: str
    executable: bool = False

    def __post_init__(self) -> None:
        if self.rollbackType not in ROLLBACK_TYPES:
            raise RollbackPlanError(f"invalid rollbackType: {self.rollbackType!r}")
        if self.risk not in RISK_LEVELS:
            raise RollbackPlanError(f"invalid risk level: {self.risk!r}")
        if self.executable is not False:
            raise RollbackPlanError("Phase 27 rollback instructions must never be executable")

    def to_dict(self) -> dict[str, Any]:
        return {
            "operationId": self.operationId,
            "rollbackType": self.rollbackType,
            "priorState": self.priorState,
            "requiredApprovals": self.requiredApprovals,
            "risk": self.risk,
            "executable": self.executable,
        }


def build_rollback_plan(diffs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Non-executable rollback instructions. For updates, preserves the
    remote ("before") state so a reviewed revert has something concrete to
    restore to. For creates, only ever recommends archive/unpublish/delete
    candidacy -- never an automatic delete."""
    instructions: list[RollbackInstruction] = []

    for d in diffs:
        status = d["comparisonStatus"]
        object_id = d["objectId"]
        placement = d.get("modulePlacement", {})

        if status == "UPDATE":
            instructions.append(
                RollbackInstruction(
                    operationId=object_id,
                    rollbackType="restore-prior-state",
                    priorState={
                        "contentHash": d["contentHashBefore"],
                        "metadataHash": d["metadataHashBefore"],
                        "placementHash": d["placementHashBefore"],
                    },
                    requiredApprovals=[object_id],
                    risk="medium" if any(
                        fd["changeKind"] == "material content change" for fd in d.get("fieldDiffs", [])
                    ) else "low",
                )
            )
            if placement.get("status") == "needs-reorder":
                instructions.append(
                    RollbackInstruction(
                        operationId=object_id,
                        rollbackType="restore-prior-placement",
                        priorState={
                            "module": placement.get("currentModule"),
                            "position": placement.get("currentPosition"),
                        },
                        requiredApprovals=[object_id],
                        risk="low",
                    )
                )
        elif status == "CREATE":
            instructions.append(
                RollbackInstruction(
                    operationId=object_id,
                    rollbackType="archive-candidate",
                    priorState={"existedBefore": False},
                    requiredApprovals=[object_id],
                    risk="low",
                )
            )
        elif status == "DELETE_CANDIDATE":
            instructions.append(
                RollbackInstruction(
                    operationId=object_id,
                    rollbackType="delete-candidate",
                    priorState={
                        "contentHash": d["contentHashBefore"],
                        "metadataHash": d["metadataHashBefore"],
                    },
                    requiredApprovals=[object_id, "manual-review"],
                    risk="high",
                )
            )

    return [instr.to_dict() for instr in instructions]
