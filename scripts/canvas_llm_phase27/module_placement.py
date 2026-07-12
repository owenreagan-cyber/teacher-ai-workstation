from __future__ import annotations

from dataclasses import dataclass
from typing import Any

PLACEMENT_STATUSES = {
    "already-correct",
    "needs-placement",
    "needs-reorder",
    "missing-module",
    "ambiguous-module",
    "blocked",
    "omitted",
}


class ModulePlacementError(ValueError):
    pass


@dataclass
class ModulePlacementResult:
    status: str
    targetModuleRef: str | None
    targetModuleId: str | None
    currentModule: str | None
    currentPosition: int | None
    desiredModule: str | None
    desiredPosition: int | None
    conflictReason: str | None

    def __post_init__(self) -> None:
        if self.status not in PLACEMENT_STATUSES:
            raise ModulePlacementError(f"invalid module placement status: {self.status!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "targetModuleRef": self.targetModuleRef,
            "targetModuleId": self.targetModuleId,
            "currentModule": self.currentModule,
            "currentPosition": self.currentPosition,
            "desiredModule": self.desiredModule,
            "desiredPosition": self.desiredPosition,
            "conflictReason": self.conflictReason,
        }


def classify_module_placement(
    local: dict[str, Any],
    remote: dict[str, Any],
    known_modules: list[dict[str, Any]],
    comparison_status: str,
) -> ModulePlacementResult:
    """known_modules: modules that actually exist in the target course, each
    {"moduleId": str, "name": str}. Never creates a module or module item --
    this only classifies whether the desired placement can be reached."""
    desired_module = local.get("moduleRef")
    desired_position = local.get("modulePosition")
    current_module = remote.get("moduleRef") if remote else None
    current_position = remote.get("modulePosition") if remote else None

    if comparison_status in {"BLOCKED", "CONFLICT"}:
        return ModulePlacementResult(
            "blocked", desired_module, None, current_module, current_position,
            desired_module, desired_position, f"placement blocked by {comparison_status}",
        )
    if comparison_status == "OMIT":
        return ModulePlacementResult(
            "omitted", desired_module, None, current_module, current_position,
            desired_module, desired_position, None,
        )

    if not desired_module:
        return ModulePlacementResult(
            "already-correct", None, None, current_module, current_position, None, None, None
        )

    matches = [m for m in known_modules if m["name"] == desired_module]
    if not matches:
        return ModulePlacementResult(
            "missing-module", desired_module, None, current_module, current_position,
            desired_module, desired_position,
            f"module {desired_module!r} does not exist in the target course",
        )
    if len(matches) > 1:
        return ModulePlacementResult(
            "ambiguous-module", desired_module, None, current_module, current_position,
            desired_module, desired_position,
            f"module name {desired_module!r} matches {len(matches)} modules",
        )

    target_module_id = matches[0]["moduleId"]

    if not remote:
        return ModulePlacementResult(
            "needs-placement", desired_module, target_module_id, None, None,
            desired_module, desired_position, None,
        )
    if current_module == desired_module and current_position == desired_position:
        return ModulePlacementResult(
            "already-correct", desired_module, target_module_id, current_module,
            current_position, desired_module, desired_position, None,
        )
    if current_module == desired_module:
        return ModulePlacementResult(
            "needs-reorder", desired_module, target_module_id, current_module,
            current_position, desired_module, desired_position, None,
        )
    return ModulePlacementResult(
        "needs-placement", desired_module, target_module_id, current_module,
        current_position, desired_module, desired_position, None,
    )
