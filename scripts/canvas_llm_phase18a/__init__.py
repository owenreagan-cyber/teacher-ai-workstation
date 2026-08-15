"""Canonical WeeklyPlan + evidence model (Phase 18A).

Read-only modeling only. This package builds, validates, serializes, and
inspects a canonical WeeklyPlan in memory. It performs no Canvas writes, makes
no network calls, and never reads or emits Canvas tokens or secrets.

The WeeklyPlan is the sole normalized input for future preview and publishing
phases. It records instructional/publishing intent and its evidence provenance;
it does not embed permanent live Canvas configuration (for example, numeric
assignment-group IDs are referenced separately during preflight, never stored
as eternal truth here).

Import submodules directly, e.g.:

    from scripts.canvas_llm_phase18a.models import WeeklyPlan
    from scripts.canvas_llm_phase18a.validation import validate_plan
"""
