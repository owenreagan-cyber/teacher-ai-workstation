# Reading and Spelling Together Logic

## Purpose

Together Logic defines how Reading and Spelling share Canvas surfaces without becoming one instructional subject.

Highest authority:

```text
docs/programs/canvas-llm/2026-2027-fpk-canvas-operating-contract.md
```

## Canonical rule

Reading and Spelling:

```text
share one Canvas course
share one weekly agenda surface
remain separate instructional subjects
retain separate daily entries
retain separate assignment families
retain separate assessment logic
retain separate revision and approval state
```

Math is not part of Together Logic.

## Current routing relationship

```text
Reading course ID: 26442
Spelling course ID: 26442
Spelling mergedWithSubject: reading
Spelling sharesCanvasCourseWith: reading
readingAndSpellingShareAgenda: true
reading-spelling page group
```

## Separate subject identity

The weekly model must retain separate subject keys:

```text
reading
spelling
```

Each subject keeps its own lesson or test input, entry type, in-class text, homework text, notes, validation, revision, assignment intent, announcement intent, and approval state.

The internal storage field may remain `at_home`; rendered agenda output uses the `Homework` label.

## Shared agenda composition

Recommended display order per weekday:

```text
Reading
Spelling
```

For each weekday, the shared page may show Reading and Spelling In Class and Homework sections.

## Assignment behavior

Reading assignments remain Reading assignments.

Spelling assignments remain Spelling assignments.

Examples:

```text
RM4: Mastery Test 4
RM4: Fluency Checkout 4
RM4: Spelling Test 1
```

Both subjects use the `RM4:` title prefix.

Historical note: a legacy `SPELL` routing prefix conflict is superseded and non-authoritative for 2026–2027 titles.

## Reading assessment behavior

Reading may generate Mastery Tests and Fluency Checkouts.

Reading Test 14 must not generate Checkout 14.

## Spelling assessment behavior

Spelling may generate Spelling Test assignments and minimal assessment announcements.

The current canonical data supports Tests 1–24 only.

## Announcement behavior

Standalone Spelling announcements are allowed.

Standalone Reading announcements are allowed.

Required behavior:

- Spelling assessment without a Reading assessment that week → standalone Spelling announcement;
- Reading assessment without a Spelling assessment that week → standalone Reading announcement;
- Reading and Spelling assessments in the same instructional week → combined family announcement;
- sharing a Canvas course or agenda does not by itself require a combined announcement;

Assessment announcements are prepared for Friday 4:00 PM America/New_York.

## Prohibited interpretations

Together Logic must never be interpreted as merging subjects, sharing all assignment groups automatically, using one approval for every artifact, or generating exact Spelling words or Reading checkout locations in parent-facing output.

## Validation requirements

The validator must confirm shared course and agenda behavior, separate subject records, separate assessment-family logic, Reading Test 14 no-Checkout rule, and Spelling Test 25 gating.
