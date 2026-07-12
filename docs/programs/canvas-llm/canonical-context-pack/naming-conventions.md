# Canonical Naming Conventions

## Purpose

Canvas titles must be deterministic, concise, teacher-readable, and sortable.

The general assignment-tab format is:

```text
CLASS PREFIX: Assignment Name
```

Punctuation, capitalization, spacing, prefixes, and number placement are part of the contract and must be validated.

Legacy naming conventions must not override the examples explicitly approved by the owner.

## Approved subject prefixes

| Subject | Prefix | Status |
|---|---|---|
| Math | `SM5` | APPROVED |
| Reading | `RM4` | APPROVED |
| Spelling | `RM4` for current assignment-title examples | APPROVED_WITH_OPEN_FIELDS |
| Language Arts | `ELA4` | APPROVED |
| History | `HIST4` | APPROVED |
| Science | `SCI4` | APPROVED |
| Homeroom | No ordinary assignment prefix currently approved | OWNER_DECISION_REQUIRED |

Reading and Spelling may share a Canvas course and agenda page while retaining separate instructional and assignment identities.

## Approved assignment-title examples

These examples are authoritative acceptance cases:

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

## Math assignment patterns

### Lesson homework

```text
SM5: Lesson {lessonNumber} Odds
SM5: Lesson {lessonNumber} Evens
```

The Odds/Evens suffix is determined by canonical Math parity rules and may be changed only by an explicit teacher override.

Examples:

```text
SM5: Lesson 1 Odds
SM5: Lesson 2 Evens
```

### Written tests

```text
SM5: Math Test {testNumber}
```

Example:

```text
SM5: Math Test 1
```

### Fact Tests

```text
SM5: Fact Test {factTestNumber}
```

Example:

```text
SM5: Fact Test 1
```

### Study Guides

The exact current assignment title pattern remains to be verified against current owner-approved behavior.

Candidate historical patterns must remain non-canonical until approved:

```text
SM5: Study Guide {testNumber}
SM5: Math Test {testNumber} Study Guide
```

Status: `OWNER_DECISION_REQUIRED`

### Investigations

Exact assignment-generation and title behavior remain to be verified.

Status: `OWNER_DECISION_REQUIRED`

## Reading assignment patterns

### Lesson workbook and comprehension

```text
RM4: Lesson {lessonNumber} Workbook and Comprehension
```

Example:

```text
RM4: Lesson 4 Workbook and Comprehension
```

### Reading tests

Exact current title pattern remains to be confirmed.

Possible historical evidence includes:

```text
RM4: Reading Test {testNumber}
RM4: Reading Mastery Test {testNumber}
```

Status: `OWNER_DECISION_REQUIRED`

### Reading Checkouts

Exact current title pattern remains to be confirmed.

Possible historical evidence includes:

```text
RM4: Checkout {checkoutNumber}
RM4: Reading Checkout {checkoutNumber}
```

Status: `OWNER_DECISION_REQUIRED`

Reading Test 14 must never generate Checkout 14 or a title referencing Checkout 14.

## Spelling assignment pattern

```text
RM4: Spelling Test {testNumber}
```

Example:

```text
RM4: Spelling Test 1
```

The shared `RM4` prefix reflects the current owner-approved title example. Any legacy `SPELL` prefix remains legacy evidence unless explicitly reapproved.

## Language Arts assignment patterns

### Classroom Practice

```text
ELA4: Classroom Practice {practiceNumber}
```

Example:

```text
ELA4: Classroom Practice 4
```

### Tests

Exact format remains to be confirmed.

Candidate:

```text
ELA4: {unitOrTopic} Test
```

Status: `OWNER_DECISION_REQUIRED`

## History assignment patterns

History assignments are disabled by default unless explicitly approved for the current subject/type.

Approved examples:

```text
HIST4: American Revolution Test
HIST4: American Revolution Chapter 1 Vocab
```

These examples establish the prefix and topic-first structure but do not authorize all History entries to create assignments.

## Science assignment patterns

Science assignments are disabled by default unless explicitly approved for the current subject/type.

Approved example:

```text
SCI4: Structures and Functions Chapter 1 Test
```

This establishes the prefix and topic-first structure but does not authorize all Science entries to create assignments.

## Agenda-page content naming

For Math, the page body uses concise instructional wording rather than repeating the full Canvas assignment title.

Example:

```text
Math

In Class: Lesson 1
Homework: [SM5: Lesson 1 Odds]
```

The Homework text must link to the corresponding verified Canvas assignment after that assignment exists.

Before the assignment URL is created and verified, the page generator must:

- retain the intended assignment reference;
- mark the dependency unresolved;
- avoid inventing a URL;
- block final publish where the verified link is required.

## Agenda page titles

The current 2026–2027 Canvas agenda-page scaffold is authoritative for exact week-page titles and date labels.

Do not infer or replace those titles with generic patterns until they are extracted and indexed from:

```text
config/curriculum/canvas/instructional-weeks-2026-2027.json
config/curriculum/canvas/weekly-agenda-standard-2026-2027.json
```

## Homeroom naming

Homeroom uses a Newsletter Page rather than the standard subject agenda artifact.

Exact newsletter title pattern remains to be documented in:

```text
newsletter-homeroom-contract.md
```

Status: `OWNER_DECISION_REQUIRED`

## Normalization examples

Teacher-entered shorthand must be normalized without changing meaning.

Examples:

| Teacher input | Normalized instructional text |
|---|---|
| `l1` | `Lesson 1` |
| `L1` | `Lesson 1` |
| `lesson 1` | `Lesson 1` |
| `Lesson 1` | `Lesson 1` |

For Math Lesson 1, the resulting assignment title is:

```text
SM5: Lesson 1 Odds
```

Normalization must not guess an assessment number, topic, homework parity override, resource, due time, or assignment group when those values are unresolved.

## Validation requirements

The context-pack validator must test exact equality for at least:

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

Validation must fail for known incorrect forms such as:

```text
SM5: 1 Lesson Odds
SM5 Lesson 1 Odds
Math Test 1
RM4 Spelling Test 1
```

## Unresolved naming decisions

- Math Study Guide title
- Math Investigation title
- Reading Test title
- Reading Checkout title
- Language Arts test title
- Homeroom newsletter title
- Standard weekly announcement titles
- Assessment reminder titles
