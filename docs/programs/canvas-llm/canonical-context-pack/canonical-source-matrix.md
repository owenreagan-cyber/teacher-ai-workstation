# Canonical Source Matrix

## Purpose

This matrix identifies the authoritative source for each Canvas LLM rule, map, contract, and configuration domain.

Highest authority:

```text
docs/programs/canvas-llm/2026-2027-fpk-canvas-operating-contract.md
```

Legacy applications may provide implementation ideas or historical evidence, but they must not silently override current Teacher AI Workstation sources or current owner-approved 2026–2027 decisions.

## Status vocabulary

- `APPROVED` — current authoritative source with no known open fields
- `APPROVED_WITH_OPEN_FIELDS` — authoritative source, but some runtime metadata remains unresolved
- `OWNER_DECISION_REQUIRED` — owner input is still required
- `LIVE_READ_REQUIRED` — current Canvas metadata must be fetched through an approved read-only action
- `LEGACY_EVIDENCE` — useful historical behavior, but not current authority
- `SUPERSEDED` — retained for history but not active
- `PROHIBITED` — must not be used as current behavior
- `DORMANT` — historical implementation retained; not a current workflow dependency

## Source precedence

1. `docs/programs/canvas-llm/2026-2027-fpk-canvas-operating-contract.md`
2. Current canonical configuration under `config/curriculum/`
3. Current validator-backed deterministic rule engines
4. Current owner-approved doctrine and contract documents in this context pack
5. Current read-only Canvas metadata
6. Validated historical Canvas behavior
7. Legacy application evidence
8. Fixtures and prototype behavior

## Canonical sources

| Domain | Status | Authoritative source | Validator or consumer | Notes |
|---|---|---|---|---|
| Operating contract | APPROVED | `docs/programs/canvas-llm/2026-2027-fpk-canvas-operating-contract.md` | Context pack and canonical knowledge validators | Highest explicit authority |
| Product architecture | APPROVED | `docs/programs/canvas-llm/canonical-context-pack/product-and-architecture-rules.md` | Context-pack validator | Single-user, local-first Teacher AI Workstation |
| Canvas course routing | APPROVED_WITH_OPEN_FIELDS | `config/curriculum/canvas-course-mappings.json` | `scripts/canvas_llm_phase22/validate_canonical_knowledge.py` | Numeric assignment-group and module IDs remain live-read metadata |
| Quarter-subject activation | APPROVED | `config/curriculum/canvas/quarter-subject-activation-2026-2027.json` | `scripts/canvas_llm_phase22/validate_canonical_knowledge.py` | History Q1/Q3; Science Q2/Q4; inactive subject untouched |
| Agenda page rules | APPROVED | `config/curriculum/canvas/agenda-page-rules.json` | Phase 22/23 validators and generators | Reminders only; Homework label; no Resources section |
| 2026–2027 instructional weeks | APPROVED | `config/curriculum/canvas/instructional-weeks-2026-2027.json` | `scripts/canvas_llm_phase22/phase22_workstation.py` | Week codes, titles, and date ranges |
| Weekly agenda standard | APPROVED | `config/curriculum/canvas/weekly-agenda-standard-2026-2027.json` | Agenda contract validator | Current page anatomy and weekday structure |
| Math lesson to Power Up map | APPROVED | `config/curriculum/math/saxon-math-5/lesson-power-up-map.json` | `scripts/canvas_llm_phase22/validate_canonical_knowledge.py` | Expected coverage: Lessons 1–120 |
| Math Fact Test practice map | APPROVED | `config/curriculum/math/saxon-math-5/fact-test-practice-map.json` | `scripts/canvas_llm_phase22/validate_canonical_knowledge.py` | Expected coverage: Fact Tests 1–23 |
| Reading comprehension locations | APPROVED | `config/curriculum/reading/reading-mastery-4/comprehension-location-map.json` | `scripts/canvas_llm_phase22/validate_canonical_knowledge.py` | Expected coverage: Lessons 1–140 |
| Reading Checkout passages | APPROVED | `config/curriculum/reading/reading-mastery-4/checkout-passage-map.json` | `scripts/canvas_llm_phase22/validate_canonical_knowledge.py` | Checkouts 1–13 only; Reading Test 14 has no Checkout |
| Spelling cumulative lists | APPROVED_WITH_OPEN_FIELDS | `config/curriculum/spelling/cumulative-test-word-lists.json` | `scripts/canvas_llm_phase22/validate_canonical_knowledge.py` | Tests 1–24; owner-provided Test 25 still requires reconciliation |
| Calendar-disruption doctrine | APPROVED | `docs/programs/canvas-llm/phase-21-codex-autonomous-sandbox-learning-agent/calendar-disruption-doctrine.md` | `scripts/canvas_llm_phase24/rule_engine.py` | Snow-day cascade, stale-artifact invalidation, no Monday tests |
| Current-week selection | APPROVED | `scripts/canvas_llm_phase22/phase22_workstation.py` | Phase 22 tests/status | Must use instructional calendar, not fixed offsets |
| Prediction and correction precedence | APPROVED | `scripts/canvas_llm_phase24/rule_engine.py` and `scripts/canvas_llm_phase24/correction_memory.py` | `scripts/canvas_llm_phase24/validate_prediction.py` | Explicit correction outranks prediction; hard rules remain authoritative |
| Phase 25 resource resolution | DORMANT | `scripts/canvas_llm_phase25/` | Historical validators only | De-scoped from active Canvas LLM workflow; code retained as evidence |
| Weekly workstation storage | APPROVED_WITH_OPEN_FIELDS | `scripts/canvas_llm_phase26/storage.py` | `scripts/canvas_llm_phase26/validate_phase26_state.py` | Current storage exists; real editable weekly content model still requires recovery work |
| Revision and approval model | APPROVED | `scripts/canvas_llm_phase26/revisions.py` and `scripts/canvas_llm_phase26/approval.py` | Phase 26 validator | Editing invalidates relevant approval |
| Canvas comparison states | APPROVED | `scripts/canvas_llm_phase27/comparison.py` and `scripts/canvas_llm_phase27/safety_diff.py` | `scripts/canvas_llm_phase27/validate_phase27.py` | NEW, UPDATE, NO_CHANGE, CONFLICT, BLOCKED, OMIT, DELETE_CANDIDATE |
| Dependency graph | APPROVED | `scripts/canvas_llm_phase27/dependency_graph.py` | Phase 27 validator | Failed dependencies block downstream operations |
| Approval gate | APPROVED | `scripts/canvas_llm_phase27/approval_gate.py` | Phase 27 validator | Approval must bind to current revision and snapshot |
| Deployment ledger | APPROVED | `scripts/canvas_llm_phase27/ledger.py` | Phase 27 health checks | SQLite integrity, quarantine, and deployment history |
| Canvas transport boundary | APPROVED | `scripts/canvas_llm_phase27/transport.py` | Phase 27 validator | No uncontrolled parallel deploy service |
| Assignment due time | APPROVED | Operating contract §10 | Assignment and approval contracts | Same calendar day at 11:59 PM America/New_York |
| Assessment announcement timing | APPROVED | Operating contract §7 | Announcement contract | Prepared for Friday 4:00 PM America/New_York |
| Homeroom newsletter cadence | APPROVED | Operating contract §12 | `newsletter-homeroom-contract.md` | Monthly, not weekly |
| Canvas assignment-group IDs | LIVE_READ_REQUIRED | Current Canvas metadata | Future `sync_canvas_metadata` action | Do not hardcode, guess, or reuse archived-year IDs |
| Current module IDs | LIVE_READ_REQUIRED | Current Canvas metadata | Future metadata validator | Resolve by approved read-only sync |
| Historical and reference apps | LEGACY_EVIDENCE | `.local/reference-apps/` and separate legacy repositories | `legacy-app-comparison-oracle.md` | Read-only comparison sources only |
| Phase 23 synthetic fixture | PROHIBITED | `fixtures/canvas-llm/phase-23/synthetic-weekly-content.json` | Test-only use | Must not remain the production weekly content source |
| Rejected Phase 27B frontend experiment | SUPERSEDED | Local stash and ignored recovery patch | None | Preserved for evidence; not approved frontend |

## Required future review fields

Every source added to this matrix must record:

- domain;
- authoritative path;
- status;
- schema;
- coverage;
- validator;
- current consumer;
- legacy alternatives;
- known conflicts;
- owner decisions;
- last reviewed date.
