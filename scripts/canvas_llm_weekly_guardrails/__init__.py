"""Weekly Canvas workflow guardrails (final integration/cleanup round).

Small, pure, import-safe modules that codify the hard guardrails for the weekly
workflow. They do not introduce a new orchestration engine, publisher, state
machine, or dashboard; they only make explicit the preconditions the existing
Phases 18A-18E and 22-27 workflow must satisfy.

- ``pacing_session``: a fresh live read of the 2026-2027 FPK pacing guide
  (tab ``4B - Reagan``) is required at the start of every weekly session.
- ``newsletter_guard``: live Homeroom read before edits, expired-date cleanup,
  and the mandatory teacher question before final review.
- ``launch_gate``: a distinct, explicit launch command is required; approval
  and final review never imply launch.

No network. No Canvas writes. No token use. No new persistence subsystem.
"""

from __future__ import annotations

from .launch_gate import (
    BLOCK_LAUNCH_REQUIRED,
    LAUNCH_COMMANDS,
    LaunchState,
    approval_is_not_launch,
    is_launch_command,
    is_launched,
    launch_blockers,
    normalize_command,
)
from .newsletter_guard import (
    BLOCK_LIVE_READ_REQUIRED,
    BLOCK_QUESTION_REQUIRED,
    NewsletterGuardState,
    can_finalize_newsletter,
    newsletter_blockers,
    prune_expired_dates,
)
from .pacing_session import (
    BLOCK_FRESH_PULL_REQUIRED,
    BLOCK_MISSING_WEEK_DATES,
    BLOCK_PREVIOUS_WEEK_MISSING,
    BLOCK_READ_FAILURE,
    BLOCK_WRONG_SOURCE,
    FPK_SHEET_NAME,
    FPK_SPREADSHEET_ID,
    PacingSessionSnapshot,
    build_blockers,
    can_build,
    covers_previous_week,
    invalidate,
    is_fresh,
    mark_read_failure,
    new_session_snapshot,
    record_fresh_pull,
    weekdays_for_week,
)

__all__ = [
    "BLOCK_FRESH_PULL_REQUIRED",
    "BLOCK_LAUNCH_REQUIRED",
    "BLOCK_LIVE_READ_REQUIRED",
    "BLOCK_MISSING_WEEK_DATES",
    "BLOCK_PREVIOUS_WEEK_MISSING",
    "BLOCK_QUESTION_REQUIRED",
    "BLOCK_READ_FAILURE",
    "BLOCK_WRONG_SOURCE",
    "FPK_SHEET_NAME",
    "FPK_SPREADSHEET_ID",
    "LAUNCH_COMMANDS",
    "LaunchState",
    "NewsletterGuardState",
    "PacingSessionSnapshot",
    "approval_is_not_launch",
    "build_blockers",
    "can_build",
    "can_finalize_newsletter",
    "covers_previous_week",
    "invalidate",
    "is_fresh",
    "is_launch_command",
    "is_launched",
    "launch_blockers",
    "mark_read_failure",
    "new_session_snapshot",
    "newsletter_blockers",
    "normalize_command",
    "prune_expired_dates",
    "record_fresh_pull",
    "weekdays_for_week",
]
