# Reading and Spelling Together Logic

## Purpose

Together Logic defines how Reading and Spelling share Canvas surfaces without becoming one instructional subject.

This contract exists to prevent incorrect merging of unrelated subjects and to preserve current validated routing behavior.

## Canonical rule

Reading and Spelling:

```text
share one Canvas course
share one weekly agenda surface
remain separate instructional subjects
retain separate daily entries
retain separate assignment families
retain separate resource requirements
retain separate assessment logic
retain separate revision and approval state
```

Math is not part of Together Logic.

Language Arts, History, Science, and Homeroom are not part of Together Logic.

## Current routing relationship

```text
Reading course ID: 26442
Spelling course ID: 26442
Spelling mergedWithSubject: reading
Spelling sharesCanvasCourseWith: reading
```

Current agenda rule:

```text
readingAndSpellingShareAgenda: true
```

Current Phase 22 generation group:

```text
reading-spelling
```

## Separate subject identity

The weekly model must retain separate subject keys:

```text
reading
spelling
```

They must never be collapsed into one persisted subject row.

Each subject keeps its own:

```text
lesson or test input
entry type
in-class text
at-home text
resources
notes
resolver output
validation
revision
assignment intent
announcement intent
approval state
```

## Shared agenda composition

The shared agenda page may combine Reading and Spelling content by weekday.

Recommended display order:

```text
Reading
Spelling
```

For each weekday, the shared page may show:

```text
Reading — In Class
Reading — At Home
Spelling — In Class
Spelling — At Home
```

Blank fields may be omitted visually, but the underlying subject/day records remain present.

## Shared page identity

A shared Reading/Spelling page must carry one stable page artifact identity while preserving source dependencies from both subjects.

Internal page metadata should include:

```text
subject_group: reading-spelling
source_subjects:
  - reading
  - spelling
source_entry_ids
source_revisions
content_hash
dependencies
blockers
approval_state
```

## Assignment behavior

Reading assignments remain Reading assignments.

Spelling assignments remain Spelling assignments.

Sharing a course or agenda does not merge titles, grading rules, assignment groups, resources, or assessment families.

Examples:

```text
RM4: Lesson 4 Workbook and Comprehension
RM4: Spelling Test 1
```

The Spelling prefix conflict remains separately documented.

## Reading assessment behavior

Reading may generate:

```text
Reading Test
Reading Checkout
Reading assessment announcement
Reading assessment reminder
```

Reading Test 14 must not generate Checkout 14.

## Spelling assessment behavior

Spelling may generate:

```text
Spelling Test
Spelling assessment notice
Spelling reminder
focus-word content
```

The current canonical data supports Tests 1–24 only.

## Resource behavior

Reading and Spelling may share a page but not automatically share resource eligibility.

Examples:

- a Reading Reader page is not a Spelling resource;
- a Spelling word list is not a Reading comprehension resource;
- a shared announcement may reference both only when explicitly composed;
- teacher-only or secure resources remain blocked regardless of shared course.

## Approval behavior

Approval must be revision-bound.

For a shared page:

- a Reading edit invalidates the shared page approval;
- a Spelling edit invalidates the shared page approval;
- an unrelated Math edit does not invalidate it;
- subject assignment approvals remain separate;
- page approval does not automatically approve all linked assignments.

## Dependency behavior

A shared page may depend on:

```text
Reading assignment URLs
Reading resource URLs
Spelling assignment URLs
Spelling resource URLs
assessment reminder state
```

A required unresolved dependency blocks page publication.

Optional unresolved content produces a warning only when the contract allows omission.

## Announcement behavior

Standalone Spelling announcements are allowed.

Spelling tests typically occur once each instructional week, so a standalone
Spelling assessment announcement is normal expected behavior.

Reading and Spelling announcements combine only when both subjects have an
assessment occurring within the same instructional week.

Required behavior:

- Spelling assessment without a Reading assessment that week → standalone Spelling announcement;
- Reading assessment without a Spelling assessment that week → standalone Reading announcement;
- Reading and Spelling assessments in the same instructional week → combined family announcement;
- sharing a Canvas course or agenda does not by itself require a combined announcement;
- combined communication does not merge the underlying assessment families.

A combined announcement may contain separate labeled sections such as:

```text
Reading Test
Reading Checkout, when applicable
Spelling Test
```

Reading, Checkout, and Spelling records retain separate identities,
dependencies, resources, revisions, and validation.

## Prohibited interpretations

Together Logic must never be interpreted as:

- merging Math, Reading, and Spelling;
- storing Reading and Spelling as one subject;
- sharing all resources automatically;
- sharing all assignment groups automatically;
- using one approval for every Reading and Spelling artifact;
- assigning one assessment number across both subjects;
- generating Checkout content for Spelling;
- generating Spelling focus words from Reading data.

## Validation requirements

The validator must confirm:

- Reading and Spelling share course `26442`;
- Reading and Spelling share an agenda;
- Reading and Spelling remain separate subject records;
- Math is excluded from the shared group;
- separate resource resolution remains intact;
- separate assignment generation remains intact;
- separate assessment-family logic remains intact;
- shared-page approval is invalidated by either source subject edit;
- unrelated-subject edits do not invalidate the shared page;
- Reading Test 14 never creates Checkout 14;
- Spelling Test 25 is not generated without approved source data.
