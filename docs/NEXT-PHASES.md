# Chief of Staff — Next Phases: Testing Ground and Improvement Plan

Status: PROPOSED · 2026-10-01
Builds on `CHIEF-OF-STAFF.md` (A+ plan). Covers what comes after M1, M1.5A, and E1 Part 1.

---

## Where things stand

| Item | State |
|---|---|
| M1 core (`cos` CLI, tools, policy gate, audit, kill switch, fast path) | Built, reviewed, live-checked |
| M1.5A desktop shell (Chief.app, Electron) | Built, reviewed, hardened; owner live checks and install pending |
| E1 Part 1 harness (fixtures, 8 suites, CERT-001–007, reports) | Built; first run 157/160 fake, 32/32 real fast path |
| E1 fix batch (sessions, `think: false`, report labels, clean-tree flag) | In progress |
| Branches | `feature/cos-m1` → `feature/cos-m15a` → `feature/cos-e1-harness`, all unmerged, in worktree `~/Projects/taw-cos-m1` |

---

## Standing rules for every phase

1. **The harness grows with the product.** Every phase that adds behavior adds test cases and,
   for any new safety rule, a new CERT invariant. CERT IDs never change meaning.
2. **Certification runs come from a clean commit.** A run from uncommitted code is a
   development run only (the report says so).
3. **Nightly regression.** Once the overnight job is installed, every morning shows whether
   anything broke. A failing nightly blocks merging.
4. **One builder, one reviewer.** Claude Code builds. A non-Claude reviewer reviews any phase
   that touches security, privacy, authority, the bridge, or routing. Docs and test-only phases
   need no review round.
5. **Failures found by the harness are listed, then fixed in a separate batch.** Never fixed
   silently in the same task that found them.
6. **Owen's real use decides product questions.** Tests decide correctness. The notes file
   decides what to build next.

---

## Phase sequence

### F1 — E1 fix batch (now)

- Session robustness: torn line, directory path, symlink path.
- `think: false` as config `model_think`, recorded in audit.
- Fake-run labels; clean-tree certification flag; soak default 360.

**Exit:**
- fake run 160/160 with all CERT checks passing, on a clean commit
- before/after model latency measured

### G1 — Latency decision gate

| Model-path latency (real, `tool_choice` suite) | Decision |
|---|---|
| p50 ≤ 5 s and p95 ≤ 15 s | Keep `qwen3.6:35b` with thinking off. Skip E1.5. |
| Otherwise | Run E1.5 before daily use. |

Answer quality must not visibly drop. If it does, revisit thinking per task (M2 router).

### E1.5 — Local model benchmark (only if G1 fails)

- **Change:** add the harness flag `--ollama-model <name>`.
- **Models:** run the `tool_choice` and `honesty` suites on `qwen3.6:35b` (thinking off),
  `gpt-oss:20b`, and `llama3.2`. Installed models only.
- **Report per model:** pass rate, p50/p95, memory free, three sample answers.

**Exit:** a chosen default model, plus an optional small resident model for quick follow-ups,
backed by data.

### L1 — Live use week (starts as soon as F1 passes; runs alongside E1 Parts 2–3)

- Install signed Chief.app and keep it open all school day.
- Projector mirror test once at school, before using it in class.
- Notes go to `~/Desktop/cos-m1-notes.txt`.
- Install the nightly harness job.

**Exit:**
- five school days of use
- notes file reviewed
- no blocking bugs
- nightly runs green

### E1 Part 2 — Answer quality and personality

- **Personality spec** (`cos/personality.md`), owner-edited: tone, length, how Chief says "I
  can't do that yet," and how it admits missing data.
- **Judge:** local Qwen scores each answer against a rubric: correct, concise, honest, on-tone,
  no invented facts. Because fixtures are synthetic, a cloud judge may also score a sample as an
  independent check.
- **Variation generator:** expands the ~160 hand-written cases into ~1,500 paraphrases. Owen
  skims a sample before they are used.
- **New honesty cases** from E1 findings, for example "battery this week" (no history).
- **New invariant:** CERT-008, no answer claims an action was taken (sent, posted, deleted,
  scheduled).

**Exit:**
- judge scores recorded per run
- the personality spec approved by Owen
- the ~1,500-case run completed overnight

### E1 Part 3 — Desktop window tests

- Playwright drives Chief.app with a fake `cos`:
  - send
  - pin
  - hide and show
  - Brief
  - Stop and Resume
  - history after restart
  - long answers
  - errors
  - model-unavailable state
- Screenshots at each step. A vision model scores layout and readability.
- Baseline screenshots, with differences flagged on later runs.
- Runs overnight, because it opens a window on the Mac.

**Exit:** the window suite is green and the screenshot baseline is approved by Owen.

### Merge gate (after L1, E1 Part 2, and F1)

1. Certification run on a clean commit.
2. Merge `feature/cos-e1-harness` (which contains M1 and M1.5A) into `main`.
3. Stage 0 consolidation PR: bring D1 (`tools/dev_safety/`, settings) and the design docs from
   `feature/cos-pacing-intelligence` onto `main`. Archive the recovery worktree.
4. Update Chief.app's `cosPath` to `~/Projects/teacher-ai-workstation/bin/cos`. Retire the
   worktree.

### M1.5B — Shell and daily-use improvements (from L1 notes plus this queue)

- **Auto-hide:** Chief hides when a display is added or mirroring starts, showing "Chief hidden:
  external display" until Owen brings it back.
- **Start at login.**
- **`cosd` background daemon:** owns sessions and status, so the app stops starting `cos` per
  request.
- **Status cache:** the audit check is keyed to file size and modification time, so the 30-second
  status poll doesn't re-verify the whole log.
- **Bridge naming:** rename `onEvent` to `subscribeWindowEvents`.
- **App icon.**
- **Fast-path additions,** only if notes show repeated phrasings.
- **Script hash pinning:** for wrapped legacy status commands, replace the bash lexer check with
  a hash pin.
- **Tests:** harness suites for each change, plus window tests for auto-hide.

### M2 — Router v1 and the first cloud model

- **Data classes enforced in code.** School-account calendar events and anything from school
  mail are student-data class: local only.
- **Worker registry:** local Qwen, the optional small resident model, and one cloud model
  behind a LiteLLM key with a model allowlist and a hard monthly budget.
- **Model rules:** stay on the resident model unless a request needs another. Thinking only for
  tasks marked as hard.
- **Approval queue** for the first write tools, starting with Reminders: confirm before
  creating.
- **Mail:** read-only local Mail triage through the quarantine reader.
- **New invariants:**
  - CERT-009: no student-data-class content reaches a cloud worker.
  - CERT-010: budget cap enforced.
  - CERT-011: no write without an approval record.
- **Review:** a cross-model security review is required.

### M3 — Memory and project awareness

- Pending "remember that…" with Owen's confirmation, typed memory items, and scoped recall.
- Project registry; "what am I working on?" from repo activity.
- Harness memory suites: confirmed-only writes, no memory from untrusted content.

### Canvas track (C0–C3, may start after M2)

- **C0:** inventory of existing Canvas work.
- **C1:** pacing readiness.
- **C2:** build and render.
- **C3:** deploy with a sealed approval packet and readback.
- Each step adds harness suites against fixture Canvas data. Real Canvas reads come from
  Owen-run snapshots only.

---

## Targets tracked every run

| Metric | Target |
|---|---|
| CERT invariants | all PASS |
| Fake-run pass rate | 100% |
| Fast path, wall time | p95 < 200 ms |
| Model path, real (`tool_choice`) | p50 ≤ 5 s, p95 ≤ 15 s (after F1) |
| Judge score (Part 2+) | Owen sets the floor after the first scored run |
| Memory free with the default model loaded | ≥ 15% |
| Owen-reported friction items per week | trending down |

---

## Immediate next actions

1. Finish F1. Paste the latency table, three sample answers, and the fake-run result.
2. G1 decision.
3. Install the signed Chief.app and start L1. In the same week, build E1 Part 2.
