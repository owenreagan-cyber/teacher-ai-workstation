# Current State

Live 2026-2027 school-year state only. This file changes when the live state changes; it does not hold permanent rules.

```text
Status: live-state snapshot
Last reviewed: 2026-10-11
```

## Identity

- Teacher: Owen Reagan
- Class: 4A - Reagan
- Room: 203
- School year: 2026-2027
- Live pacing tab: 4A - Reagan

## Course IDs (2026-2027 production)

| Subject | Course ID | Status |
| --- | --- | --- |
| Math | 26404 | active |
| Reading/Spelling | 26442 | active |
| Language Arts | 28171 | active |
| History | 28165 | quarter-gated (Q1, Q3) |
| Science | 28166 | quarter-gated (Q2, Q4) |
| Homeroom | 26429 | newsletter-only |

Authoritative source: `config/curriculum/canvas-course-mappings.json`. Normalized view: `config/fpk/canvas-courses.json`.

## Calendar position

- Track out: September 21 - October 9, 2026 (completed)
- School resumed: Monday, October 12, 2026 (Q2W1)
- Current quarter: Q2 — Science active, History inactive (redirect-only)

Source: `config/curriculum/canvas/instructional-weeks-2026-2027.json` and `config/curriculum/canvas/quarter-subject-activation-2026-2027.json`.

## Latest produced week

Q2W1 (October 12-16, 2026) has been produced and deployed to live Canvas:

- 5 subject Q2W1 weekly pages updated in place (Math, Reading/Spelling, Language Arts, Science, History redirect) and set as course front pages
- 12 graded assignments created and readback-verified
- 4 assessment announcements + 4 weekly-update announcements (full agenda embedded)
- Homeroom rolling newsletter updated in place to "Track 2, Week 1 · October 12-16, 2026"
- Homeroom stamp-sheet family announcement scheduled (Mon Oct 12, 8:00 AM ET)

Preceding production package: Q1W9 (September 14-18, 2026) via `scripts/canvas-llm/q1w9_build.py`.

```text
NOTE: The Q2W1 deployment facts above are from the Phase 3.5B guarded live deployment (readback-verified against live Canvas). Confirm against a fresh live read before any further production action.
```

## Unresolved live metadata

The following were `LIVE_READ_REQUIRED`; they were resolved by the Phase 2 GET-only sweep (2026-10-11) and canonicalized in `config/fpk/canvas-courses.json` (group + module IDs) and `config/fpk/live-canvas-behavior.json` (placement + capabilities):

- ✅ assignment-group IDs (numeric) — resolved for all six courses
- ✅ agenda module IDs + weekly-page module placement — resolved
- ✅ parent/observer relationship — **AVAILABLE** (structural; schema-only)
- ⚠️ Canvas Conversation attachment/image — **REQUIRES_WRITE_TEST** (not verified live)

Raw evidence: `.local/canvas-llm/phase2-live-sweep/` (untracked, GET-only).


