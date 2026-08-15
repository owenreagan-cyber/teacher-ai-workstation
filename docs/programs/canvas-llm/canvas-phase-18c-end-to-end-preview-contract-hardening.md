# Canvas LLM Phase 18C — Canonical WeeklyPlan End-to-End Preview Assembly & Downstream Contract Hardening

## Purpose

Phase 18C takes the Phase 18A canonical `WeeklyPlan` and Phase 18B translation
layer all the way through the existing read-only downstream preparation pipeline
into a deterministic, auditable **Teacher Preview**. It also hardens the
downstream model boundary so the translation layer no longer hand-authors
fragile serialized dict shapes that can silently drift from the real models.

The canonical plan remains the single source of truth. No downstream stage may
invent or overwrite canonical instructional decisions. Phase 18C is strictly
read-only / preview-only: no Canvas writes, no mutation, no token use.

## End-to-End Pipeline

```text
Evidence / Rules
        ↓
Canonical WeeklyPlan            (Phase 18A, scripts/canvas_llm_phase18a)
        ↓
Validated Translation           (Phase 18B, scripts/canvas_llm_phase18b)
        ↓
Pure Shared Contracts           (phase22/phase24/phase26 contracts.py)
        ↓
Preparation (agenda / prediction / workstation)
        ↓
Read-only Teacher Preview       (Phase 18C, scripts/canvas_llm_phase18c)
```

```text
assemble_teacher_preview(weekly_plan, runtime_context)
  1. validate canonical plan            (fail closed)
  2. translate through Phase 18B        (builds shared contracts)
  3. detect downstream-key collisions   (fail closed)
  4. detect missing Canvas config       (block, never guess)
  5. propagate unresolved owner policy  (due-time convention)
  6. run canonical-vs-downstream drift  (fail closed on semantic drift)
  7. evaluate readiness                 (deterministic)
  8. return deterministic TeacherPreview
```

## Contract Split

Downstream models were already pure (`dataclasses` only); the coupling came from
package `__init__.py` files that re-exported execution modules. Phase 18C
introduces explicit, import-safe contract modules and cleans package roots:

| Package | Contract module | Exports |
| --- | --- | --- |
| `scripts/canvas_llm_phase22` | `contracts.py` | `WeeklyAgendaPage` |
| `scripts/canvas_llm_phase24` | `contracts.py` | `WeekPrediction`, `PredictedInstructionalEvent`, `Confidence`, `SourceEvidence`, `TeacherOverride`, `UnresolvedDecision`, … |
| `scripts/canvas_llm_phase26` | `contracts.py` | `WorkstationPacket`, `SubjectSnapshot`, `WeekSelection`, `ManifestOperation`, `compact`, `stable_id` |
| `scripts/canvas_llm_phase18c` | `contracts.py` | `TeacherPreview`, `RuntimeContext`, `ReadinessState`, `Derivation`, `DriftReport` |

The Phase 18B `translation.py` now builds these contracts directly and
serializes via each contract's `to_dict()`, eliminating hand-authored downstream
shapes. The Phase 22 `WeeklyAgendaPage` was moved out of `weekly_agenda_publisher.py`
(which imports the Canvas connector/writer) into the pure `contracts.py`.

## Safe Import Boundaries

`contracts.py` files import only the Python standard library and sibling pure
models. Importing them (or the package roots) must not transitively import
Canvas execution code (`canvas_connector`, `canvas_writer`, `canvas_verification`,
`phase22_workstation`, `rule_engine`, `pipeline`).

```python
from scripts.canvas_llm_phase24.contracts import WeekPrediction
from scripts.canvas_llm_phase26.contracts import WorkstationPacket, SubjectSnapshot
from scripts.canvas_llm_phase22.contracts import WeeklyAgendaPage
```

Package `__init__.py` files now re-export only pure contracts. Execution
entrypoints (`predict_week.py`, `phase26_workstation.py`, etc.) are imported
explicitly when execution is required. Tests assert `sys.modules` contains no
execution modules after importing contracts.

## Teacher Preview

`TeacherPreview` is a deterministic, read-only, human-review representation. It
is **not** a write-ready Canvas payload.

```text
TeacherPreview
  week_code, monday_date, friday_date, timezone, week_title
  courses[]        per-course/day content + source + evidence + status + derivation
  days[]           Mon–Fri aggregated per-course view
  agenda           WeeklyAgendaPage (display labels)
  prediction       WeekPrediction (advisory)
  workstation      subject snapshots (SubjectSnapshot)
  unresolved[]     canonical ambiguity records
  protected[]      write-blocked courses
  missing_config[] missing live Canvas configuration diagnostics
  unresolved_policy[]  owner-unresolved policy (due-time convention)
  warnings[]       combined warnings
  blocked_reasons[]  human-readable blockers
  readiness        overall readiness state
  provenance[]     trace to canonical source
  drift{}          canonical-vs-downstream drift report
```

Each `PreviewDay` carries a machine-readable `derivation` classification:
`canonical`, `derived`, `configured`, `predicted`, `unresolved`, `blank`, or
`protected`.

## Canonical Authority

`WeeklyPlan` remains authoritative. `WeekPrediction`, `SubjectSnapshot`, legacy
fixtures, historical precedent, publisher defaults, and Canvas configuration are
never alternate canonical truth. Prediction is advisory only and never outranks
teacher instruction, live pacing, canonical rules, or live Canvas config.

## Prediction Role

Prediction never converts `unresolved` into canonical fact. Unresolved content
stays unresolved with the prediction attached separately as advisory data marked
`decision_layer == "unresolved"` and `requires_review == True`.

## Readiness States

```text
READY_FOR_REVIEW
ADVISORY_ONLY
BLOCKED_UNRESOLVED
BLOCKED_PROTECTED
BLOCKED_MISSING_CONFIG
BLOCKED_POLICY
```

Readiness never implies publish readiness. Evaluation order (first match wins):

1. missing Canvas config → `BLOCKED_MISSING_CONFIG`
2. owner policy unresolved (due-time) → `BLOCKED_POLICY`
3. canonical content unresolved → `BLOCKED_UNRESOLVED`
4. protected course present → `BLOCKED_PROTECTED`
5. only advisory content → `ADVISORY_ONLY`
6. otherwise → `READY_FOR_REVIEW`

## Drift Detection

`detect_drift(plan, translation)` fails closed on semantic drift:

- each eligible canonical course/day maps downstream exactly once
- no unexpected downstream course/day appears (cross-course leakage)
- canonical text is not replaced
- teacher-decided state remains teacher-decided
- blank stays blank; unresolved stays unresolved; protected stays protected
- provenance remains traceable
- no fabricated identifiers; no unauthorized defaults
- week code / Monday / Friday date identity does not drift

`invalid_drift` entries block acceptance; `ok == False` whenever any exist.

## Missing Config Behavior

For a non-protected course that requests artifacts, the following live/registry
fields are required (keyed by downstream subject key):

| Artifact | Required config |
| --- | --- |
| `page` | `course_id`, `module_id` |
| `assignment` | `course_id`, `assignment_group_id` |
| `announcement` | `course_id` |
| `newsletter-front-page` | `course_id` |

Missing any required field → `BLOCKED_MISSING_CONFIG`. IDs are never guessed,
never reused from precedent, and never derived heuristically.

## Due-Time Unresolved Behavior

The Canvas assignment due-time convention remains **owner-unresolved**. Phase 18C
does not invent a due time (no midnight, no class start, no end-of-day, no copied
prior week). The unresolved policy is:

1. carried by `RuntimeContext.due_time_policy` (default `"unresolved"`)
2. surfaced in `unresolved_policy`, `warnings`, and `blocked_reasons`
3. mapped to `BLOCKED_POLICY` readiness (when no harder blocker exists)

Phase 24 no longer strips the "Canvas assignment due-time convention remains
owner-unresolved" warning (previously causing a Phase 26 propagation failure);
Phase 24 validation now treats it as a WARN, and Phase 26 readiness computes
`dueTimeBlocker` from the Phase 24 advisory warnings. The policy decision itself
remains with the owner.

## Failure-Mode Handling

| # | Failure mode | Handling |
| --- | --- | --- |
| 1 | Downstream defaults into canonical blank | Blank is first-class; no "No Homework"/"TBD" injected |
| 2 | Publisher injects title/lesson number | Titles are `display_label`; canonical content not rewritten |
| 3 | Prediction fills unresolved field | Prediction advisory only; unresolved preserved |
| 4 | Protected course becomes writable | Protected stays `assignmentPolicy=disabled`, `Blocked` |
| 5 | Two entries map to same downstream key | Collision detection fails closed |
| 6 | Downstream schema drift | Shared contracts + schema compatibility tests |
| 7 | Missing config → guessed IDs | `BLOCKED_MISSING_CONFIG`; never guess |
| 8 | Due-time manufactured | Unresolved policy propagated; no due time invented |
| 9 | Duplicate action generation | Deterministic, idempotent assembly |

## Zero-Write Proof

- no `POST`/`PUT`/`PATCH`/`DELETE`
- no `requests.*`, `urllib.request`, `http.client`
- no `canvas_writer` / `canvas_connector` import
- no `CANVAS_TOKEN` reference
- `sys.modules` inspection asserts write modules are never loaded during assembly

## Future Write-Gate Implications

`TeacherPreview` is the last read-only checkpoint before any future controlled
write phase. `BLOCKED_MISSING_CONFIG`, `BLOCKED_POLICY`, and `BLOCKED_UNRESOLVED`
define the exact conditions that must be cleared before write enablement can be
considered. The drift report is the canonical-vs-downstream audit surface for
Phase 19 / write-gate review.

## Migration Notes

Prefer:

```python
from scripts.canvas_llm_phase24.contracts import WeekPrediction
from scripts.canvas_llm_phase26.contracts import WorkstationPacket, SubjectSnapshot
from scripts.canvas_llm_phase22.contracts import WeeklyAgendaPage
```

over execution-heavy package imports. Package `__init__.py` files remain
backward-compatible for pure model access (`from scripts.canvas_llm_phase24 import WeekPrediction`
still works) but no longer transitively load execution modules.

## Status Command

```bash
bin/chief-of-staff --canvas-llm-phase-18c-status
```

See also `scripts/canvas-llm-phase-18c-status.sh` and the adversarial test suite
`tests/canvas-llm-phase-18c-preview-assembly-test.sh`.
