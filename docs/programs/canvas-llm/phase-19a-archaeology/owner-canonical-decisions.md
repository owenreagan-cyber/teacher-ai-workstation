# Canvas LLM Phase 19A Owner Canonical Decisions

## Status

Owner-approved decision capture for future Phase 19B canonical rule constitution.

This document captures decisions made after archaeology review. It is a planning/specification artifact only.

## Subject Prefixes

Canonical prefixes are mandatory for future generation:

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
Historical variations are aliases only.
Future generation uses canonical prefixes.
AI does not choose prefixes.
```

## Math Assessment Titles

Canonical Math assessment titles:

```text
SM5: Test {number}
SM5: Fact Test {number}
SM5: Study Guide {number}
```

Legacy aliases may be mapped for search/migration, but they are not future output formats.

Examples of legacy aliases:

```text
SM5: Lesson {number} Test
SM5: Test — Lesson {number}
```

## Math Study Guide Grading

Canonical Study Guide rule:

```text
points_possible = 0
exclude_from_final_grade = true
Does Not Count Toward Final Grade = checked
Purpose = preparation/review
```

Important:

```text
The Canvas "Does Not Count Toward Final Grade" box must be checked when the assignment is created.
```

## Assignment Rule Philosophy

Assignment existence must be deterministic.

AI may:

- suggest wording
- summarize
- explain
- draft parent-facing text after rules decide the assignment exists

AI may not:

- decide whether an assignment exists
- invent assignments
- override subject rules
- override grading rules
- override safety boundaries

## Newsletter Model

Canonical model:

```text
Newsletter = Homeroom Canvas Page
Announcement = notification only
```

Canonical announcement text:

```text
The newsletter has been updated for the week of {date range}.
```

Newsletter page owns:

- weekly updates
- family communication
- events
- reminders
- approved birthday handling

Birthday information requires separate privacy approval before reuse or storage.

## File Management Model

Vision:

```text
AI File Assistant
```

Near-term phase:

```text
READ ONLY
```

Allowed:

- discover files
- classify files
- detect duplicates
- map relationships
- suggest organization
- create cleanup plans

Future phase:

```text
WRITE-GATED FILE ORGANIZER
```

Before any file operation:

1. Show proposed changes.
2. Human approves.
3. Execute exact approved operation.
4. Verify result.

Never allowed:

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

## Reading / Spelling Together

Canonical direction:

- Reading and Spelling share RM4 identity.
- Reading and Spelling may have separate pacing rows.
- Reading and Spelling may have separate assignments.
- Reading owns the Canvas page.
- Announcements are combined.
- No standalone Spelling announcements.

## Friday Rules

Canonical direction:

- no normal homework assignments on Friday
- At Home section omitted unless explicitly required
- tests allowed
- reminder communication allowed
- celebratory copy remains optional and teacher-controlled

## Review Status

These decisions are ready to become:

```text
APPROVED_PATTERN
```

in Phase 19B.

This document does not authorize:

- Canvas writes
- assignment creation
- page creation
- file movement
- publishing
- code implementation
