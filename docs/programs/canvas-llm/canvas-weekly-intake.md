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
bin/canvas-intake --week next            # resolve next instructional week
bin/canvas-intake --week current         # resolve current instructional week
bin/canvas-intake --quarter 2 --week 2   # explicit + deterministic
bin/canvas-intake run --live-context     # add GET-only page lookup + duplicate check
bin/canvas-intake review                 # print REVIEW.md
bin/canvas-intake questions              # list open questions
bin/canvas-intake status                 # PASS/WARN/FAIL proof
bin/canvas-intake self-test              # synthetic tests
```

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

## Approval gate

Approval is explicit and granular (week / subject / page / assignments /
announcement). States: `PENDING`, `NEEDS_CHANGES`, `APPROVED`, `BLOCKED`.
Absence of a response is never approval.

## Deployment boundary

This package performs **no Canvas writes**. `POST`/`PUT`/`PATCH`/`DELETE` are
statically forbidden (zero-write proof). Publishing is a separate guarded
deployment phase.
