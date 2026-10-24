"""Weekly Planner Agent — teacher-facing conversational planning foundation.

This package is the *planning/review* layer above the existing Canvas intake,
planner, and Friday rollover infrastructure. It is read-only with respect to
Canvas: it models a canonical ``WeeklyPlan``, translates plain-language teacher
instructions into structured proposed changes, runs Assessment Date Watch, and
prepares a teacher-facing Friday review.

It NEVER writes to Canvas, never schedules, and never publishes. Live Canvas
mutation remains exclusively owned by ``scripts/canvas_llm_rollover`` behind the
existing guarded publisher. Local state is written only under
``.local/canvas-planner/agent/`` (gitignored).
"""
from __future__ import annotations

__all__ = ["models"]
