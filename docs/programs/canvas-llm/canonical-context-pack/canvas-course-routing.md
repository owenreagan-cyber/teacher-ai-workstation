# Canvas Course Routing Contract

## Purpose

This contract defines the current 2026–2027 logical subject-to-course routing for the Teacher AI Workstation Canvas LLM builder.

Highest authority:

```text
docs/programs/canvas-llm/2026-2027-fpk-canvas-operating-contract.md
```

The authoritative machine-readable source remains:

```text
config/curriculum/canvas-course-mappings.json
config/curriculum/canvas/quarter-subject-activation-2026-2027.json
```

## Current production routing

| Subject | Subject key | Canvas course ID | Title prefix | Assignment policy | Special behavior |
|---|---|---:|---|---|---|
| Math | `math` | `26404` | `SM5:` | enabled | Independent course and agenda |
| Reading | `reading` | `26442` | `RM4:` | enabled | Shares agenda with Spelling |
| Spelling | `spelling` | `26442` | `RM4:` | enabled | Shares course and agenda with Reading |
| Language Arts | `language-arts` | `26495` | `ELA4:` | enabled | Independent course and agenda |
| History | `history` | `26493` | `HIST4:` | quarter-activated | Active Q1 and Q3 only |
| Science | `science` | `26496` | `SCI4:` | quarter-activated | Active Q2 and Q4 only |
| Homeroom | `homeroom` | `26427` | none | newsletter only | Monthly Homeroom newsletter target |

## Routing identity

Every routed subject record should include:

```text
subjectId
displayName
courseId
canonicalPrefix
assignmentPolicy
readOnly
writesBlocked
newsletterTarget
mergedWithSubject
sharesCanvasCourseWith
```

Not every field applies to every subject.

## Current-year authority

The 2026–2027 production mapping is the only current writable routing source.

Archived mappings may be retained for historical comparison, but must remain:

```text
readOnly: true
writesBlocked: true
```

Archived course IDs must never be reused for current production deployment.

## Environment separation

The routing configuration may contain:

```text
production
demoSandbox
archivedByYear
```

Rules:

- production mappings are current-year targets;
- sandbox mappings are test-only;
- archived mappings are read-only;
- no environment may silently fall back to another;
- the UI must show the selected environment;
- production writes require explicit approval and current metadata.

## Course ID behavior

A committed course ID may establish the logical current routing target.

Before a real write, the system should still verify course exists, name matches expected subject/year, course is not archived, course is writable, current user has required permission, and environment matches intended target.

A mismatch blocks publication.

## Assignment-group and module metadata

The course mapping does not authorize guessing numeric Canvas object IDs.

The following must be resolved from teacher-initiated read-only Canvas metadata:

```text
assignment_group_id
module_id
module_item_id
current page URL
current assignment URL
```

Logical names may be committed. Numeric live IDs must be verified.

## Prefix interpretation

Approved assignment-title prefixes:

```text
Math: SM5:
Reading: RM4:
Spelling: RM4:
Language Arts: ELA4:
History: HIST4:
Science: SCI4:
```

Every assignment title must begin with the correct colon-form prefix.

Historical note: older routing evidence used a separate `SPELL` routing key. That prefix is superseded and non-authoritative for 2026–2027 assignment titles.

## History and Science quarter activation

Quarter activation is machine-readable in:

```text
config/curriculum/canvas/quarter-subject-activation-2026-2027.json
```

Rules:

- Q1 and Q3: History active; Science inactive and untouched.
- Q2 and Q4: Science active; History inactive and untouched.

During an active quarter, the active subject may generate agenda pages, assignments, and announcements per the operating contract.

During an inactive quarter, the inactive subject receives no generated grades, assignments, announcements, or agenda changes. Its existing Canvas page must remain untouched.

## Homeroom policy

Homeroom routes to:

```text
courseId: 26427
newsletterTarget: true
```

Homeroom's primary generated artifact is the monthly newsletter page.

Homeroom is not treated as an ordinary subject-assignment stream.

## Failure behavior

Routing must block publication when:

- subject has no current production mapping;
- course is archived;
- writes are blocked;
- environment is ambiguous;
- subject is inactive for the current quarter;
- live course verification fails;
- required assignment group or module metadata is unresolved.

## Validation requirements

The validator must confirm:

- Math resolves to `26404` with prefix `SM5:`;
- Reading resolves to `26442` with prefix `RM4:`;
- Spelling resolves to `26442` with prefix `RM4:`;
- Language Arts resolves to `26495` with prefix `ELA4:`;
- History resolves to `26493` with prefix `HIST4:`;
- Science resolves to `26496` with prefix `SCI4:`;
- quarter activation matches `quarter-subject-activation-2026-2027.json`;
- Homeroom resolves to `26427`;
- archived years are read-only;
- sandbox routing remains isolated from production.
