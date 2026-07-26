# Canonical Naming Conventions

## Purpose

Canvas titles must be deterministic, concise, teacher-readable, and sortable.

Highest authority:

```text
docs/programs/canvas-llm/2026-2027-fpk-canvas-operating-contract.md
```

The general assignment-tab format is:

```text
CLASS PREFIX: Assignment Name
```

Punctuation, capitalization, spacing, prefixes, and number placement are part of the contract and must be validated.

## Approved subject prefixes

| Subject | Prefix | Status |
|---|---|---|
| Math | `SM5:` | APPROVED |
| Reading | `RM4:` | APPROVED |
| Spelling | `RM4:` | APPROVED |
| Language Arts | `ELA4:` | APPROVED |
| History | `HIST4:` | APPROVED |
| Science | `SCI4:` | APPROVED |
| Homeroom | No ordinary assignment prefix | N/A |

Reading and Spelling may share a Canvas course and agenda page while retaining separate instructional and assignment identities.

## Approved assignment-title examples

These examples are authoritative acceptance cases:

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

## Assessment naming patterns

| Subject | Pattern | Example |
|---|---|---|
| Math written | `SM5: Written Assessment {n}` | `SM5: Written Assessment 7` |
| Math fact | `SM5: Fact Assessment {n}` | `SM5: Fact Assessment 7` |
| Reading mastery | `RM4: Mastery Test {n}` | `RM4: Mastery Test 4` |
| Reading fluency | `RM4: Fluency Checkout {n}` | `RM4: Fluency Checkout 4` |
| Spelling | `RM4: Spelling Test {n}` | `RM4: Spelling Test 1` |
| Language Arts | topic or writing-title form | `ELA4: Persuasive Writing Final Draft` |
| History | topic form | `HIST4: Ancient Rome Assessment` |
| Science | topic form | `SCI4: Life Cycles Assessment` |

Reading Test 14 must never generate Checkout 14 or a title referencing Checkout 14.

## Math assignment patterns

### Lesson homework

Homework titles follow the operating-contract schedule rather than odd/even lesson parity alone.

Examples:

```text
SM5: Lesson 18 Homework
```

Historical note: older evidence used `SM5: Lesson {n} Odds/Evens` patterns. Those remain superseded naming evidence unless explicitly reapproved.

### Study Guides

Study guides are not part of the 2026–2027 Canvas workflow.

Historical candidate patterns such as `SM5: Study Guide {n}` remain dormant and non-authoritative.

## Reading assignment patterns

### Classwork

Daily classwork goal on the agenda page:

```text
Workbook
```

### Homework

Tuesday and Thursday homework:

```text
Comprehension Questions
```

## Spelling assignment pattern

```text
RM4: Spelling Test {testNumber}
```

Example:

```text
RM4: Spelling Test 1
```

Historical note: a legacy `SPELL` routing prefix remains dormant evidence only.

## Language Arts assignment patterns

Final writing drafts use titles such as:

```text
ELA4: Persuasive Writing Final Draft
```

## History and Science assignment patterns

History and Science assignments are generated only during their active quarters per:

```text
config/curriculum/canvas/quarter-subject-activation-2026-2027.json
```

Approved examples:

```text
HIST4: Ancient Rome Assessment
SCI4: Life Cycles Assessment
```

## Agenda-page content naming

For Math, the page body uses concise instructional wording:

```text
In Class: Lesson 18
Homework: #12-30 evens
```

Agenda pages must not link to assignments or curriculum resources.

## Agenda page titles

The current 2026–2027 Canvas agenda-page scaffold is authoritative for exact week-page titles and date labels from:

```text
config/curriculum/canvas/instructional-weeks-2026-2027.json
config/curriculum/canvas/weekly-agenda-standard-2026-2027.json
```

## Homeroom naming

Homeroom uses a monthly Newsletter Page rather than the standard subject agenda artifact.

Approved monthly newsletter page title pattern:

```text
Homeroom Newsletter — {Month YYYY}
```

Approved newsletter-update announcement wording:

```text
The newsletter has been updated for {Month YYYY}.
```

## Assignment points and due time

All assignments:

- are worth 100 points;
- display as percentages;
- are due on the same calendar day as the assignment;
- are due at 11:59 PM America/New_York.

## Normalization examples

Teacher-entered shorthand must be normalized without changing meaning.

| Teacher input | Normalized instructional text |
|---|---|
| `l1` | `Lesson 1` |
| `L1` | `Lesson 1` |
| `lesson 1` | `Lesson 1` |

Normalization must not guess an assessment number, topic, resource, due time, or assignment group when those values are unresolved.

## Validation requirements

The context-pack validator must test exact equality for at least:

```text
SM5: Written Assessment 7
SM5: Fact Assessment 7
RM4: Mastery Test 4
RM4: Fluency Checkout 4
RM4: Spelling Test 1
ELA4: Persuasive Writing Final Draft
HIST4: Ancient Rome Assessment
SCI4: Life Cycles Assessment
```

Validation must fail for known incorrect forms such as:

```text
SM5: 7 Written Assessment
SM5 Written Assessment 7
Math Test 7
RM4 Spelling Test 1
```

## Unresolved naming decisions

- Language Arts non-assessment accuracy-grade titles when not covered by operating contract

Generator alignment with these naming rules is scheduled for C0L and later phases.
