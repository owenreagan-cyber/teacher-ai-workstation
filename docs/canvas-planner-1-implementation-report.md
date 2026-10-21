# Canvas Planner 1 — Part B implementation report

Date: 2026-10-21

Branch: `feature/canvas-planner-1`

Scope: approved Part B only; no push, merge, LaunchAgent installation, or live Canvas write

## Outcome

Canvas weekly planning now has one canonical local service/projection over the
authoritative JSON intake and deployment packets. The Teacher Workstation and
`bin/canvas-weekly-status` consume that projection. The Friday rollover is the
only weekly-package publisher; the legacy direct deploy UI and CLI paths are
blocked.

The configured runtime root is `TAW_STATE_ROOT`, defaulting to
`/Users/owen/Projects/teacher-ai-workstation/.local`. Tests used temporary
fixtures. Week and Friday calculations use `ZoneInfo("America/New_York")`,
including the November 1, 2026 DST boundary.

No work from `wip/canvas-live-q1w9` was merged or cherry-picked. Grade entry and
the grade-check job were not changed. The new Friday LaunchAgent is committed
but was not copied, loaded, bootstrapped, or otherwise installed.

## Commits

| Step | Commit | Result |
| --- | --- | --- |
| Authority and state root | `76d7a8b` | D-018 amendment, D-027/D-028, JSON authority, legacy SQLite labels, state root, DST fix |
| Status and deep links | `fdb16d1` | versioned local status contract, CLI, route opening |
| Review-first source sync | `ed46b5c` | delta proposal, explicit apply/keep, preserved owner overrides |
| Plan, AI, approvals | `0c0e134` | edit history/undo, structured evidence review, exact course bundles and diffs |
| Five-stage UI | `da72bb3` | redesigned Planner and exact previews |
| Friday publisher | `11ad17b` | all-or-nothing/partial rollover, full package readback, one uninstalled Friday plist |
| Source and review automation | `9274dca` | sheet preview/save, opportunistic daily check, debounced AI unavailable fallback |

Part A findings are in `ef960c8`.

## Screen descriptions

1. **Week:** Q2W3/date header, previous/next controls, one computed Next action,
   plain-language readiness banner, five-course stage grid, source and AI cards.
   Visually inspected in Chrome against the installed Q2W3 packet.
2. **Source:** connection metadata, Resync, Change sheet, Google Sheets link,
   subject-by-day pacing grid, Edited badges, and a review card that lists exact
   old/new cells, affected artifacts, kept edits, and unchanged subjects. Change
   sheet displays the server-detected name, tab, week columns, subjects, and
   sample values before Save. Nothing is applied without Apply change.
3. **Plan:** course tabs with flag counts and editable weekday rows showing the
   source value, In Class/At Home plan, assignments, due dates, and reminders.
   Edits autosave into owner overrides, regenerate the proposal, enter history,
   and can be undone.
4. **AI review:** per-course state, evidence-bearing structured findings and
   one-click answers, the eight required checks, and recorded model. A missing
   reviewer becomes explicit UNAVAILABLE after the edit debounce and never PASS.
5. **Preview & approve:** exact page and announcement HTML in sandboxed Canvas-
   styled frames, Desktop/Phone widths, assignments/reminders, AI state, atomic
   course approval, and reapproval diffs. Math page and announcement were
   visually inspected in Chrome; their embedded agenda was identical.
6. **Friday:** automatic-rollover preference, all-five readiness gate, exact
   five-step package description, GET-only dry run, warned/typed partial publish,
   and prior verified result. The 1 PM Chief decision item is stable and local.
7. **Completed weeks:** verified ledger history, latest first.
8. **Settings:** plain-language planning mode plus the state root, source
   fingerprint, approval timestamp, page identifiers, and event history.

## Validation

| Proof | Result |
| --- | --- |
| Canvas Planner unittest discovery | 25 passed |
| Teacher Workstation unittest discovery | 14 passed, 2 sandbox port skips |
| Canvas rollover plain-Python suites | 43 passed |
| Targeted combined proof after final edits | 38 passed, 2 sandbox port skips, plus 4 rollover execution tests passed |
| `scripts/chief-of-staff-validate-all.sh` | 79 PASS / 0 WARN / 0 FAIL |
| validate-all with smoke + Phase 1 | 79 PASS / 0 WARN / 0 FAIL |
| dashboard | 160 PASS / 0 WARN / 0 FAIL |
| governance and broader status commands | all passed |
| Current flat repo set (`tests/*.sh`, `tests/*.py`, three unittest suites) | 149 passed / 10 failed across 159 commands |
| Historical REL-2 167-command set | 159 passed / 8 failed; zero new failures versus 157 passed / 10 failed |

The eight historical failures are the same environment/legacy failures already
recorded in `docs/rel-2-baseline.md`: three missing-Q1W5 launcher cases,
grade-check local scheduler/state, Phase 22 ignored local metadata, Phase 23
loopback binding, Canvas Planner launcher loopback binding, and the old Teacher
Workstation Q2W3 fixture assumption. Two historical failures now pass: Canvas
intake and Phase 22 canonical knowledge.

The current flat set adds four post-baseline commands. Two pass. Two retain
their already-recorded fixture/date failures: `canvas-agenda-date-standardization-test.sh`
and `q2w3-corrective-pass-regression-test.sh`. No failure was caused by this
mission's feature code.

All new mutation and publishing tests used temporary packet roots and fake
Canvas transports. No live Canvas write or live partial/full publish ran.

## Q2W3 status contract

Captured read-only from the installed state root on 2026-10-21:

```json
{
  "domain": "canvas_weekly_planning",
  "contract_version": 1,
  "generated_at": "2026-10-21T18:35:25.005369Z",
  "week": {
    "code": "Q2W3",
    "label": "October 26–30",
    "state": "NEEDS_OWEN",
    "source_synced_at": "2026-10-19T23:14:35.076905+00:00",
    "rollover_at": "2026-10-23T20:00:00Z",
    "rollover_state": "BLOCKED"
  },
  "courses": [
    {"id":"math","name":"Math","stages":{"source":"done","plan":"to_review","ai_review":"not_run","assignments":"approved","preview":"stale"}},
    {"id":"reading_spelling","name":"Reading/Spelling","stages":{"source":"done","plan":"to_review","ai_review":"not_run","assignments":"approved","preview":"stale"}},
    {"id":"language_arts","name":"Language Arts","stages":{"source":"done","plan":"to_review","ai_review":"not_run","assignments":"approved","preview":"stale"}},
    {"id":"science","name":"Science","stages":{"source":"done","plan":"to_review","ai_review":"not_run","assignments":"not_required","preview":"stale"}},
    {"id":"homeroom","name":"Homeroom newsletter","stages":{"source":"done","plan":"done","ai_review":"not_run","assignments":"not_required","preview":"to_review"}}
  ],
  "next_action": {
    "title": "Review Math",
    "deep_link": "http://127.0.0.1:4310/#week/q2w3/math/preview"
  },
  "action_items": [
    {"id":"approval:q2w3:math","kind":"decision","title":"Review Math"},
    {"id":"approval:q2w3:reading_spelling","kind":"decision","title":"Review Reading/Spelling"},
    {"id":"approval:q2w3:language_arts","kind":"decision","title":"Review Language Arts"},
    {"id":"approval:q2w3:science","kind":"decision","title":"Review Science"},
    {"id":"approval:q2w3:homeroom","kind":"decision","title":"Review Homeroom newsletter"}
  ],
  "completed": [
    {"week":"Q2W2","result":"Published and verified","verified_at":"2026-10-17T00:40:00+00:00"}
  ]
}
```

## Open risks and operational notes

- No eligible D-026 reviewer provider is currently configured. Automatic
  review therefore reports UNAVAILABLE with its reason; Owen may approve only
  after the explicit no-AI confirmation. The structured fake-reviewer path is
  tested and ready for a separately approved provider integration.
- The daily pacing comparison is opportunistic when Owen opens Source. There
  is intentionally no daily scheduler; D-028 authorizes exactly one Friday job.
- Q2W3 is correctly BLOCKED in installed state because all five exact packages
  need review/reapproval. The scheduler will publish nothing in this state.
- The Friday LaunchAgent must be installed from merged main, not this feature
  worktree. Its paths deliberately target the installed main checkout.
- A live Canvas GET dry run and any live publish remain unexercised in this
  mission. The write engine was tested only with `FakeDeployClient`.

## Owen's exact trial and scheduler steps

Use `docs/canvas-planner-1-steps.md`. It contains the exact Planner/status/dry-
run commands and the separate install/uninstall commands for
`com.teacher-ai-workstation.canvas-friday`. Do not touch or reuse the
grade-check LaunchAgent.
