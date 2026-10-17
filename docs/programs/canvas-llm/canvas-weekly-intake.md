# Canvas Weekly Intake + Staging Workspace

```text
Status: active (local-first, read-only intake/staging)
Authority: OWNER_POLICY + reused Phase 3 pacing engine
Command: bin/canvas-intake
```

## Purpose

Turn the connected 2026-2027 FPK Pacing Guides (teacher tab `4A - Reagan`) into
a teacher-reviewable staging packet **before** any Canvas write. Intake and
publishing are deliberately separate: this system can never reach
`PUBLISHED_VERIFIED`, and the guarded deployment workflow performs all Canvas
writes later.

## Source priority

```text
newest explicit Owen instruction
> current live pacing
> approved/locked decisions
> canonical source files
> older project history
> model inference
```

Blank pacing cells remain blank. Never shift pacing, infer missing lessons,
move content across days, or invent assignments because a cell is blank.

## Lifecycle

```text
SOURCE_FETCHED -> NORMALIZED -> DRAFTED -> NEEDS_INPUT
-> READY_FOR_REVIEW -> TEACHER_APPROVED -> READY_TO_PUBLISH
-> PUBLISHED_VERIFIED
```

- `NEEDS_INPUT` is set automatically when open questions exist.
- `TEACHER_APPROVED` and `READY_TO_PUBLISH` are **never** set automatically.
- `PUBLISHED_VERIFIED` is only reachable by the separate deployment workflow.

## Staging workspace

Everything is local + gitignored under `.local/canvas-llm/intake/`:

```text
2026-2027/
  q2/
    w2/
      source/pacing-snapshot.json
      normalized/week.json
      drafts/{math,reading,language-arts,science}-page.html
      drafts/assignments.json
      drafts/announcements.json
      questions/questions.json + questions.md
      intake-manifest.json
      REVIEW.md
```

## CLI

```bash
bin/canvas-intake prepare-next               # recurring: prepare the next unprepared week
bin/canvas-intake run --week next            # fetch + normalize + draft + questions
bin/canvas-intake run --quarter 2 --week 2   # explicit + deterministic
bin/canvas-intake run --live-context         # add GET-only page lookup + duplicate check
bin/canvas-intake review                     # print REVIEW.md (primary Owen view)
bin/canvas-intake questions                  # list open questions (--status answered|all)
bin/canvas-intake apply-teacher-input        # answer a question / add reminder / reject assignment
bin/canvas-intake approve --subject math --all   # approve page+assignments+announcement
bin/canvas-intake status                     # PASS/WARN/FAIL proof (completed vs next-prepared)
bin/canvas-intake self-test                  # synthetic tests
```

`prepare-next` resolves the next instructional week that is NOT already
`PUBLISHED_VERIFIED`, fetches authoritative pacing, detects source delta
(`NEW` / `UNCHANGED` / `CHANGED`), preserves owner overrides, and stops at
`READY_TO_PUBLISH`. It never deploys.

## Recurring cycle

```text
AUTHORITATIVE PACING -> DETECT NEXT WEEK -> SNAPSHOT -> NORMALIZE -> DRAFT
-> COMPARE TO PRIOR/EXISTING STATE -> SURFACE DELTAS / QUESTIONS
-> TEACHER INPUT -> APPROVAL -> READY_TO_PUBLISH -> STOP
```

- **Delta detection** — fresh source hash vs existing packet: `NEW` (no packet),
  `UNCHANGED` (preserve approvals/drafts), `CHANGED` (per-cell diff; regenerate
  only affected artifacts; invalidate only affected approvals).
- **Owner-override precedence** — `newest explicit Owen instruction > live pacing
  > locked decisions > canonical files > history > model inference`. A refreshed
  pacing that conflicts with local teacher input surfaces
  `SOURCE_CHANGED_AFTER_OWNER_OVERRIDE` and requires Owen review.
- **Assessment reminders** are drafted locally (never posted): Math
  Written+Fact Assessment (Fact Test → Power Up via
  `fact-test-practice-map.json`), Spelling test (authoritative list range). A
  reminder must be explicitly approved before it is included in `READY_TO_PUBLISH`.

## Announcement scheduling semantics (verified)

Canvas honors `delayed_post_at`. Do NOT interpret `published=true` or
`posted_at == created_at` as early publication. The reliable "visible to
students" signal is **active-feed membership**:

```text
future delayed_post_at AND not in active_only feed  -> HELD (correct)
future delayed_post_at AND in active_only feed      -> PREMATURE (FAIL)
delayed time passed AND in active_only feed         -> POSTED (expected)
published=false AND not active AND not scheduled     -> DRAFT_UNPUBLISHED
```

Encoded in `scripts/canvas_llm_intake/scheduling.py`.

## Reused components

The intake layer reuses the Phase 3 pacing engine rather than duplicating it:

- `scripts/canvas_llm_phase3/pacing_extractor.py` — live sheet fetch + normalized week
- `scripts/canvas_llm_phase3/pacing_math.py` — Math lesson/assessment rules
- `scripts/canvas_llm_phase3/pacing_reading.py` — Reading/Spelling rules
- `scripts/canvas_llm_phase3/pacing_translation.py` — Shurley / History / Science rules
- `scripts/canvas_llm_phase3/canvas_preview.py` — agenda HTML (`kl_wrapper_3`)
- `scripts/canvas_llm_phase3/pacing_announcement.py` — assessment facts
- `config/curriculum/canvas/canvas-course-mappings.json` — course IDs
- `config/curriculum/canvas/quarter-subject-activation-2026-2027.json` — rotation
- `config/curriculum/canvas/assignment-routing-contract-2026-2027.json` — routing + defaults

## Assignment proposal

Proposals are staging-only. Canonical defaults:

```text
points_possible = 100
grading_type = percent
submission_types = ["on_paper"]
omit_from_final_grade = false
due = 11:59 PM America/New_York
```

Auto-propose only: Math homework/classwork/assessments, Reading/Spelling
workbook/assessment/spelling-test, Language Arts Classroom Practice + Chapter
Test. History/Science auto-propose only explicit Chapter Test / Quiz. Every
proposal carries `requires_teacher_approval: true`.

## Duplicate prevention

With `--live-context`, the intake performs GET-only lookups of the pre-created
weekly page (by canonical slug) and lists existing assignments, classifying each
proposal as `EXISTS_EXACT` / `NEW_PROPOSAL`. It never POSTs.

## Teacher input

Teacher input is recorded in `teacher-input.json` (gitignored) and applied on
regeneration without overwriting `source/pacing-snapshot.json` or the
normalized interpretation. The invariant is:

```text
SOURCE + NORMALIZED SOURCE + TEACHER INPUT = REGENERATED DRAFT
```

Supported operations: answer a question, add a reminder/note/special-event/
assessment-note, reject or restore an assignment proposal, and replace
announcement wording. Owen never edits generated HTML directly.

## Approval

Approval is explicit and granular (subject `page` / `assignments` /
`announcement`). States: `PENDING`, `NEEDS_CHANGES`, `APPROVED`, `BLOCKED`.
Approval binds to the current draft hash; any regeneration that changes an
approved artifact reverts it to `PENDING`. Absence of a response is never
approval.

## READY_TO_PUBLISH gate

A week reaches `READY_TO_PUBLISH` only when:

- pacing snapshot valid, active subjects correct
- page drafts generated, no blocking unresolved questions
- assignment proposals resolved, reminders + announcements generated
- `weekly_update_agenda_hash == page_agenda_hash` for every announcement
- required artifacts (page/announcement always; assignments if proposed) approved
- no `BLOCKED` approval states

Artifacts that do not apply (e.g. Science with no proposed assignments) are not
required. Partial approval is supported; a partially-approved week is
`READY_FOR_REVIEW`, never `READY_TO_PUBLISH`.

## Parser clarifications (owner-evidence-backed)

- **Reading bare numbers** — a bare integer in the Reading pacing field is a
  Reading Mastery lesson number (live sheet runs `L37 L38 L39 L40` then
  `41 42 43 44 45` then `46…50`, continuing the numeric progression). `41` →
  `Lesson 41`.
- **Math `FA6*` marker** — the `*` is stripped for identifier extraction
  (`FA6` → Fact Assessment 6) but the marker is preserved with
  `meaning: UNKNOWN` and surfaced as an open question. The marker semantics
  remain unresolved until Owen defines them.

## Deployment boundary

This package performs **no Canvas writes**. `POST`/`PUT`/`PATCH`/`DELETE` are
statically forbidden (zero-write proof). Publishing is a separate guarded
deployment phase.
