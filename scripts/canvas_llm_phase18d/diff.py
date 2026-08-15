"""Deterministic semantic safety-diff (Phase 18D).

Compares current live Canvas state against desired canonical state and emits a
machine-readable field-level diff. Uses semantic normalization (via Phase 27
``canonicalize``) so benign formatting/whitespace differences do not produce
meaningless UPDATE noise, while meaningful instructional differences are never
normalized away.
"""

from __future__ import annotations

from typing import Any

from scripts.canvas_llm_phase27.canonicalize import canonical_hash, canonicalize_content

from .contracts import (
    ChangeKind,
    DiffClassification,
    FieldDiff,
    RiskTier,
    SafetyDiffItem,
)


def _canon(value: Any) -> str:
    return canonicalize_content(value if value is not None else "")


def compare_field(field: str, current: Any, desired: Any) -> FieldDiff:
    """Compare a single field semantically (whitespace/formatting insensitive)."""
    if _canon(current) == _canon(desired):
        return FieldDiff(field=field, current=current, desired=desired, change=ChangeKind.NO_CHANGE.value)
    if current is None or current == "":
        change = ChangeKind.ADD.value
    elif desired is None or desired == "":
        change = ChangeKind.REMOVE.value
    else:
        change = ChangeKind.UPDATE.value
    return FieldDiff(field=field, current=current, desired=desired, change=change)


def compare_state(current: dict[str, Any], desired: dict[str, Any], fields: list[str]) -> list[FieldDiff]:
    """Produce ordered field diffs over the given field list."""
    diffs: list[FieldDiff] = []
    for field in fields:
        diffs.append(compare_field(field, current.get(field), desired.get(field)))
    return diffs


def has_meaningful_change(diffs: list[FieldDiff]) -> bool:
    return any(d.change != ChangeKind.NO_CHANGE.value for d in diffs)


def semantic_hash(state: dict[str, Any], fields: list[str]) -> str:
    """Deterministic hash of the *semantic* content of the given fields."""
    return canonical_hash({f: state.get(f) for f in fields})


def classify(operation: str, blockers: list[str], *, had_remote_drift: bool = False) -> tuple[str, str]:
    """Map an intent's operation + blockers to a (classification, risk) pair."""
    if blockers:
        return DiffClassification.BLOCKED.value, RiskTier.HIGH.value
    if operation == "CREATE":
        return DiffClassification.SAFE_CREATE.value, RiskTier.LOW.value
    if operation == "UPDATE":
        if had_remote_drift:
            return DiffClassification.REVIEW_REQUIRED.value, RiskTier.HIGH.value
        return DiffClassification.SAFE_UPDATE.value, RiskTier.MEDIUM.value
    if operation == "NO_CHANGE":
        return DiffClassification.NO_CHANGE.value, RiskTier.LOW.value
    if operation == "SKIP":
        return DiffClassification.SKIP.value, RiskTier.LOW.value
    return DiffClassification.REVIEW_REQUIRED.value, RiskTier.MEDIUM.value


def build_safety_diff_item(
    intent_id: str,
    object_type: str,
    course: str,
    locator: str,
    operation: str,
    source: str,
    field_diffs: list[FieldDiff],
    blockers: list[str],
    *,
    had_remote_drift: bool = False,
) -> SafetyDiffItem:
    classification, risk = classify(operation, blockers, had_remote_drift=had_remote_drift)
    return SafetyDiffItem(
        intent_id=intent_id,
        object_type=object_type,
        course=course,
        locator=locator,
        operation=operation,
        classification=classification,
        risk=risk,
        source=source,
        blockers=list(blockers),
        field_diffs=field_diffs,
    )
