"""Phase 24 pure contracts (import-safe).

This module re-exports the pure dataclasses from ``models`` so consumers can
import the prediction contract without transitively loading prediction logic or
Canvas execution infrastructure.

Importing this module must never import ``rule_engine`` (which depends on
``phase22_workstation`` and its network-capable imports), ``canvas_connector``,
``canvas_writer``, or any token/network code.
"""

from __future__ import annotations

from .models import (
    Confidence,
    PredictedAssessment,
    PredictedHomework,
    PredictedInstructionalEvent,
    PredictedLesson,
    PredictedResourceRequirement,
    RuleExplanation,
    SourceEvidence,
    TeacherCorrection,
    TeacherOverride,
    UnresolvedDecision,
    WeekPrediction,
)

__all__ = [
    "Confidence",
    "PredictedAssessment",
    "PredictedHomework",
    "PredictedInstructionalEvent",
    "PredictedLesson",
    "PredictedResourceRequirement",
    "RuleExplanation",
    "SourceEvidence",
    "TeacherCorrection",
    "TeacherOverride",
    "UnresolvedDecision",
    "WeekPrediction",
]
