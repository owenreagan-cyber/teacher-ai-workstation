"""Precedent classification for the August 15 Canvas scout findings.

Precedent is SUPPORTING EVIDENCE only; it is never a source of truth that can
override current teacher instruction or current pacing. Scout findings are
split into three mutually exclusive categories:

- ``operational_behavior``   (A) canonical operational behavior
- ``canvas_configuration``   (B) current Canvas configuration (registry, live-verified)
- ``anomaly``                (C) known anomalies / historical inconsistencies

Only operational behavior may be promoted into generation rules. Configuration
belongs in the registry and remains live-verifiable, never hardcoded as an
eternal rule. Anomalies must never be promoted automatically.
"""

from __future__ import annotations

PRECEDENT_CLASSES: dict[str, str] = {
    "operational_behavior": "A. canonical operational behavior",
    "canvas_configuration": "B. current Canvas configuration",
    "anomaly": "C. known anomaly / historical inconsistency",
}

# Classes that may feed generation rules. Configuration is routed to the
# registry; anomalies are never promotable.
PROMOTABLE_PRECEDENT_CLASSES: frozenset[str] = frozenset({"operational_behavior"})

# Documented August 15 scout findings, classified. This is a static catalog for
# documentation and status proof only; the production planner must not reread
# the whole evidence bundle on every run.
PRECEDENT_CATALOG: list[dict[str, str]] = [
    {"classification": "operational_behavior", "description": "Seeded weekly pages are reused/updated in place"},
    {"classification": "operational_behavior", "description": "No-homework days omit At Home entirely"},
    {"classification": "operational_behavior", "description": "Spelling may display/announce in Reading while the gradebook assignment routes to Language Arts"},
    {"classification": "operational_behavior", "description": "Homeroom newsletter front page updated in place"},
    {"classification": "canvas_configuration", "description": "Course IDs"},
    {"classification": "canvas_configuration", "description": "Assignment-group IDs (resolve/verify live; never hardcode as eternal truth)"},
    {"classification": "anomaly", "description": "RM4 Lesson 13 with Lesson 12 description"},
    {"classification": "anomaly", "description": "History review assignments using test descriptions"},
    {"classification": "anomaly", "description": "Trailing-space title"},
    {"classification": "anomaly", "description": "Naming transitions"},
]


def is_valid_precedent_class(classification: str) -> bool:
    return classification in PRECEDENT_CLASSES


def is_anomaly(classification: str) -> bool:
    return classification == "anomaly"


def is_promotable(classification: str) -> bool:
    return classification in PROMOTABLE_PRECEDENT_CLASSES
