# Friday 4 PM Canvas Weekly Rollover Contract

Status: `APPROVED_PATTERN` (implementation authorized by mission; production
execution requires a separate Owen authorization).

## Purpose

Every Friday at **4:00 PM America/New_York**, Canvas transitions from the
current instructional week to the upcoming instructional week. This is a
permanent, reusable weekly rule — never hard-coded to a specific week.

```text
Q2W2 → Q2W3   (Friday, October 23, 2026 at 4:00 PM America/New_York)
```

## Canonical rollover time

The rollover fires the Friday immediately before the upcoming week's Monday, at
4:00 PM local time. All scheduling is timezone-aware (`zoneinfo.ZoneInfo`,
`America/New_York`); the UTC offset is never hard-coded (EDT vs EST resolves via
DST).

```text
upcoming week Monday 2026-10-26  →  Friday 2026-10-23 16:00 ET  →  2026-10-23T20:00:00Z
upcoming week Monday 2026-11-09  →  Friday 2026-11-06 16:00 ET  →  2026-11-06T21:00:00Z  (EST)
```

## Lifecycle states

`NOT_DUE` · `PREPARING` · `NEEDS_OWEN` · `READY` · `HELD_UNTIL_4PM` ·
`EXECUTING` · `PUBLISHED_VERIFIED` · `BLOCKED`

`HELD_UNTIL_4PM` is "ready but before Friday 4 PM"; `PUBLISHED_VERIFIED` is
terminal. A hard blocker outranks "needs Owen", which outranks "preparing".

## Rollover order

1. **Pre-rollover validation** — readiness gate (no writes).
2. **Academic page rollover** — set each active subject's already-existing
   upcoming-week page as the course front page.
3. **Homeroom rollover** — copy the approved newsletter content forward into
   the pre-existing upcoming-week Homeroom page, then set it as the front page.
4. **Weekly communication** — create/schedule one subject-isolated weekly
   update per active course.
5. **Final verification** — readback, ledger, lifecycle transition.

## Hard rules

- **Never create a replacement weekly page.** Pages are update/set-front-page
  in place; identity keys on `page_id` (slug is mutable navigation identity).
- **Active subjects only.** For Q2, Math / Reading+Spelling / Language Arts /
  Science roll; History stays inactive and untouched.
- **Homeroom is newsletter-style**, never the academic agenda template. The
  copy-forward preserves evergreen sections (Behavior Tracker, Carpool, Family
  Quick Links, Contact Guidance, class motto), prunes only expired dates, and
  never invents content or resurrects expired events.
- **Weekly update structure (§6):**

  ```text
  Good afternoon,
  [Week in Review]
  [Next-Week Overview]
  The Canvas {subject} page has been updated...
  [FULL EXACT UPCOMING AGENDA HTML]
  Have a great weekend!
  Mr. Reagan
  ```

- **Course isolation (§9):** each narrative reads only its own subject's pacing
  cells — no cross-subject information.
- **Agenda-hash invariant (§10):** `weekly_update_agenda_hash == page_agenda_hash`
  is a deployment gate; mismatch FAILs.
- **Date format:** body/announcement dates use `Day of the week, Month day`
  (`Monday, October 26`); page titles may remain compact
  (`Q2W3 - October 26–30, 2026`).
- **Visibility:** a future `delayed_post_at` + absent from the active feed =
  `HELD_SCHEDULED` (correct); future + present = premature (FAIL).
- **Idempotence:** already-front-page → skip; exact weekly update already
  exists → skip; rollover ledger already `PUBLISHED_VERIFIED` → already
  complete unless live verification shows drift.
- **Partial failure:** a failed write records `BLOCKED` with successful
  actions, the failed action, live readback, remaining actions, and a recovery
  path. A partial rollover is never reported as complete.

## Manual fallback

```bash
bin/canvas-weekly-rollover --week q2w3 --dry-run
bin/canvas-weekly-rollover --week q2w3 --preflight
bin/canvas-weekly-rollover --week q2w3 --execute --production --confirm "ROLLOVER Q2W3"
```

Manual execution uses the same engine as scheduled execution (no second path).

## Status surfaces

```bash
bin/chief-of-staff --friday-rollover-status
bin/teacher-workstation   # Home card + GET /api/friday-rollover
```

## Module layout

```text
scripts/canvas_llm_rollover/
  schedule.py    Friday 4 PM scheduling + lifecycle
  narrative.py   subject-isolated Week-in-Review / Next-Week-Overview
  homeroom.py    newsletter copy-forward (date pruning, evergreen preserve)
  manifest.py    deterministic rollover plan builder
  ledger.py      untracked rollover ledger
  rollover.py    readiness gate, GET-only preflight, guarded execution
  status.py      Chief of Staff status
  cli.py         manual fallback command
```

Production writes require `--production` + exact owner confirmation and are
gated behind the same client/ledger primitives as `scripts/canvas_llm_deploy`.
