# Canonical Context Pack 2026-2027

**Status:** Active planning authority for Context Pack phase (docs/status only)
**Status:** R1 (Initialization Fix) - COMPLETED
**Architecture Target:** Local-first, single-user, SQLite-backed workstation
**Runtime Scope:** No runtime behavior changes in this phase

## 1. Canonical source precedence

1. **APPROVED**: `config/curriculum/**` owner-approved 2026-2027 canonical JSON.
2. **APPROVED**: Validator-backed deterministic logic (`scripts/canvas_llm_phase22/validate_canonical_knowledge.py`, `scripts/canvas_llm_phase24/rule_engine.py`).
3. **APPROVED**: Owner doctrine docs (including Phase 21 calendar disruption doctrine).
4. **LIVE_READ_REQUIRED**: Current-year Canvas metadata (`assignment_groups`, modules, pages) via explicit read-only sync.
5. **LEGACY_EVIDENCE**: Prior implementations (`pacing-sync-pilot`, extracted `thales-academic-os*`) for historical reference only.
6. **OWNER_CONFIRMATION_REQUIRED**: Any unresolved date-level or policy ambiguity after source recovery.

## 2. Product vision (canonical)

- **APPROVED**: Single-user, local-first workstation with SQLite as durable source of truth.
- **APPROVED**: Deterministic rule execution for pacing/assignment/page structure.
- **APPROVED**: Human approval gate before publish/write workflows.
- **APPROVED**: No manual copy/paste dependency as the steady-state objective.
- **APPROVED**: Legacy Supabase/Firebase architecture is superseded for this product line.

## 3. Recovered weekly input schema

| Field | Type | Required | Rule / Source |
|---|---|---:|---|
| `weekCode` | `string` | Yes | Q/W token (ex: `Q1W5`) from `config/curriculum/canvas/instructional-weeks-2026-2027.json` |
| `date` | `string` (ISO) | Yes | Instructional sequence date |
| `weekday` | `Monday..Friday` | Yes | Weekday enum used across Phase 22/23/24 engines |
| `subject` | `math|reading|spelling|language-arts|history|science|homeroom` | Yes | Canonical subject IDs from course mapping and workstation schemas |
| `entry_type` | `lesson|assessment|test|study-guide|checkout|review` | Yes | Deterministic rule routing by type |
| `lessonNumber` | `number|null` | Conditional | Required when lesson-typed instruction is present |
| `assessmentNumber` | `number|null` | Conditional | Used for test family mapping |
| `in_class` | `string` | Yes | Agenda generation source |
| `at_home` | `string` | Yes | Friday constraints and assignment generation source |
| `resources` | `array<object|string>` | No | Resolved through resource engine and map keys |
| `manualOverride` | `object|null` | No | Explicit teacher correction/override signal |
| `reviewState` | `approved|needs_review|blocked` | No | Deterministic validation surface |

## 4. Recovered business rules and contracts

### 4.1 Subject logic and naming

- **APPROVED**: Reading and Spelling share one Canvas course in current-year mapping (`config/curriculum/canvas-course-mappings.json`).
- **APPROVED**: Together logic remains active conceptually (shared course; merged page/announcement workflows by policy).
- **APPROVED**: Math parity default (odd/even homework) with explicit teacher override.
- **APPROVED**: Deterministic prefix families (`SM5`, `RM4`, `SPELL`, `ELA4`) from current mapping.

### 4.2 Friday constraints

- **APPROVED**: Friday instruction allowed.
- **APPROVED**: Standard Friday homework defaults off; non-test At Home suppressed by rule.
- **APPROVED**: Tests remain allowed under Friday policy.
- **Source evidence**:
  - `docs/programs/canvas-llm/phase-22-predictive-weekly-planning-workstation/canonical-owner-rules.md`
  - `pacing-sync-pilot-8c50be47/src/lib/friday-rules.ts` (legacy implementation evidence)

### 4.3 Snow-day/calendar-disruption contract

**Status: APPROVED canonical behavior for Context Pack**

Source citations:
- `docs/programs/canvas-llm/phase-21-codex-autonomous-sandbox-learning-agent/calendar-disruption-doctrine.md`
- `docs/programs/canvas-llm/current-handoff.md`
- `scripts/canvas_llm_phase24/rule_engine.py` (Monday test displacement assertions)

Contract:
1. Unexpected closure creates a `calendar_disruption` event; closed date is non-instructional.
2. Closed day shows `In Class: Snow Day`; At Home/Homework removed.
3. Missed lesson moves to next valid instructional day; downstream sequence cascades by instructional-day order.
4. No silent lesson drops; no automatic conversion of missed lesson into homework.
5. Recompute affected assignments, agenda rows, resources, Study Guides, due dates, reminders, announcements.
6. Affected generated/approved artifacts become stale and require regeneration/review.
7. Keep original and revised schedules in audit history; mistaken closure is reversible.
8. Tests may not land on Monday after cascade; shift to Tuesday and adjust sequence coherently.
9. Study Guide timing recalculates from prior valid instructional day.
10. Changed assessment date requires regenerated parent/student communication.
11. Revised content stays blocked from publish until renewed owner approval.

Classification tags:
- `calendar_disruption`
- `snow_day_protocol`
- `requires_preview`
- `requires_owner_approval_before_canvas_write`

### 4.4 Announcement scheduling contract

**Status: APPROVED canonical scheduling logic**

Rule:
- Post on the **last instructional day before the upcoming instructional week** at configured preferred time.
- If Friday instructional, post Friday.
- If Friday not instructional, post previous instructional day.
- Monday holiday alone does not force Thursday posting.
- Resolve multi-day closures to latest valid instructional day before week start.
- No fixed calendar-day offset logic.

Posting time:
- `4:00 PM America/New_York` is retained as **LEGACY_APPROVED_BEHAVIOR / DEFAULT_PENDING_CURRENT_CONFIRMATION**.
- Final production posting time remains configurable.

### 4.5 Assignment-group resolution contract

**Status: APPROVED**

- **APPROVED**: Logical assignment-group names are canonical in committed config.
- **LIVE_READ_REQUIRED**: Current numeric Canvas assignment-group IDs must come from explicit read-only metadata sync.
- **APPROVED**: No auto-sync on startup; startup may warn stale metadata.
- **APPROVED**: Publishing blocked when required group is unresolved/stale/ambiguous.
- **PROHIBITED**: Placeholder IDs, guessed IDs, or promoted legacy numeric IDs.

Proposed cache schema (`assignment_group_cache`):

| Column | Type | Notes |
|---|---|---|
| `logical_name` | TEXT | Canonical internal route key |
| `canvas_name` | TEXT | Exact Canvas group name |
| `canvas_group_id` | INTEGER NULL | Resolved numeric ID |
| `course_id` | INTEGER | Course scope |
| `school_year` | TEXT | ex: `2026-2027` |
| `fetched_at` | TEXT | ISO timestamp |
| `source` | TEXT | `live_canvas_metadata` |
| `is_stale` | INTEGER | 0/1 |
| `is_ambiguous` | INTEGER | 0/1 |
| `ambiguity_note` | TEXT NULL | Explanation |

Command/UI action:
- `sync_canvas_metadata` (explicit teacher-triggered read-only pull)

### 4.6 Spelling source authority

**Status: APPROVED**

Active canonical source:
- `config/curriculum/spelling/cumulative-test-word-lists.json`

Validator-backed requirements:
- 24 tests (1-24)
- 25 words per test
- 5 focus words per test
- order and spelling preserved
- Test 24 focus words at positions 21-25

Source evidence:
- `scripts/canvas_llm_phase22/validate_canonical_knowledge.py`

Policy:
- Runtime and validators consume only canonical JSON.
- Other copies remain as **LEGACY_EVIDENCE** / **SUPERSEDED** (not active inputs).
- Canonical edits require explicit owner-approved curriculum update + validation + comparison report.

## 5. Canvas payload contracts (recovered)

### 5.1 Assignment payload (Canvas API shape)

Endpoint: `POST /api/v1/courses/{course_id}/assignments`
Recovered shape:

```json
{
  "assignment": {
    "name": "SM5: Test 18",
    "description": "<p>...</p>",
    "points_possible": 100,
    "grading_type": "points",
    "published": true,
    "assignment_group_id": 12345,
    "due_at": "2026-08-25T03:59:00.000Z",
    "omit_from_final_grade": false
  }
}
```

### 5.2 Agenda page payload (Canvas wiki page)

Endpoint: `PUT /api/v1/courses/{course_id}/pages/{page_url}`
Recovered shape:

```json
{
  "wiki_page": {
    "title": "Q1W5 - August 17-21, 2026",
    "body": "<div id=\"kl_wrapper_3\">...</div>",
    "published": false
  }
}
```

## 6. Canonical maps recovered

- **APPROVED**: Course and prefix map: `config/curriculum/canvas-course-mappings.json`
- **APPROVED**: Instructional week scaffold: `config/curriculum/canvas/instructional-weeks-2026-2027.json`
- **APPROVED**: Agenda structural rules: `config/curriculum/canvas/weekly-agenda-standard-2026-2027.json`
- **APPROVED**: Math map sources:
  - `config/curriculum/math/saxon-math-5/lesson-power-up-map.json`
  - `config/curriculum/math/saxon-math-5/fact-test-practice-map.json`
- **APPROVED**: Reading maps:
  - `config/curriculum/reading/reading-mastery-4/comprehension-location-map.json`
  - `config/curriculum/reading/reading-mastery-4/checkout-passage-map.json`
- **APPROVED**: Spelling canonical list:
  - `config/curriculum/spelling/cumulative-test-word-lists.json`

## 7. Calendar gap classification artifact

Detailed day-by-day classification for scaffold gaps is recorded in:

- `docs/master-plan/calendar-gap-date-classification-2026-2027.md`

This includes per-date source citations and excludes weekends from unresolved owner questions.

## 8. Legacy evidence and extraction locations

Extracted local reference repos (read-only evidence only):

- `.local/reference-apps/thales-academic-os/`
- `.local/reference-apps/thales-academic-os-v2/`

Classification:
- **LEGACY_EVIDENCE** only (UX/workflow/business-rule archaeology).
- Not current-year canonical authority.

## 9. Known conflicts recovered

### 9.1 Spelling source conflict (legacy vs canonical)

Canonical vs legacy map differences (same diffs in two legacy files):
- Test 14 word 12: `I` vs `Il`
- Test 15 word 16: `Defeated` vs `Delighted`
- Test 16 word 18: `I` vs `Il`

### 9.2 Assignment group naming divergence

Different legacy surfaces use variant labels (`Check Out` vs `Check Outs`, `Assessments` vs `Reading Assessments`), so names are canonicalized logically and numeric IDs remain `LIVE_READ_REQUIRED`.

## 10. Remaining unresolved items

- **OWNER_CONFIRMATION_REQUIRED**: Unresolved 2026-2027 weekday statuses listed in `calendar-gap-date-classification-2026-2027.md`.
- **LIVE_READ_REQUIRED**: Current-year numeric assignment-group IDs from read-only Canvas metadata sync.
- **DEFAULT_PENDING_CURRENT_CONFIRMATION**: Preferred announcement post time (4:00 PM ET retained as legacy-approved default).
