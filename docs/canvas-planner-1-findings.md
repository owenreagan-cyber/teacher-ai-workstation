# Canvas Planner 1 — Part A Findings

```text
Status: read-only investigation complete
Mission: docs/prompts/PROMPT-CANVAS-PLANNER-1.md, Part A only
Branch: feature/canvas-planner-1
Investigation date: 2026-10-20
Implementation approval: not granted by this report
```

## Executive summary

The repository already contains most of the safe execution core needed by Canvas Planner 1: a loopback-only Teacher Workstation, pacing intake and normalization, exact-HTML page generation, artifact-scoped approvals, GET-only preflight, guarded deployment with readback verification, and a Friday rollover engine with local status and ledgers. The principal gap is not Canvas transport. It is a coherent planner workflow and state authority above those components.

Four findings should shape Part B:

1. The current web application reads JSON artifacts under `.local/canvas-llm/intake` and `.local/canvas-llm/deployments`, while other canonical documentation names Phase 22/26 SQLite as the production teacher authority. The state authority must be selected explicitly before planner mutations are added.
2. Source resync currently detects changes but then rebuilds the intake packet immediately. That behavior does not satisfy the proposed review-first source-change workflow.
3. The Friday rollover engine exists, but no installed or repository-defined Friday rollover LaunchAgent or LaunchDaemon was found. Part B therefore cannot “reuse the existing scheduler job” without an owner decision about which scheduling surface to use.
4. `wip/canvas-live-q1w9` is 105 main commits behind and contains one large, mixed-purpose commit. It must not be merged or cherry-picked wholesale. A small number of pure helpers or invariants may be ported selectively after comparison with current contracts.

No runtime, Canvas, API, scheduler, or product write was performed during this investigation. No secrets or `.env` files were read.

## 1. Current architecture map

### 1.1 Teacher Workstation screens and routes

The current browser application is implemented in `apps/teacher-workstation/app.js` and served by `scripts/teacher_workstation/server.py` on `127.0.0.1:4310`.

| Current hash route | Current screen | Notes for Part B |
| --- | --- | --- |
| `#home` | Home | Summary and entry point. |
| `#weekly` | Weekly planning | Current week list; launcher opens here. |
| `#subject/<quarter>/<week>/<subject>` | Subject editor | Current per-subject work surface. |
| `#assignments` | Assignments | Cross-week assignment review. |
| `#announcements` | Announcements | Announcement editing/review. |
| `#questions` | Questions | Teacher questions and answers. |
| `#review` | Review | Exposes internal state names and hashes that should be translated for a teacher-facing UI. |
| `#deploy` | Deploy | Preflight and guarded deployment controls. |
| `#completed` | Completed | Published/completed-week view. |
| `#system` | System | Local service/status information. |

The current subject list is Math, Reading/Spelling, Language Arts, Science, and History. Homeroom is handled separately by rollover rather than as a normal subject-plan row. The proposed Part B deep links do not yet exist:

```text
#week/q2w3
#week/q2w3/source
#week/q2w3/<course>/plan
#week/q2w3/<course>/ai
#week/q2w3/<course>/preview
#week/q2w3/friday
```

The server currently exposes these read routes:

- `GET /api/status`
- `GET /api/friday-rollover`
- `GET /api/home`
- `GET /api/weeks`
- `GET /api/completed`
- `GET /api/week/{quarter}/{week}`
- `GET /api/week/{quarter}/{week}/questions`

It also exposes local mutation routes for owner overrides, source restoration, blank/pending states, question answers, assignment dispositions, announcement edits, approval/revocation, preflight, and deploy. Mutating requests are protected by loopback Host/port validation, same-origin checks, a per-start request token, JSON-only input, a 1 MB body limit, and explicit method restrictions.

`bin/teacher-workstation` currently supports `--no-open`; it does not implement `--open <route>`. `scripts/canvas_planner_app/launcher.sh` supplies the existing start/reuse/health-check mechanics but opens the fixed `#weekly` route.

### 1.2 Local state and authority surfaces

The feature worktree has no `.local` state. Filename-only inspection of the installed main checkout at `/Users/owen/Projects/teacher-ai-workstation/.local` found these relevant state families:

| State family | Location | Principal contents |
| --- | --- | --- |
| Intake | `.local/canvas-llm/intake/2026-2027/q<q>/w<w>/` | Intake manifest, pacing snapshot, normalized week, subject HTML drafts, assignment/announcement/reminder drafts, questions, teacher input, owner overrides, approval manifest, source changes, review summary. |
| Deployment | `.local/canvas-llm/deployments/2026-2027/q<q>/w<w>/` | Preflight records, deployment ledger, published-verified ledger, rollover ledger, and backups. |
| Grade check | `.local/canvas-llm/grade-check/` | State, enrollment overrides, run summaries, backups, stdout, and stderr logs. |
| Phase 22 planning | `.local/canvas-llm/phase-22-predictive-weekly-planning/` | `workstation.sqlite3`, backups, WAL/quarantine/import reports. |
| Phase 26 production | `.local/canvas-llm/phase-26-unified-weekly-production/` | `workstation.db`, exports, and quarantine data. |
| Launcher | `.local/teacher-workstation/launcher/` | Launcher log. |

The current Teacher Workstation adapter reads the JSON intake/deployment trees relative to the repository checkout. It does not use the Phase 22 or Phase 26 SQLite databases. This creates two authority problems:

- Canonical documentation that identifies SQLite as production teacher authority conflicts with the running UI's JSON-backed behavior.
- State is checkout-relative. The installed launcher and scheduled jobs point at the main checkout, while this feature worktree has no equivalent `.local` state.

Part B should use one explicit state root and one documented canonical authority. The least disruptive bounded choice is to keep the current JSON intake/deployment packets authoritative for this mission, hide them behind a single Canvas Planner service/projection layer, and schedule any SQLite migration as a separate approved mission.

### 1.3 Week resolution

`scripts/canvas_llm_intake/week_resolution.py` loads `config/curriculum/canvas/instructional-weeks-2026-2027.json` through the Phase 3 configuration surface.

- Explicit quarter/week overrides take precedence.
- “Current” means the date falls within the configured Monday-Friday instructional window.
- “Next” means the first future configured start.
- `TAW_TODAY` provides deterministic test pinning.
- The intake resolver uses a fixed UTC-4 timezone rather than `ZoneInfo("America/New_York")`, so dates after the daylight-saving transition are a correctness risk.
- The rollover scheduler logic uses `ZoneInfo("America/New_York")` and the prior Friday at 4:00 PM.
- The home adapter selects the first non-published staged week from a reverse lexical glob; that is not a durable chronological rule if week naming changes.

### 1.4 Approval store

`scripts/canvas_llm_intake/approval.py` stores approvals in `approvals/approval-manifest.json`.

Supported artifact granularities are `page`, `assignments`, `announcement`, and `assessment_reminder`. Supported states are `PENDING`, `NEEDS_CHANGES`, `APPROVED`, `BLOCKED`, and `NOT_REQUIRED`.

An approval binds the exact draft hash and source hash. A source or draft change makes the approval stale. Each approval record retains history, and deploy readiness requires every applicable artifact to be approved with no open teacher questions.

This is reusable, but Part B's single course-level “Approve” action is not currently atomic. It will need a bundle/transaction layer that approves the applicable artifacts together and records the reason and before/after diff for later reapproval. There is also no unified revision/event ledger that can undo source sync, plan edits, AI-review decisions, and approval changes consistently.

### 1.5 Source intake and synchronization

The intake path normalizes the pacing source, creates subject drafts and structured supporting artifacts, detects source deltas, records owner overrides, and generates questions.

The reusable delta logic can produce per-cell before/after values. Conflict detection is narrower: it primarily recognizes rejected assignments/reminders and does not produce a complete impact map for all retained owner overrides.

The important mismatch is in `cycle.prepare_week()`: it fetches the current pacing snapshot, detects a delta, and then calls the intake build before saving the change record. In practice the regenerated packet is applied automatically. Part B requires resync to propose changes and wait for Owen to choose apply, keep, or resolve. This behavior must be separated before the new Source stage is built.

No daily source-comparison job, source-change preview/save decision, or change-sheet UI currently exists.

### 1.6 Generators

The active production path uses these generator families:

| Output | Current implementation |
| --- | --- |
| Normalized pacing source | `scripts/canvas_llm_phase3/pacing_extractor.py` |
| Subject pages | `scripts/canvas_llm_phase3/pacing_pages.py`, orchestrated by `scripts/canvas_llm_intake/intake.py` |
| Assignments | Phase 3 subject translators (`pacing_math`, `pacing_reading`, and `pacing_translation`), normalized by intake |
| Weekly announcements | Intake announcement drafting plus `scripts/canvas_llm_rollover/narrative.py` |
| Assessment reminders | `scripts/canvas_llm_intake/reminders.py` |
| Exact deploy announcement body | `scripts/canvas_llm_deploy/plan.py` |
| Friday Homeroom content | `scripts/canvas_llm_rollover/homeroom.py` |

The deploy announcement body intentionally embeds the exact page HTML and verifies that invariant with a hash. Older Phase 22/23/24/26 generator paths remain in the repository and represent architecture debt; they should not be introduced into the Planner UI as a second generation path.

There is no current AI review service, evidence store, model-selection record, debounced review queue, or structured finding/action schema.

### 1.7 Preflight and deployment

The Teacher Workstation deploy adapter delegates to `scripts/canvas_llm_deploy`.

The current reusable protections are strong:

- Preflight is GET-only against the fake or live Canvas client.
- Preflight compares Canvas IDs, duplicate classifications, and source, snapshot, and approval hashes.
- A preflight expires after 15 minutes.
- Deploy requires production mode, exact typed confirmation, a valid unexpired preflight, and matching source/approval snapshot hashes.
- The coordinator backs up current pages, applies the planned writes, reads each target back, stops on partial failure, and writes deployment and verification ledgers.
- Fake and live clients use the same coordinator boundary.

Normal deployment writes pages, assignments, announcements, and reminders. Friday rollover separately owns front-page selection and Homeroom copy-forward. Part B must make this ownership explicit so that a Friday action cannot double-send or overlap a normal deploy.

There is one D-018 contract risk to resolve: the current UI sends the preflight ID, expected hashes, and typed confirmation, while the decision language says the UI sends only the packet ID and the core reloads the canonical packet. The coordinator revalidates state, but Part B should align the transport contract explicitly rather than silently preserving the divergence.

### 1.8 Friday rollover engine

`scripts/canvas_llm_rollover/` contains schedule, manifest, narrative, Homeroom, ledger, rollover, status, and CLI modules. `bin/canvas-weekly-rollover` is the manual command surface.

The engine already provides:

- Local readiness/preflight evaluation.
- Active-subject selection by quarter.
- Existing-page front-page selection rather than replacement-page creation.
- Homeroom copy-forward.
- Weekly communication generation.
- Post-write readback verification.
- Idempotence and a partial-failure ledger.
- Local states including `NOT_DUE`, `PREPARING`, `NEEDS_OWEN`, `READY`, `HELD_UNTIL_4PM`, `EXECUTING`, `PUBLISHED_VERIFIED`, and `BLOCKED`.

It does not provide an installed Friday scheduler, a 1:00 PM action-item reminder, an automatic/manual toggle, or a manual partial-publish confirmation workflow. The current rollover status reader is local-only and is the best starting point for the proposed B8 projection.

## 2. Reconciliation of `wip/canvas-live-q1w9` with `main`

The merge base is `0609599f6b659d90f59238340a9518760aded8c2`. At investigation time, `main` was 105 commits ahead and the WIP branch was one commit ahead. The WIP-only commit, `3f4a335` (`wip: preserve live Canvas Q1W5–Q1W9 work, grade entry, planner app`), changes 80 files with approximately 14,395 insertions and 46 deletions.

The branch is not a safe merge unit.

| File/group | Classification | Merge prerequisites or disposition |
| --- | --- | --- |
| `assistant/chief-of-staff/workspace/**` | Duplicate/parked | Historical architecture only. Chief of Staff authority says this workspace is reference material, not a merge target. |
| `.gitignore` additions for local Chief of Staff/learning state | Potentially still needed | Port only if the current owners still create those paths and current ignore rules do not already cover them. Not a Part B prerequisite. |
| Phase 23/26 demo JSON changes | Superseded | Demo/live-like data is not production authority. Do not merge. |
| Course ID `26429`, At Home labels, and canonical course mapping changes | Duplicate | Current main contains these independently through later release work and configuration. |
| Weekly-update contracts, examples, and guardrails | Mostly duplicate; examples are historical evidence | Current intake/rollover owns the exact weekly-update hash contract. Port only a demonstrably missing invariant into the current contract and tests. |
| Birthday tile helper/contract | Potentially still needed | Compare against the current Homeroom rollover contract; port only as an isolated, tested helper if still missing. |
| Language Arts alternation / “explicit CP assignment only” rules | Partly duplicate, partly conflicting | Current Phase 3 behavior covers much of it. The WIP separator change conflicts with current docs/tests. Requires an owner/canonical-format decision before selective porting. |
| Old validators, status scripts, and their tests | Superseded/duplicate | Re-express only missing invariants in the current intake/rollover suites. Do not port old status surfaces wholesale. |
| `scripts/canvas-llm/q1w5*` through `q1w9*`, build/audit/preflight/publish/repair/event scripts | Superseded operational one-offs | Retain as historical evidence only. Any extracted rule must lose hard-coded dates, course objects, and live-run assumptions and receive current tests. |
| `phase35a*` and `phase35b*` | Superseded | Replaced by `canvas_llm_deploy` and `canvas_llm_rollover`. |
| `phase2_live_sweep.py` and `phase2a_get_only_sweep.py` | Potentially still useful | Bounded GET-only archaeology may be valuable because docs reference a sweep absent from main. Port in a separate mission after endpoint, output, and no-write review. |
| `canvas_html_compat_lab.py` | Potentially still useful | Diagnostic only, not Part B core. Port separately with a clear local-only contract. |
| `ela4_grade_entry_apply.py`, `scripts/canvas_llm_grade_entry/**`, and tests | Unique but out of scope and blocked | Never merge into Canvas Planner. Requires a dedicated D-022 mission, typed per-student confirmation design, packet/security review, and isolated validation. |
| Phase 22 `homeroom_newsletter.py`, `subject_weekly_update.py`, and `playground_picnic.py` | Mixed | Some pure helpers may be reusable; current intake/rollover already covers weekly updates and Homeroom, while the picnic artifact is event-specific. Isolate and test any selected helper. |
| Phase 22 connection, writer, launcher, and workstation changes | Superseded | Current deploy client/coordinator and rollover are the maintained write path. Do not merge. |
| Phase 23/24 implementation changes | Mostly duplicate/conflicting | Course IDs and much formatting behavior are already on main; separator and assignment differences require explicit canonical decisions. Do not merge wholesale. |
| WIP tests | Evidence, not a merge unit | Port only a missing behavior into the current test organization and current authority path. |
| HTML examples | Historical evidence | Do not treat examples as authoritative production content. |

The safe reconciliation method is selective reimplementation against current contracts, not cherry-picking the WIP commit.

## 3. Scheduled-job inventory

The inventory checked the installed user and system launchd locations and launchctl registration. Exactly two installed jobs were related to Teacher AI Workstation or its Chief of Staff ecosystem. No related LaunchDaemon and no Friday rollover scheduler were found.

### 3.1 `com.teacher-ai-workstation.grade-check`

Installed plist: `~/Library/LaunchAgents/com.teacher-ai-workstation.grade-check.plist`

- Registered in the user GUI domain.
- Schedule: Monday-Friday at 4:15 PM local time.
- Program: `/bin/bash /Users/owen/Projects/teacher-ai-workstation/bin/grade-check --send`.
- Working directory: `/Users/owen/Projects/teacher-ai-workstation`.
- Environment enables the approved grade-check send path.
- At inspection: not running, four recorded runs, last exit code `1`.

Exact read scope:

- `config/canvas-llm/grade-check-config.json` and the instructional-week configuration.
- Local enrollment overrides and the previous grade-check state.
- Credentials from the process environment or the private Canvas environment file; the credential file itself was not read during this investigation.
- Canvas GET requests for course enrollments with student grade summaries, assignments, assignment groups, and student submissions.
- Active core courses by quarter; Homeroom is excluded.

Exact write/send scope:

- It performs no Canvas writes; the Canvas reader implements GET only.
- Preview mode does not persist state.
- Send mode may send one consolidated report to Owen's allowlisted address through Gmail or explicitly enabled SMTP. It never sends to parents.
- Only after a successful send, it atomically updates `.local/canvas-llm/grade-check/state.json` and appends a privacy-reduced run summary to `logs/grade-check.runs.jsonl`.
- It also emits stdout/stderr logs and maintains local backups.

This job must remain isolated from Canvas Planner. D-022's per-student typed confirmation applies to grade changes; this job does not change grades. Its persistent launchd send approval is nevertheless not an authorization mechanism for planner publishing. Its last exit code should be investigated independently before anyone relies on it.

### 3.2 `com.owen.chief-evals`

Installed plist: `~/Library/LaunchAgents/com.owen.chief-evals.plist`

- Registered in the user GUI domain.
- Schedule: nightly at 2:00 AM.
- Program: `/opt/homebrew/bin/python3.12 /Users/owen/Projects/taw-cos-m1/evals/harness/run.py --model real --repeat-fast-path 360 --long-session 500 --quiet`.
- At inspection: not running, six recorded runs, last exit code `0`.
- It targets the separate/stale `taw-cos-m1` checkout, not this worktree.

The repository copy under `evals/launchd/` describes the job as prepared but not loaded, which is stale relative to the installed machine state.

### 3.3 Scheduler conclusion

No installed job invokes `bin/canvas-weekly-rollover`, the rollover package, or a Friday 4:00 PM planner action. No matching job was found in `/Library/LaunchAgents` or `/Library/LaunchDaemons`.

Part B must not repurpose the grade-check job: it runs at the wrong time, has a different data classification and safety contract, and belongs to a deliberately isolated grade domain. Creating a new scheduler is also outside Part A and conflicts with the prompt's instruction to reuse an existing job. Owen must resolve whether an uninstalled intended job exists elsewhere or authorize a bounded scheduler addition in Part B.

## 4. Reusable interfaces, missing interfaces, and Part B work

### 4.1 Reusable now

- Loopback-only HTTP service, static application shell, and mutation request guards.
- Intake normalization, source snapshots, per-cell delta detection, owner overrides, teacher input, and question IDs.
- Exact-HTML page and supporting-artifact generation.
- Hash-bound artifact approvals and stale-approval detection.
- Fake/live Canvas client boundary.
- GET-only preflight, expiring evidence, guarded coordinator, backups, readback, and deployment ledgers.
- Rollover schedule calculations, manifest, narrative, Homeroom copy-forward, status, CLI, idempotence, and verification ledger.
- Launcher health/start/reuse mechanics.
- Completed/published evidence from verified ledgers.

### 4.2 Missing interfaces

- One canonical persistence authority and explicit state-root selection.
- Append-only revision/event history and consistent undo.
- Review-first source resync with apply/keep/resolve decisions.
- Complete owner-override impact analysis.
- Daily source comparison and a source-change action surface.
- The proposed five-stage planner shell, Week overview, actions, Completed weeks, and Settings.
- Structured AI review, evidence citations, debounce, model/entitlement recording, unavailable state, and action IDs.
- Exact-HTML side-by-side preview, phone-width toggle, and safe preview isolation.
- Atomic course-level approval with a human-readable reapproval diff.
- Local weekly status projection and CLI.
- Validated deep-link parsing and `teacher-workstation --open`.
- Friday 1:00 PM action, automatic/manual toggle, default all-or-nothing behavior, and separately confirmed manual partial publish.
- An actual Friday rollover scheduler or an approved alternative.
- Teacher-language translations for internal states and hashes.

### 4.3 Scope that belongs in Part B

Part B should assemble the planner above the current intake, approval, deploy, and rollover cores. It should not introduce a second Canvas client, a second deployment coordinator, a second rollover engine, or a grade-domain dependency. Any state migration, new scheduler, or WIP archaeology that cannot fit those boundaries should be split into an owner-approved prerequisite mission.

## 5. Proposed B8 status contract

The status command should be a pure projection of local cached state. It must not import or construct a Canvas client and must remain functional under an explicit network-denied test.

### 5.1 Command and service boundaries

```text
bin/canvas-weekly-status --json
bin/teacher-workstation --open "week/q2w3/math/preview"
```

The status projector should live in the Canvas/Pacing domain, not Chief of Staff. It should read only the selected local state root: intake manifest, source snapshot, change set, overrides, questions, approval manifest and draft hashes, a future AI-review record, rollover status/ledger, and published-verified ledgers.

The opener should validate the route, reuse a healthy local server or start one, and open the corresponding loopback URL. Existing hashes should remain temporary aliases during migration, for example `#weekly` and `#subject/2/3/math`.

### 5.2 Week-state projection

The proposed precedence is:

1. `PUBLISHED_VERIFIED` when a verified publish ledger is current.
2. `EXECUTING` while a rollover execution ledger is active.
3. `BLOCKED` for hard readiness, integrity, or deployment blockers.
4. `NEEDS_OWEN` for unresolved source changes, plan flags, AI findings, questions, or approvals.
5. `READY_TO_PUBLISH` when ready and due. This maps the rollover engine's current `READY` state into the B8 vocabulary.
6. `HELD_UNTIL_4PM` when ready before the scheduled time.
7. `AI_REVIEWED` when all required structured reviews are current and passed.
8. `PLANNED` when required course plans are complete.
9. `SOURCE_SYNCED` when the current source snapshot exists and has no unresolved delta.

The active course set should be derived from quarter configuration, plus Homeroom. For Q2 that is Math, Reading/Spelling, Language Arts, Science, and Homeroom; History replaces Science in Q1/Q3.

### 5.3 Stage projection

| Stage | Suggested projected states | Evidence |
| --- | --- | --- |
| Source | `missing`, `synced`, `changed`, `needs_you` | Source snapshot and unresolved `changes.json` decisions. |
| Plan | `not_started`, `planned`, `to_review`, `blocked` | Normalized plan state, open teacher flags, owner overrides, and questions. |
| AI review | `not_run`, `unavailable`, `passed`, `needs_you`, `stale` | Future structured AI-review record bound to source/plan hashes and model identity. |
| Preview & approve | `to_review`, `approved`, `stale`, `blocked`, `not_required` | Aggregate of applicable page, assignment, announcement, and reminder approvals. |
| Friday | Existing rollover states projected to the B8 vocabulary | Rollover status, readiness evidence, schedule, and verified ledger. |

### 5.4 Deterministic next actions and deep links

Next actions should be ordered deterministically by blocker severity, week, course order, stage order, and stable action ID. Suggested IDs:

- Source change: a stable cell identifier or hash of week, course, day, before, and after while unresolved.
- Teacher question: the existing `question_id`.
- AI finding: a persistent finding ID stored with the future review record.
- Approval: `approval:<week>:<course>`.
- Friday readiness: `friday-readiness:<week>`.

Resolved items should disappear from the active list while retaining their creation and resolution history in the local event record. Content changes should update `updated_at` without silently minting unrelated actions.

Each action should carry one exact deep link:

```text
http://127.0.0.1:4310/#week/q2w3
http://127.0.0.1:4310/#week/q2w3/source
http://127.0.0.1:4310/#week/q2w3/math/plan
http://127.0.0.1:4310/#week/q2w3/math/ai
http://127.0.0.1:4310/#week/q2w3/math/preview
http://127.0.0.1:4310/#week/q2w3/friday
```

## 6. Risks and recommended Part B build order

### 6.1 Principal risks

1. **Split authority:** JSON intake/deployment state, Phase 22 SQLite, Phase 26 SQLite, and checkout-relative `.local` roots disagree about the source of truth.
2. **Stale authority text:** Some Canvas program documentation still describes runtime as blocked or SQLite as the only production authority despite the current approved deploy/rollover paths.
3. **Missing scheduler:** The requested reusable Friday scheduler was not found.
4. **Grade-domain contamination:** Reusing grade-check scheduling or code would violate the intended D-022 isolation and use the wrong timing and approval model.
5. **Source auto-apply:** Current resync rebuilds content before teacher acceptance.
6. **Approval mismatch:** Existing approvals are artifact-granular; Part B asks for an atomic course-level action and meaningful reapproval diff.
7. **No AI review layer:** Entitlement, router, evidence, structured findings, fallback, and local action persistence are all absent.
8. **D-018 transport mismatch:** The current UI/core payload contract should be reconciled with the packet-only decision language.
9. **Incomplete history:** Not every mutation records a durable reason, before/after state, or undoable revision.
10. **Preview security:** Exact HTML preview requires strong iframe/CSP isolation without altering deploy bytes.
11. **Overlapping publish paths:** Normal deploy and Friday rollover can own adjacent artifacts; their responsibilities must be unambiguous.
12. **Timezone inconsistency:** Intake week resolution uses fixed UTC-4 while rollover uses `America/New_York`.
13. **Unsafe WIP merge:** The WIP branch mixes historical live operations, planner experiments, grade writing, and duplicated infrastructure.
14. **Environment drift:** The feature worktree has no local state, while installed launchers/jobs point at other checkouts.
15. **Grade-check health:** The installed job's last exit code is `1`.

### 6.2 Recommended build order

0. **Owner decisions and gate check.** Select the canonical planner state/root, resolve the stale authority language, and decide how the absent Friday scheduler requirement will be handled. Recommended bounded choice: retain the current JSON packet authority for this mission and defer SQLite migration.
1. **B8 foundation first.** Implement the local-only status projection, validated deep-link parser, route opener, deterministic action IDs, and network-denial tests.
2. **Revision and source-change foundation.** Add an append-only revision/event layer; split source comparison from application; implement apply/keep/resolve and complete override impact reporting.
3. **Planner shell.** Build Week overview and the Source/Plan/AI/Preview/Friday stages from the status projection rather than duplicating state logic in the browser.
4. **Plan editing.** Connect plan changes, assignment impact, owner overrides, reason capture, history, and undo.
5. **AI review.** Add structured evidence-backed findings, debounce, model/entitlement record, stable action IDs, stale detection, and explicit unavailable behavior.
6. **Preview and approval.** Render the exact deploy HTML safely, add the phone-width view, aggregate approvals atomically by course, and show the reapproval diff.
7. **Friday workflow.** Add readiness presentation, all-or-nothing default, explicitly confirmed manual partial publish, 1:00 PM action creation, and scheduler integration only after the owner resolves the missing-job finding.
8. **Migration and proof.** Move the launcher default to the new Week route, retain legacy route aliases temporarily, run fake-transport and security regression suites, and verify screenshots and deep links without live writes.

## 7. Part A boundary confirmation

This report is the only repository change made for Part A. The investigation used read-only repository, git, local-state filename, plist, and launchctl inspection. It did not call Canvas, run AI generation, inspect secrets, mutate `.local` state, install tools, change launchd configuration, implement Part B, or perform any live write.
