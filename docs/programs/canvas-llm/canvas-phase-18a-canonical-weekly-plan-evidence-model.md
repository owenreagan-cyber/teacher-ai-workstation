# Canvas LLM Phase 18A — Canonical WeeklyPlan + Evidence Model

```text
Status: complete (read-only modeling)
Classification: documentation/status + read-only model code only
```

## Purpose

Phase 18A adds a canonical `WeeklyPlan` model that can become the sole
normalized input for future preview and publishing phases.

The finished system architecture is:

```text
teacher natural-language intent
→ current pacing/source resolution
→ canonical WeeklyPlan
→ teacher-readable preview
→ existing deployment manifest/publisher
→ full preflight → backup → apply → live verification
```

Phase 18A delivers only the canonical `WeeklyPlan` and its evidence model. It
does not change any Phase 14B/16/17 behavior, the deployment manifest, or the
publisher.

## Implementation note

Reused existing structures:

- course registry: `config/canvas-llm/approved-canvas-course-manifest.json`
  (subject names and roles; numeric IDs stay here, never inside the plan);
- week calendar: `config/curriculum/canvas/instructional-weeks-2026-2027.json`
  (used to construct the canonical example);
- protected-subject rule: `config/curriculum/canvas/quarter-subject-activation-2026-2027.json`;
- dataclass + camelCase `to_dict()` conventions from `scripts/canvas_llm_phase24/models.py`
  and `scripts/canvas_llm_phase26/models.py`;
- the source-precedence philosophy from `canonical-context-pack/canonical-source-matrix.md`;
- CLI/status conventions: `bin/chief-of-staff --canvas-llm-phase-18a-status`.

Genuinely missing (new in this phase): a clean, self-contained canonical
`WeeklyPlan` that is a normalized input — not the Phase 24 prediction output or
the Phase 26 workstation packet — with explicit evidence provenance, a six-level
source precedence, and three-way precedent classification.

## WeeklyPlan schema

```text
WeeklyPlan
  schema/version
  school_year, quarter, week_number, week_code
  monday_date, friday_date, timezone
  source_metadata, teacher_instructions, teacher_overrides
  courses: Reading/Spelling, Math, Language Arts, History, Science
    CoursePlan: course, days[5], requested_artifacts, protected, notes
      DayEntry: weekday, date, in_class, homework, raw, blank,
                decided_source, evidence[], ambiguity
  assessments_reminders, requested_artifacts, protected_courses
  unresolved_ambiguities, warnings, provenance
```

- `raw` preserves pacing/instruction values verbatim (unknown shorthand remains
  unchanged).
- `in_class` / `homework` hold the normalized student-facing interpretation
  where established; empty `homework` means "omit At Home".
- `blank` marks a day that must stay blank (never guessed).
- `decided_source` records which source class determined the normalized value.
- `evidence` carries provenance per material decision.

Design constraint: the plan must not embed permanent live Canvas configuration.
Numeric assignment-group IDs are never stored here as eternal truth; they are
referenced/resolved separately and verified during later preflight.

## Source precedence

Encoded in `source_precedence.py`, highest authority first:

```text
1. teacher_instruction   Current teacher instruction
2. live_pacing           Current live 2026-2027 FPK pacing guide, tab "4B - Reagan"
3. canonical_rule        Canonical operational/subject rules
4. live_canvas_config    Current verified Canvas configuration/registry
5. precedent             Approved Canvas precedent
6. historical_fallback   Historical examples/chats
```

Rules:

- never invent academic content;
- blank pacing cells remain blank;
- unknown curriculum shorthand remains unchanged unless an established rule
  defines it;
- precedent must never override current teacher instruction or current pacing;
- historical Canvas anomalies must not become templates automatically.

Validation enforces that a value `decided_source` is never lower-precedence than
any other evidence source present for that field.

## Precedent classification

Encoded in `precedent.py`. August 15 scout findings split into three categories:

```text
A. operational_behavior    canonical operational behavior (promotable to rules)
B. canvas_configuration    current Canvas configuration (registry, live-verified)
C. anomaly                 known anomalies / historical inconsistencies (never promotable)
```

Documented examples: seeded weekly pages updated in place, no-homework days omit
At Home, spelling displays in Reading while the gradebook assignment routes to
Language Arts, and Homeroom front-page updates (A); course IDs and
assignment-group IDs (B); RM4 Lesson 13 with Lesson 12 description, History
review assignments using test descriptions, trailing-space titles, and naming
transitions (C).

The catalog is static documentation/status proof only; the production planner
does not reread the August 15 evidence bundle on every run.

## Validation

`validation.py` enforces:

- required Monday-Friday week/date consistency (dates must fall on the named
  weekday; Friday is Monday + 4 days);
- known course names only;
- blank remains blank;
- unresolved ambiguity can be represented without guessing;
- invalid/contradictory plans fail validation;
- protected courses remain explicit;
- lower-precedence sources never override higher-precedence sources;
- anomalies never promote into deciding rules.

## Safety boundaries

Read-only. This phase performs zero Canvas writes (no POST/PUT/PATCH/DELETE),
makes no network calls, does not read or emit `CANVAS_TOKEN`, does not modify
live Canvas, and keeps all runtime/generated evidence under git-ignored
`.local/`. No generated Canvas evidence is committed.

## Files

```text
scripts/canvas_llm_phase18a/__init__.py
scripts/canvas_llm_phase18a/source_precedence.py
scripts/canvas_llm_phase18a/precedent.py
scripts/canvas_llm_phase18a/models.py
scripts/canvas_llm_phase18a/validation.py
scripts/canvas_llm_phase18a/examples.py
scripts/canvas_llm_phase18a/cli.py
scripts/canvas-llm-phase-18a-status.sh
tests/canvas-llm-phase-18a-canonical-weekly-plan-test.sh
```

## Status command

```bash
bin/chief-of-staff --canvas-llm-phase-18a-status
```

The command proves: the canonical WeeklyPlan model is present, validation
passes, the provenance/evidence model is present, precedent classification is
represented, no Canvas writes are required, and Phase 14B/16/17 regression
status still passes.
