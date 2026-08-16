# Weekly Canvas Workflow Guardrails

Final integration/cleanup round. These guardrails make explicit the preconditions
the existing Phases 18A–18E and 22–27 weekly workflow must satisfy. They add no
orchestration engine, publisher, state machine, dashboard, or persistence
subsystem.

## Fresh pacing pull (hard rule)

Every weekly session starts with a fresh live read of the 2026-2027 FPK pacing
guide, tab `4B - Reagan`:

- Spreadsheet ID: `1I-CNb_ZPnOozY2wSMNAWF3bzuRZWDdZt9yoSBKtLWD4`
- Sheet: `4B - Reagan`

Remembered/cached pacing (earlier chats, cached plans, prior deployments,
fixtures, project memory) provides context only — it never satisfies freshness.
A failed live read blocks the build; there is no silent fallback to memory.

`pacing_session.py` models the session-scoped snapshot and its blockers:

- `new_session_snapshot()` — no fresh pull recorded (build blocked).
- `record_fresh_pull(...)` — records a successful live read.
- `invalidate(...)` — a refresh/verify/re-read command forces a new pull.
- `mark_read_failure(...)` — a failed read blocks the build.
- `can_build(...)` / `build_blockers(...)` — the deterministic gate.

The snapshot also requires the immediately previous school week so the weekly
course announcement reflection uses real prior-week pacing.

## Newsletter / Homeroom guardrails

`newsletter_guard.py`:

- Live Homeroom read required before any edit (never an old local copy).
- `prune_expired_dates(...)` removes only clearly-expired dates, preserves all
  future dates, and surfaces ambiguous dates instead of guessing.
- The mandatory teacher question ("anything to add to the newsletter?") must be
  asked before the newsletter can move to final Canvas review.

## Explicit launch

`launch_gate.py`: approval of pacing, artifact generation, and the final review
are pre-launch steps. A distinct, explicit launch command (`Launch`,
`Publish it`, `Apply Q1W5`, `Go live`, ...) is required. No inferred approval.

## Proof surface

- `python3 scripts/canvas_llm_weekly_guardrails/cli.py --selfcheck`
- `bash scripts/canvas-llm-weekly-guardrails-status.sh`
- `bash tests/canvas-llm-weekly-guardrails-test.sh`
