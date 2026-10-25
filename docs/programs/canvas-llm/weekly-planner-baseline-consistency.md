# Weekly Planner Agent — Baseline Cross-Source Consistency

```text
Status: active (implementation)
Phase: weekly-planner-baseline-consistency
Branch: feature/weekly-planner-baseline-consistency
Runtime activation: read-only GET only (Canvas + Google pacing)
Non-destructive: no Canvas writes, no Google writes, no real email, no scheduler
```

## What this phase closes

The agent previously detected **temporal** changes ("yesterday Thursday, today
Friday"). This phase adds the **baseline** consistency gate:

> "Google pacing currently says Thursday, but Canvas currently says Friday."

It works on first run, a newly created week, after snapshot loss, and after a
long outage — no prior history required. It does not infer which source changed
first and never silently resolves the disagreement.

## Two detection systems (both preserved)

| System | Comparison | Event |
| --- | --- | --- |
| Temporal change detection | previous ↔ current | `assessment_date_changed`, etc. |
| Baseline cross-source consistency | current pacing ↔ current Canvas | `cross_source_conflict` |

A first observation produces **no** temporal events, but **does** run the
cross-source scan (the central acceptance requirement of this phase).

## Cross-source engine

`scripts/weekly_planner_agent/cross_source.py` compares the normalized pacing
cells (from `live_sources`) directly against the normalized Canvas observation
(from `canvas_observation`). Deterministic checks only:

- **Assessment date** — Canvas assignment due day (America/New_York local day;
  `03:59Z` = 11:59 PM ET the prior evening) vs the authoritative date.
- **Assessment identity** — same kind, different number due in the active week.
- **Assessment assignment missing** — enabled subjects only (math, reading/spelling,
  language arts; science/history are manual-only and never flagged).
- **Pacing vs owner override** — an explicit owner instruction outranks pacing.
- **Front page** — the current-week page is not the active front page (Homeroom
  excluded; it is a monthly newsletter carried forward by the rollover).
- **First announcement / day-before reminder** — presence + scheduled date +
  posted state + duplicate, scoped to the current assessment window (historical
  reminders are ignored, never flagged).

Ambiguous matches are skipped (UNKNOWN), never guessed. A source outage
(UNKNOWN/STALE/UNAVAILABLE) produces **no** fabricated conflict.

## Authority hierarchy (unchanged)

1. Owen explicit instruction → 2. verified pacing → 3. verified Canvas →
4. subject rules → 5. inference. A lower-authority source disagreeing is still
surfaced: "Canvas disagrees with your current plan", never "Canvas wins".

## Q2W3 Math owner override

`scripts/weekly_planner_agent/owner_instructions.py` records Owen's explicit
decision as **auditable data** (not generic logic), applied through the existing
`teacher_override` / `OWNER_INSTRUCTION` mechanism:

- **Thursday 2026-10-29** — Written Assessment 7 + Fact Assessment 7
- **Friday 2026-10-30** — Investigation 4

Reason: assessments intentionally moved to Thursday because Friday is the
classroom's Halloween-ish day. The override survives local-state rebuild and
outranks a later-disagreeing pacing or Canvas.

## Notifications + scheduler

`mode = preview`, `email_enabled = false`. Cross-source conflicts may draft
notifications but never send. The Friday LaunchAgent is not installed or loaded.

## Status

```bash
bin/chief-of-staff --weekly-planner-agent-status
```

Reports baseline consistency scan status, unresolved cross-source conflicts,
assessment conflicts, override-backed conflicts, source freshness, Friday review
blocked state, and scheduler state.

- **PASS** — sources agree or all material conflicts explicitly resolved
- **WARN** — non-blocking conflict or an active owner override with a
  lower-authority disagreement
- **FAIL** — material unresolved conflict that makes approval unsafe
