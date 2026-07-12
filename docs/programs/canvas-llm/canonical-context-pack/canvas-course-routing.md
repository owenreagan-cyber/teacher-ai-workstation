# Canvas Course Routing Contract

## Purpose

This contract defines the current 2026–2027 logical subject-to-course routing for the Teacher AI Workstation Canvas LLM builder.

The authoritative machine-readable source remains:

```text
config/curriculum/canvas-course-mappings.json
```

This document explains how the mappings must be interpreted and validated.

## Current production routing

| Subject | Subject key | Canvas course ID | Routing prefix | Assignment policy | Special behavior |
|---|---|---:|---|---|---|
| Math | `math` | `26404` | `SM5` | enabled | Independent course and agenda |
| Reading | `reading` | `26442` | `RM4` | enabled | Shares agenda with Spelling |
| Spelling | `spelling` | `26442` | `SPELL` | enabled | Shares course and agenda with Reading |
| Language Arts | `language-arts` | `26495` | `ELA4` | enabled | Independent course and agenda |
| History | `history` | `26493` | none | disabled | Agenda-capable; no assignment generation by default |
| Science | `science` | `26496` | none | disabled | Agenda-capable; no assignment generation by default |
| Homeroom | `homeroom` | `26427` | `NEWSLETTER` | newsletter only | Homeroom newsletter target |

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

Before a real write, the system should still verify:

- course exists;
- course name matches expected subject/year;
- course is not archived;
- course is writable;
- current user has required permission;
- environment matches intended target.

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

`canonicalPrefix` currently acts as a routing/configuration field.

Current validated values:

```text
Math: SM5
Reading: RM4
Spelling: SPELL
Language Arts: ELA4
Homeroom: NEWSLETTER
```

History and Science have no current assignment prefix because ordinary assignment generation is disabled.

## Spelling prefix conflict

The routing configuration and validator use:

```text
SPELL
```

The current owner-approved title example is:

```text
RM4: Spelling Test 1
```

This may mean the system needs separate fields:

```text
routingPrefix
studentFacingTitlePrefix
```

That distinction is not yet implemented.

Until owner resolution:

- keep `SPELL` in the routing configuration;
- keep `RM4: Spelling Test 1` in the naming acceptance examples;
- do not silently rewrite either;
- mark generated Spelling assignment titles as requiring review if they depend on this conflict.

## History and Science policy

Current canonical behavior:

```text
assignmentPolicy: disabled
agendaCapable: true
```

This means:

- weekly agenda content may be generated;
- teacher notes and resources may be stored;
- ordinary assignments are not generated automatically;
- assignment creation requires a later explicit owner-approved rule.

An approved example title does not automatically enable assignment generation.

## Homeroom policy

Homeroom routes to:

```text
courseId: 26427
canonicalPrefix: NEWSLETTER
newsletterTarget: true
```

Homeroom’s primary generated artifact is the newsletter page.

Homeroom is not treated as an ordinary subject-assignment stream unless a later contract explicitly adds one.

## Failure behavior

Routing must block publication when:

- subject has no current production mapping;
- course is archived;
- writes are blocked;
- environment is ambiguous;
- subject policy disables the requested artifact;
- live course verification fails;
- required assignment group or module metadata is unresolved;
- routing depends on an unresolved prefix conflict.

## Validation requirements

The validator must confirm:

- Math resolves to `26404`;
- Math prefix is `SM5`;
- Reading resolves to `26442`;
- Reading prefix is `RM4`;
- Spelling resolves to `26442`;
- Spelling shares Reading’s course;
- Spelling routing prefix is `SPELL`;
- Language Arts resolves to `26495`;
- Language Arts prefix is `ELA4`;
- History assignments are disabled;
- Science assignments are disabled;
- Homeroom resolves to `26427`;
- Homeroom is a newsletter target;
- archived years are read-only;
- archived-year writes are blocked;
- sandbox routing remains isolated from production.
