# Canonical Canvas Assignment Contract

## Purpose

This contract separates four concerns:

1. teacher planning input;
2. generated assignment intent;
3. Canvas REST assignment fields;
4. internal safety, comparison, approval, and deployment metadata.

An assignment is not publishable merely because a payload can be rendered.

## Assignment lifecycle

```text
weekly planning entry
→ normalized assignment intent
→ resource resolution
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

## Internal assignment identity

| Field | Type | Required | Source | Notes |
|---|---:|---:|---|---|
| `local_object_id` | string | yes | derived | Stable idempotent local identity |
| `week_code` | string | yes | weekly model | Example: `Q1W1` |
| `school_year` | string | yes | calendar | Current production: `2026-2027` |
| `subject` | string | yes | weekly model | Canonical subject key |
| `entry_id` | string | yes | weekly model | Source daily-entry reference |
| `assignment_family_id` | string | conditional | derived | Links written test, Fact Test, Study Guide, etc. |
| `assignment_type` | enum | yes | derived or teacher-confirmed | Determines rules and routing |
| `source_revision` | integer | yes | weekly model | Revision used to generate draft |
| `content_hash` | string | yes | canonical payload | Used for comparison and idempotency |

## Teacher-facing assignment controls

| Internal field | UI label | Type | Required | Default | Notes |
|---|---|---:|---:|---|---|
| `assignment_intent` | Create Assignment | enum | yes | derived | create / do not create / review / blocked |
| `title_override` | Assignment Title | string | no | canonical title | Explicit override must be preserved |
| `description_override` | Assignment Description | rich text | no | generated | Must remain sanitizable |
| `points_override` | Points | number | no | type default | Missing canonical default may block publish |
| `due_date_override` | Due Date | ISO date | no | instructional rule | Must remain on valid instructional date |
| `due_time_override` | Due Time | local time | no | unresolved/config | Must not be guessed |
| `resource_selections` | Resources | resource refs | no | resolved defaults | Only verified student-safe resources |
| `module_intent` | Add to Module | enum | yes | derived | add / do not add / review |
| `publish_intent` | Publish State | enum | yes | draft | Draft intent is not approval |
| `notes` | Teacher Notes | text | no | empty | Local only unless explicitly included |

## Canonical assignment types

```text
math_lesson_homework
math_written_test
math_fact_test
math_study_guide
math_investigation
reading_workbook_comprehension
reading_test
reading_checkout
spelling_test
language_arts_classroom_practice
language_arts_test
history_assessment
science_assessment
custom
```

History and Science assignment types remain blocked by default unless an explicit current rule enables them.

## Canonical title examples

```text
SM5: Math Test 1
SM5: Fact Test 1
SM5: Lesson 1 Odds
ELA4: Classroom Practice 4
RM4: Lesson 4 Workbook and Comprehension
RM4: Spelling Test 1
HIST4: American Revolution Test
HIST4: American Revolution Chapter 1 Vocab
SCI4: Structures and Functions Chapter 1 Test
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

The machine-readable Canvas payload uses Canvas-compatible names.

Minimum supported structure:

```json
{
  "assignment": {
    "name": "SM5: Lesson 1 Odds",
    "description": "<p>...</p>",
    "assignment_group_id": 12345,
    "points_possible": 10,
    "grading_type": "points",
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

This is a contract example only. Numeric IDs, points, due times, and submission settings must come from approved current configuration.

IMS Common Cartridge fields such as `lomimscc:lom` are not ordinary Canvas REST assignment fields and must not be inserted into this payload unless an official Canvas API contract explicitly requires them.

## Canvas field contract

| Canvas field | Type | Required | Editable by teacher | Source or rule |
|---|---:|---:|---:|---|
| `name` | string | yes | override allowed | canonical naming formatter |
| `description` | HTML string | yes | override allowed | generated assignment body |
| `assignment_group_id` | integer | conditional/usually yes | no | live metadata resolution |
| `points_possible` | number | yes | override allowed | assignment-type matrix |
| `grading_type` | enum | yes | limited | assignment-type matrix |
| `submission_types` | list | yes | limited | assignment-type matrix |
| `due_at` | ISO timestamp or null | conditional | override allowed | instructional date + approved time |
| `unlock_at` | ISO timestamp or null | no | override allowed | policy |
| `lock_at` | ISO timestamp or null | no | override allowed | policy |
| `published` | boolean | yes | publish workflow only | false during preview |
| `allowed_attempts` | integer | no | limited | assignment-type policy |
| `omit_from_final_grade` | boolean | yes | limited | assignment-type policy |

## Supported grading types

Canvas-compatible examples include:

```text
points
percent
letter_grade
gpa_scale
pass_fail
not_graded
```

The exact allowed grading type for each assignment type must be defined in the assignment-type matrix.

## Supported submission types

Potential Canvas values include:

```text
none
online_text_entry
online_url
online_upload
media_recording
student_annotation
external_tool
on_paper
```

Do not select a submission type until the current assignment-type policy confirms it.

## Description HTML contract

Generated assignment HTML may include:

- concise assignment instructions;
- verified resource links;
- assessment details;
- approved study-guide links;
- teacher-approved supplemental wording.

It must not include:

- invented links;
- teacher-only files;
- secure assessment answers;
- raw local file paths;
- student data;
- hidden diagnostics;
- unsupported package metadata;
- unresolved placeholders presented as real content.

## Resource references

Each linked resource must include internal metadata:

```text
resource_id
title
verification_status
audience
sensitivity
canvas_file_id
canvas_url
content_hash
```

Required behavior:

- teacher-only resources are blocked from student-facing output;
- unresolved links remain unresolved;
- a required unresolved resource blocks publish;
- optional unresolved resources produce a warning;
- resources must not be silently removed to make validation pass.

## Internal safety metadata

Every generated assignment must carry:

```text
comparison_status
blockers
dependencies
approval_state
approval_revision
snapshot_id
snapshot_freshness
deployment_status
verification_status
```

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

These states describe comparison to Canvas, not teacher save state.

## Readiness states

Suggested internal readiness vocabulary:

```text
DRAFT
NEEDS_RESOURCES
NEEDS_METADATA
NEEDS_REVIEW
READY
APPROVED
PUBLISHED
VERIFIED
FAILED
```

A `READY` assignment is not yet approved.

## Publish blockers

Publishing must be blocked for:

- missing current course mapping;
- archived or read-only course;
- unresolved assignment group;
- stale or ambiguous assignment-group metadata;
- unresolved required due-time policy;
- invalid due date;
- missing required resource;
- teacher-only resource in student output;
- secure answer resource in student output;
- prohibited subject/type combination;
- unresolved Canvas conflict;
- stale source revision;
- stale Canvas snapshot;
- missing approval;
- approval bound to another revision;
- failed dependency;
- invalid payload;
- missing idempotency identity.

## Dependency behavior

Examples:

- an agenda page assignment link depends on successful assignment creation and verified URL;
- module placement depends on successful assignment creation;
- assessment reminder links may depend on assignment and page creation;
- downstream operations remain blocked when an upstream dependency fails.

## Approval contract

Approval must bind to:

```text
local_object_id
source_revision
content_hash
manifest_revision
snapshot_id
approved_by
approved_at
```

An edit after approval invalidates that approval.

The following may not be approved as normal publish operations:

```text
CONFLICT
BLOCKED
OMIT
DELETE_CANDIDATE
```

## Deployment contract

Publishing must:

1. pass validation;
2. use current metadata;
3. pass comparison;
4. satisfy dependencies;
5. have valid revision-bound approval;
6. use the Phase 27 transport boundary;
7. record the attempt in the deployment ledger;
8. use an idempotency key;
9. read the object back from Canvas;
10. compare intended and actual state;
11. mark success only after verification.

No separate frontend deploy service may bypass the Phase 27 transport, approval, dependency, or ledger layers.

## Verification contract

Read-back verification checks:

- object exists;
- correct course;
- correct name;
- correct description;
- correct assignment group;
- correct points;
- correct grading type;
- correct submission types;
- correct due date and time;
- correct publish state;
- correct module placement where applicable;
- content hash or canonicalized content matches intent.

Verification outcomes:

```text
VERIFIED
PARTIALLY_VERIFIED
FAILED
RETRY_ELIGIBLE
MANUAL_REVIEW_REQUIRED
```

## Assignment-type matrix requirement

A later populated matrix must define for every assignment type:

- title formatter;
- whether an assignment is created;
- points;
- grading type;
- submission types;
- due-date rule;
- due-time rule;
- assignment-group logical name;
- module rule;
- resource requirements;
- announcement behavior;
- blockers;
- verification requirements.

Unresolved values must be marked explicitly and must not be guessed.
