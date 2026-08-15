"""Source precedence for canonical WeeklyPlan material decisions.

Ordering (highest authority first):

1. Current teacher instruction
2. Current live 2026-2027 FPK pacing guide, tab "4B - Reagan"
3. Canonical operational/subject rules
4. Current verified Canvas configuration/registry
5. Approved Canvas precedent
6. Historical examples/chats

Lower rank = higher authority. A value decided by a lower-precedence source
must never override a value supplied by a higher-precedence source. Precedent
must never override current teacher instruction or current pacing.
"""

from __future__ import annotations

SOURCE_PRECEDENCE: list[str] = [
    "teacher_instruction",
    "live_pacing",
    "canonical_rule",
    "live_canvas_config",
    "precedent",
    "historical_fallback",
]

SOURCE_LABELS: dict[str, str] = {
    "teacher_instruction": "Current teacher instruction",
    "live_pacing": 'Current live 2026-2027 FPK pacing guide, tab "4B - Reagan"',
    "canonical_rule": "Canonical operational/subject rule",
    "live_canvas_config": "Current verified Canvas configuration/registry",
    "precedent": "Approved Canvas precedent",
    "historical_fallback": "Historical examples/chats",
}

VALID_SOURCE_CLASSES: frozenset[str] = frozenset(SOURCE_PRECEDENCE)


def precedence_rank(source_class: str) -> int:
    """Return the authority rank of a source class (0 = highest authority)."""
    if source_class not in VALID_SOURCE_CLASSES:
        raise ValueError(f"unknown source class: {source_class!r}")
    return SOURCE_PRECEDENCE.index(source_class)


def is_higher_precedence(a: str, b: str) -> bool:
    """Return True if source class ``a`` outranks source class ``b``."""
    return precedence_rank(a) < precedence_rank(b)


def highest_precedence(source_classes: list[str]) -> str | None:
    """Return the highest-authority source class among ``source_classes``."""
    if not source_classes:
        return None
    return min(source_classes, key=precedence_rank)
