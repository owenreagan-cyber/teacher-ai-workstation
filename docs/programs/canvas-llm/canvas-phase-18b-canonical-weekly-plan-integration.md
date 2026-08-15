# Canvas LLM Phase 18B — Canonical WeeklyPlan Integration

Status: implemented (read-only / preview-only)
Schema upstream: `canonical-weekly-plan`, version `1` (Phase 18A)

## Objective

Phase 18B creates the **canonical integration boundary** between the Phase 18A
canonical `WeeklyPlan` + evidence model and the existing Phase 22-27 planning,
prediction, and publishing stack. It makes `WeeklyPlan` the authoritative
normalized input contract for weekly instructional planning without forking the
downstream publisher or predictive pipeline.

```text
Source Evidence
      |
      v
Phase 18A  Canonical WeeklyPlan  (human/evidence-facing truth)
      |
      v
Phase 18B  Validated Adapter / Translation Layer   <-- this phase
      |
      v
Phase 22-27 Models + Publisher  (execution/prediction/publication)
```

## Architectural role

- `WeeklyPlan` is the canonical human/evidence-facing planning representation.
- Phase 22-27 models remain the downstream execution/prediction/publication
  representations. Phase 18B adapts to their **serialized contract shapes** and
  does not create competing model classes.
- The adapter is a pure, deterministic transformation. It performs no Canvas
  writes, no network calls, and no token access.

## Canonical authority

Downstream content is produced exclusively from validated canonical `WeeklyPlan`
data:

```text
canonical input -> derived downstream representation
```

Legacy fixtures remain for regression only; they are never co-equal production
planning truth. Teacher-decided canonical content (`teacher_instruction`) always
outranks prediction. A higher-precedence deciding source is never overwritten.

## Downstream integration point

The adapter emits three plain dicts in the exact shapes the pipeline consumes:

| Output | Compatible with | Downstream consumer |
| --- | --- | --- |
| `agenda` | `WeeklyAgendaPage.to_dict()` (Phase 22) | `WeeklyAgendaPublisher` page input |
| `prediction` | `WeekPrediction.to_dict()` (Phase 24) | `build_workstation_packet` Phase 24 packet |
| `subjects` | `SubjectSnapshot.to_dict()` (Phase 26) | workstation subject workspaces |

Each emitted item carries a provenance trace record linking it back to the
canonical source.

## Translation contract

- `translate_weekly_plan(plan)` accepts a validated `WeeklyPlan`; it reuses the
  Phase 18A `validate_plan` and **fails closed** (raises `ValueError`) on any
  validation error.
- Course display name maps to the Phase 26 subject key (`Math -> math`,
  `Reading/Spelling -> reading-spelling`, `Language Arts -> language-arts`,
  `History -> history`, `Science -> science`).
- `event_type` is derived only as `assessment` when the canonical text contains a
  known assessment marker (`test`, `assessment`, `checkout`, `quiz`), otherwise
  `lesson`. No lesson/assessment numbers are invented.
- `source_evidence` is populated from each `DayEntry`'s evidence records and the
  plan's top-level provenance.

## Precedence handling

- The Phase 18A six-level source hierarchy is passed through as
  `sourceHierarchy` (`teacher_instruction`, `live_pacing`, `canonical_rule`,
  `live_canvas_config`, `precedent`, `historical_fallback`).
- A `teacher_instruction` deciding source surfaces as `teacher_override` +
  `manual_override_state="teacher"` and `review_state="teacher_decided"`, so
  prediction cannot overwrite it.
- Invalid lower-precedence decisions are rejected by validation before
  translation.

## Evidence / provenance behavior

- Every emitted event carries `source_evidence` (source class, reference, note,
  owner-confirmed flag).
- Every day/course produces a `ProvenanceTrace` record with
  `canonical_plan_id`, `canonical_week_code`, `canonical_course`,
  `canonical_day`, `canonical_source`, and `canonical_reference`, making it
  possible to answer "why did this downstream action exist?"

## Blank handling

A blank `DayEntry` produces no downstream event and no agenda content. It is
recorded in `result.blanks` and a trace record (`downstream_kind="none"`).
Blank never becomes "No homework", "Continue lesson", "TBD", previous-day
content, or predicted activity.

## Ambiguity handling

An unresolved shorthand/ambiguity is never translated into invented concrete
content. It is recorded in `result.unresolved` and emitted as a review-only event
with empty titles, `review_state="needs_review"`, `requires_review=True`, and
`decision_layer="unresolved"`. No guessed activity is produced.

## Protected-course handling

A protected `CoursePlan` is recorded in `result.protected`, produces no
writable event and no agenda content, and yields a subject workspace with
`readinessState="Blocked"`, `approvalState="Blocked"`, and
`assignmentPolicy="disabled"`. Phase 18B does not introduce any authorization to
write a protected course.

## Precedent bundle behavior

Phase 18B adds an **optional, read-only** precedent-bundle loader at
`scripts/canvas_llm_phase18b/precedent_loader.py`.

- Bundle path: `.local/canvas/precedent/2026-08-15_operational-reconstruction/`
  (`precedent.json`, optional `PRECEDENT_REPORT.md`, `evidence/`).
- Absence is normal (not FAIL); the loader falls back to the static Phase 18A
  precedent catalog.
- The bundle is never modified and never required.
- A malformed bundle returns a controlled `malformed` diagnostic state and fails
  closed (no partial promotion).
- `anomaly` records are classified but never promoted.
- `canvas_configuration` records are classified and never hardcoded; Canvas
  configuration (course IDs, assignment group IDs, module/page IDs, URLs,
  publish flags) remains registry/live-config driven, not precedent.

## Zero-write boundary

Phase 18B contains no `canvas_writer` import, no `requests.post/put/patch/delete`,
no `urllib.request`, no `http.client`, no `CANVAS_TOKEN` reference, and no
`.local` operational write. It translates into downstream-compatible structures
and stops before execution. The adapter imports only Phase 18A modules and the
standard library; it never imports writer, connector, gate, or publisher
execution modules.

## Affected phases

- Phase 18A (upstream dependency) — unchanged, reused.
- Phase 22 (publisher), Phase 24 (`WeekPrediction`), Phase 26 (`WorkstationPacket`),
  Phase 27 (`DeployableObject`) — downstream contracts adapted to, not forked.
- Phase 18 write-gate readiness — preserved (`NEEDS_ONE_MORE_PREVIEW_REFINEMENT`),
  not forced open.

## Status command

```bash
bin/chief-of-staff --canvas-llm-phase-18b-status
```

## Regression expectations

- Phase 14b / 16 / 17 / 18 / 18A / 18B remain green.
- Downstream Phases 22-27 status remain green.
- `tests/smoke-chief-of-staff-cli.sh` remains green.
- `tests/canvas-llm-phase-18b-weekly-plan-integration-test.sh` passes all
  scenario tests (happy path, precedence, blanks, ambiguity, protected courses,
  anomaly blocking, provenance, precedent-bundle absence/malformed/valid,
  no-write path, round-trip).

## Future Phase 18C / publishing implications

Phase 18C (future) would wire the translated `agenda`/`prediction`/`subjects`
dicts into the existing `WeeklyAgendaPublisher` / `build_workstation_packet`
preparation paths without enabling writes. Phase 18B deliberately stops at the
boundary and does not schedule or execute publishing.
