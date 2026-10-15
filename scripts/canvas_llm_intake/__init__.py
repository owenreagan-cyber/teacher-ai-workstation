"""Canvas Weekly Intake + Staging Workspace.

Local-first orchestration that reuses the Phase 3 pacing engine
(``scripts.canvas_llm_phase3``) to turn the connected pacing spreadsheet into a
teacher-reviewable staging packet under ``.local/canvas-llm/intake/``.

Lifecycle:
    SOURCE_FETCHED -> NORMALIZED -> DRAFTED -> NEEDS_INPUT
    -> READY_FOR_REVIEW -> TEACHER_APPROVED -> READY_TO_PUBLISH
    -> PUBLISHED_VERIFIED

This package NEVER writes to Canvas. It issues GET-only reads (page lookup,
assignment duplicate checks) and otherwise only writes local staging artifacts.
"""
from __future__ import annotations

__all__ = ["constants"]
