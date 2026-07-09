# Canvas LLM Phase 19A Business Rules Catalog

## Status

Analysis-only rule catalog.

Rules in this file are separated into:

```text
OWNER_APPROVED
STRONG_WORKFLOW_EVIDENCE
CONFLICT_NEEDS_DECISION
LEGACY_ONLY
```

## Owner-Approved Rules

### Subject Prefixes

Status:

```text
OWNER_APPROVED
```

Canonical prefixes:

| Subject | Prefix |
|---|---|
| Math | SM5 |
| Reading | RM4 |
| Spelling | RM4 |
| Language Arts / Shurley | ELA4 |
| History | HIST4 |
| Science | SCI4 |

Rule:

```text
Future generation uses canonical prefixes.
Historical variations are aliases only.
AI does not choose prefixes.
```

### Math Assessment Titles

Status:

```text
OWNER_APPROVED
```

Canonical future titles:

```text
SM5: Test {number}
SM5: Fact Test {number}
SM5: Study Guide {number}
```

Legacy aliases may be recognized for search/migration only.

### Math Study Guide Grading

Status:

```text
OWNER_APPROVED
```

Canonical rule:

```text
points_possible = 0
exclude_from_final_grade = true
Does Not Count Toward Final Grade = checked
Purpose = preparation/review
```

Canvas creation requirement:

```text
The "Does Not Count Toward Final Grade" box must be checked.
```

### Assignment Existence

Status:

```text
OWNER_APPROVED
```

Rule:

```text
Assignment existence must be deterministic.
```

AI may:

- suggest wording
- summarize
- explain
- draft parent-facing descriptions after rules decide assignment existence

AI may not:

- decide whether an assignment exists
- invent assignments
- override subject rules
- override grading rules
- override safety boundaries

### Newsletter Model

Status:

```text
OWNER_APPROVED
```

Canonical model:

```text
Newsletter = Homeroom Canvas Page
Announcement = notification only
```

Canonical announcement:

```text
The newsletter has been updated for the week of {date range}.
```

### File Management

Status:

```text
OWNER_APPROVED
```

Near-term:

```text
READ ONLY AI File Assistant
```

Allowed:

- discover files
- classify files
- detect duplicates
- map relationships
- suggest organization
- create cleanup plans

Future:

```text
WRITE-GATED AI File Organizer
```

Required before any operation:

1. show proposed changes
2. human approves
3. execute exact approved operation
4. verify result

Never:

- automatic rename
- automatic move
- automatic delete
- automatic upload
- silent alteration of source materials

Principle:

```text
AI may organize information.
AI may not silently alter source materials.
```

## Strong Workflow Evidence

### Math Test Triple

Status:

```text
STRONG_WORKFLOW_EVIDENCE
```

A Math Test creates:

1. Written Test
2. Fact Test
3. Study Guide

Placement:

- Written Test: test day
- Fact Test: test day
- Study Guide: day before test when possible

Phase 19B should promote this to canonical after final title/grading tables are locked.

### Reading + Spelling Together

Status:

```text
STRONG_WORKFLOW_EVIDENCE
```

Rules:

- Reading and Spelling share RM4 identity.
- Reading and Spelling may have separate pacing rows.
- Reading and Spelling may have separate assignments.
- Reading owns the Canvas page.
- Announcements are combined.
- Spelling does not create a standalone Canvas page.
- Standalone Spelling announcements should be blocked.

### Friday Rules

Status:

```text
STRONG_WORKFLOW_EVIDENCE
```

Rules:

- no normal homework assignments on Friday
- non-test Friday assignments blocked by default
- At Home section omitted on Friday
- tests allowed
- reminder communication allowed
- celebratory copy optional and teacher-controlled

### Pre-Deploy Validation

Status:

```text
STRONG_WORKFLOW_EVIDENCE
```

Future diagnostics should check:

- missing file/resource references
- Friday violations
- duplicate assignments
- title prefix conventions
- Math Study Guide pairing
- Reading/Spelling Together integrity
- course ID drift
- write gate readiness

### Resource / Content Map

Status:

```text
STRONG_WORKFLOW_EVIDENCE
```

Concept:

```text
resource relationships should be mapped as evidence-backed references, not inferred by prompts alone.
```

Content/resource records should track:

- subject
- lesson reference
- type
- canonical name
- location or Canvas reference
- confidence
- approval status
- student-facing vs teacher-only status

## Conflicts Needing Decision

### Math Homework Titles

Examples seen or proposed:

```text
SM5: Lesson 78 Evens
SM5: Evens HW — Lesson 78
SM5: Odds HW — Lesson 79
```

Status:

```text
CONFLICT_NEEDS_DECISION
```

Phase 19B should choose exact canonical homework format and legacy aliases.

### Reading Homework Titles

Observed/potential formats:

```text
RM4: Reading HW {number}
RM4: Lesson {number} Workbook
```

Status:

```text
CONFLICT_NEEDS_DECISION
```

### Fact Test Numbering

Potential formats:

```text
SM5: Fact Test {number}
SM5: Lesson {number} Fact Test
```

Owner direction favors:

```text
SM5: Fact Test {number}
```

but Phase 19B should define whether `{number}` means test number or lesson number.

### Power Up Map

Status:

```text
CONFLICT_NEEDS_DECISION
```

Legacy evidence includes more than one Power Up mapping scope.

Phase 19B should create a reviewed versioned table.

### Spelling Test Titles

Potential formats:

```text
RM4: Spelling Test {test_number}
RM4: Spelling Test {lesson_endpoint}
```

Status:

```text
CONFLICT_NEEDS_DECISION
```

### Canvas Page Title Format

Potential formats:

```text
Q1W1
Q1 W1
Week of {date range}
Subject — Q1W1
```

Status:

```text
CONFLICT_NEEDS_DECISION
```

## Legacy-Only Rules

Do not adopt directly:

- direct deploy functions
- direct Canvas file rename/move
- prompt-only lesson generation
- hardcoded historical course IDs
- standalone Spelling announcement generation
- unreviewed page body templates
- unreviewed birthday persistence
- automatic publish/front-page changes

## Future Canonical Tables Needed

Phase 19B should create plain, reviewable tables for:

- subject prefixes
- assignment title formats
- assignment group routing
- grading/exclude-from-final rules
- Math Test triple rules
- Math Fact Test map
- Math Power Up map
- Reading/Spelling Together rules
- Spelling word bank/focus rule
- Friday behavior
- newsletter schema
- resource relationship schema
- file classification schema
- diagnostic check definitions
- write gate approval phrases
