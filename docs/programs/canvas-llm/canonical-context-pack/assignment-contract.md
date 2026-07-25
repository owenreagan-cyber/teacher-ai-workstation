# Canonical Canvas Assignment Contract

## Purpose

This contract separates four concerns:

1. teacher planning input;
2. generated assignment intent;
3. Canvas REST assignment fields;
4. internal safety, comparison, approval, and deployment metadata.

Highest authority:

```text
docs/programs/canvas-llm/2026-2027-fpk-canvas-operating-contract.md
```

An assignment is not publishable merely because a payload can be rendered.

Generator alignment is scheduled for C0L and later phases.

## Assignment lifecycle

```text
weekly planning entry
→ normalized assignment intent
→ generated draft
→ validation
→ Canvas comparison
→ dependency resolution
→ teacher review
→ revision-bound approval
→ controlled publish
→ read-back verification
→ ledger record
```

Historical note: an earlier lifecycle included resource resolution as a required step. Phase 25 resource resolution is de-scoped and dormant for the active workflow.

## Internal assignment identity

| Field | Type | Required | Source | Notes |
|---|---:|---:|---|---|
| `local_object_id` | string | yes | derived | Stable idempotent local identity |
| `week_code` | string | yes | weekly model | Example: `Q1W1` |
| `school_year` | string | yes | calendar | Current production: `2026-2027` |
| `subject` | string | yes | weekly model | Canonical subject key |
| `entry_id` | string | yes | weekly model | Source daily-entry reference |
| `assignment_family_id` | string | conditional | derived | Links written and fact assessments, etc. |
| `assignment_type` | enum | yes | derived or teacher-confirmed | Determines rules and routing |
| `source_revision` | integer | yes | weekly model | Revision used to generate draft |
| `content_hash` | string | yes | canonical payload | Used for comparison and idempotency |

## Teacher-facing assignment controls

| Internal field | UI label | Type | Required | Default | Notes |
|---|---|---:|---:|---|---|
| `assignment_intent` | Create Assignment | enum | yes | derived | create / do not create / review / blocked |
| `title_override` | Assignment Title | string | no | canonical title | Explicit override must be preserved |
| `description_override` | Assignment Description | rich text | no | generated | Must remain sanitizable |
| `points_override` | Points | number | no | 100 | All assignments are 100 points |
| `due_date_override` | Due Date | ISO date | no | instructional rule | Same calendar day as assignment |
| `due_time_override` | Due Time | local time | no | 11:59 PM America/New_York | Approved operating-contract default |
| `module_intent` | Add to Module | enum | yes | derived | add / do not add / review |
| `publish_intent` | Publish State | enum | yes | draft | Draft intent is not approval |
| `notes` | Teacher Notes | text | no | empty | Local only unless explicitly included |

## Canonical assignment types

```text
math_lesson_homework
math_written_assessment
math_fact_assessment
reading_workbook_comprehension
reading_mastery_test
reading_fluency_checkout
spelling_test
language_arts_accuracy
language_arts_assessment
language_arts_writing_final
history_assessment
science_assessment
custom
```

Historical types such as `math_study_guide`, `math_investigation`, and `reading_checkout` remain dormant evidence where superseded by operating-contract naming.

History and Science assignment types are active only during their approved quarters per `quarter-subject-activation-2026-2027.json`.

## Canonical title examples

```text
SM5: Written Assessment 7
SM5: Fact Assessment 7
SM5: Lesson 18 Homework
ELA4: Persuasive Writing Final Draft
RM4: Mastery Test 4
RM4: Fluency Checkout 4
RM4: Spelling Test 1
HIST4: Ancient Rome Assessment
SCI4: Life Cycles Assessment
```

Exact formatting is governed by `naming-conventions.md`.

## Canvas routing fields

| Internal field | Canvas meaning | Required before publish | Resolution |
|---|---|---:|---|
| `course_id` | Target Canvas course | yes | current course mapping |
| `course_ref` | Logical subject/course reference | yes | committed config |
| `assignment_group_id` | Numeric Canvas assignment-group ID | yes where required | teacher-initiated read-only metadata sync |
| `assignment_group_name` | Logical/current Canvas group name | yes | canonical routing contract |
| `module_id` | Numeric Canvas module ID | conditional | read-only metadata sync |
| `module_name` | Logical module name | conditional | canonical module contract |
| `module_position` | Deterministic module position | conditional | module-placement engine |

Numeric IDs must never be guessed, copied from archived years, or replaced with placeholder values.

## Canvas REST assignment payload

Minimum supported structure:

```json
{
  "assignment": {
    "name": "SM5: Lesson 18 Homework",
    "description": "<p>...</p>",
    "assignment_group_id": 12345,
    "points_possible": 100,
    "grading_type": "percent",
    "submission_types": ["none"],
    "due_at": "2026-07-20T23:59:00-04:00",
    "unlock_at": null,
    "lock_at": null,
    "published": false,
    "allowed_attempts": -1,
    "omit_from_final_grade": false
  }
}
```

Numeric IDs, points, due times, and submission settings must come from approved current configuration.

## Description HTML contract

Generated assignment HTML may include concise assignment instructions and teacher-approved supplemental wording.

It must not include invented links, teacher-only files, secure assessment answers, raw local file paths, student data, study-guide links, curriculum-resource links, or unresolved placeholders presented as real content.

Historical note: earlier contracts allowed verified resource links and study-guide links in assignment descriptions. That behavior is superseded and non-authoritative.

## Comparison states

Canonical Phase 27 comparison states:

```text
NEW
UPDATE
NO_CHANGE
CONFLICT
BLOCKED
OMIT
DELETE_CANDIDATE
```

## Publish blockers

Publishing must be blocked for:

- missing current course mapping;
- archived or read-only course;
- unresolved assignment group;
- inactive quarter subject;
- invalid due date or due time;
- prohibited subject/type combination;
- unresolved Canvas conflict;
- stale source revision;
- stale Canvas snapshot;
- missing approval;
- failed dependency;
- invalid payload;
- missing idempotency identity.

Resource resolution is not a current publication blocker.

## Approval contract

Approval must bind to local object ID, source revision, content hash, manifest revision, snapshot ID, approved_by, and approved_at.

An edit after approval invalidates that approval.

## Deployment contract

Publishing must pass validation, use current metadata, pass comparison, satisfy dependencies, have valid revision-bound approval, use the Phase 27 transport boundary, write through the ledger, and verify by read-back.

Export is not publish.

Teacher approval remains required before any future publication action.

canvasWritesAllowed remains false in current runtime posture.
