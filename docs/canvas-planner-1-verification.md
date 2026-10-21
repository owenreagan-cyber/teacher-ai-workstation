# Canvas Planner 1 — pre-PR verification

Date: 2026-10-21

Branch: `feature/canvas-planner-1`

Limits observed: no push, install, or live Canvas write

## AI review

No production code path calls a model today. `ai_review.run()` can call an
injected `Reviewer`, and tests use a fake, but no D-026 router/provider supplies
one in the app. Therefore there is no current production model name or model
selection. A future provider must use D-026's measured-entitlement routing and
the persisted record will show `reviewer.model`.

With an eligible injected reviewer, Owen sees structured per-course findings,
evidence, check results, and the recorded model. Without one, the debounce ends
in explicit `UNAVAILABLE`, the AI screen shows the reason, and Preview requires
Owen to check “I reviewed this without AI” before approval. Unavailable never
becomes PASS.

## Old UI feature parity

| Old 917-line capability | Current location |
| --- | --- |
| Owner overrides | Plan weekday In Class/At Home fields; 700 ms local autosave |
| Question answering | Plan → per-course Questions; Answer and Use recommended |
| Assignment dispositions | Plan → each proposed assignment has Reject proposal; server retains KEEP/REJECT/RESTORE operations |
| Announcement editing | Preview & approve → Edit announcement |
| Restore source | Plan → Restore source on each weekday |
| Blank / pending | Plan → Mark pending and Intentionally blank on each weekday |
| Completed weeks | Completed weeks navigation entry |
| System status | Settings → System status, from the same Planner projection |

All eight remain. The parity audit restored the four controls that had dropped
from the redesigned screen: question answers, assignment rejection,
restore-source, and pending/blank. It also restored System status under
Settings. No old Deploy screen was restored: D-028 intentionally removed that
second publisher.

## Visual check

The first fixture-server launch failed with `PermissionError: [Errno 1]` when
the sandbox denied the localhost bind. After localhost permission was granted,
Chrome rendered fixture-only data for:

- Week overview and five-course stage table;
- Math Plan, including restored source/pending/blank, question-answer, and
  assignment-rejection controls;
- Settings, including the System status projection;
- Math exact Preview, including both sandboxed page and announcement frames.

The desktop Preview screenshot visibly showed the same `math exact agenda` in
the page and announcement. Source, AI review, Friday, Completed weeks, phone
width, and interaction results were not visually verified. No mutation control
was clicked, no installed state was used, and no Canvas request was made.

## Test-count reconciliation

The figures describe different command inventories:

- **Current flat inventory:** 159 commands = 149 pass + 10 fail.
- **Historical REL-2 inventory:** 167 commands = 159 pass + 8 fail. This is the
  original 155 flat commands plus 12 authority/proof commands. REL-2 originally
  recorded 157 pass + 10 fail; two historical failures now pass.
- **Current expanded comparison:** 171 commands = 161 pass + 10 fail: the 167
  historical commands plus four post-baseline commands (two pass, two fail).

Thus `159/8` means 159 passed and 8 failed out of the 167-command historical
inventory; it does not mean 159 total. `149/10 of 159` is the current flat
inventory.

The eight historical failing commands are:

1. `canvas-llm-canvas-launch-approval-test.sh`
2. `canvas-llm-canvas-launch-test.sh`
3. `canvas-llm-canvas-launch-transport-test.sh`
4. `canvas-llm-grade-check-test.sh`
5. `canvas-llm-phase-22-predictive-weekly-planning-workstation-test.sh`
6. `canvas-llm-phase-23-weekly-content-production-engine-test.sh`
7. `canvas-planner-launcher-test.sh`
8. `teacher-workstation-ui-test.sh`

The two additional current failures are:

9. `canvas-agenda-date-standardization-test.sh`
10. `q2w3-corrective-pass-regression-test.sh`

## Publishing change

Compared with the pre-Part-B rollover, the rollover now makes these additional
Canvas writes, only when the exact approved live object does not already match:

1. `PUT` each academic weekly page body to the exact approved HTML. The old
   rollover only made the existing academic page the front page.
2. `POST` approved assignments. The old rollover created no assignments.
3. `POST` approved assessment reminders as announcements. The old rollover
   created only weekly-update announcements.

Existing write classes remain: academic front-page `PUT`, Homeroom copy-forward
page `PUT`, Homeroom front-page `PUT`, and weekly-update announcement `POST`.
Every new and existing artifact is read back and verified. Ledger/event writes
are local files, not Canvas writes.

The legacy direct deploy route and non-dry-run deploy CLI both return blocked.
Repository search found no `coordinator.deploy()` caller and no LaunchAgent,
script, or maintained documentation command invoking the disabled deploy CLI.
`scripts/canvas_llm_deploy/cli.py` still registers its own blocked command and
the legacy workflow doc names it only to state that it is blocked. Tests may
call the blocked function directly to prove the boundary.

## Friday LaunchAgent (full repository contents)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<!-- Prepared in-repo only. Do not load from a feature checkout. -->
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.teacher-ai-workstation.canvas-friday</string>
  <key>ProgramArguments</key>
  <array>
    <string>/Users/owen/Projects/teacher-ai-workstation/bin/canvas-weekly-rollover</string>
    <string>--scheduled</string>
  </array>
  <key>WorkingDirectory</key>
  <string>/Users/owen/Projects/teacher-ai-workstation</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin</string>
    <key>TAW_STATE_ROOT</key>
    <string>/Users/owen/Projects/teacher-ai-workstation/.local</string>
  </dict>
  <key>StartCalendarInterval</key>
  <array>
    <dict>
      <key>Weekday</key><integer>5</integer>
      <key>Hour</key><integer>13</integer>
      <key>Minute</key><integer>0</integer>
    </dict>
    <dict>
      <key>Weekday</key><integer>5</integer>
      <key>Hour</key><integer>16</integer>
      <key>Minute</key><integer>0</integer>
    </dict>
  </array>
  <key>StandardOutPath</key>
  <string>/Users/owen/Projects/teacher-ai-workstation/.local/canvas-planner/logs/friday-rollover.log</string>
  <key>StandardErrorPath</key>
  <string>/Users/owen/Projects/teacher-ai-workstation/.local/canvas-planner/logs/friday-rollover.log</string>
  <key>RunAtLoad</key>
  <false/>
</dict>
</plist>
```

It targets only `/Users/owen/Projects/teacher-ai-workstation`, and its complete
`ProgramArguments` array is exactly that checkout's
`bin/canvas-weekly-rollover` plus `--scheduled`. It was not installed or loaded.

## GET-only live dry run

`bin/canvas-weekly-rollover --dry-run --live-readonly` defaults to the next
instructional week, loads the live transport, performs only Canvas GETs, and
classifies the exact page-body, front-page, assignment, weekly-update, and
assessment-reminder actions as CREATE/UPDATE/SET_FRONT_PAGE/SKIP. Its output
includes `CANVAS_WRITES_PERFORMED: 0`. The exact installed-main command is in
`docs/canvas-planner-1-steps.md`. This mission tested the path only with
`FakeDeployClient`; it did not run the live command.

## Final proof after the main merge

- Canvas Planner: 27 passed.
- Teacher Workstation: 14 passed, 2 loopback-only tests skipped by the sandbox.
- Rollover: 43 passed.
- `scripts/chief-of-staff-validate-all.sh`: 79 PASS / 0 WARN / 0 FAIL.
- JavaScript syntax, `git diff --check`, and Friday plist lint: PASS.
