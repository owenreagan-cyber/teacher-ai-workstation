# Math Rules and Maps

## Status

```text
APPROVED
```

## Curriculum

```text
Saxon Math 5
```

## Canonical sources

```text
config/curriculum/math/saxon-math-5/lesson-power-up-map.json
config/curriculum/math/saxon-math-5/fact-test-practice-map.json
scripts/canvas_llm_phase22/validate_canonical_knowledge.py
scripts/canvas_llm_phase22/phase22_workstation.py
```

## Course routing

Current 2026–2027 routing:

```text
Subject: Math
Canvas course ID: 26404
Canonical prefix: SM5
```

Numeric course metadata remains subject to current approved configuration and future read-only metadata verification.

## Lesson coverage

The canonical lesson-to-Power-Up map contains exactly:

```text
Lessons 1–120
```

Validated boundary examples:

```text
Lesson 5  → Power Up A
Lesson 25 → Power Up D
Lesson 90 → Power Up F
```

The full map remains in JSON and must not be duplicated manually into this document.

## Teacher input normalization

Accepted unambiguous examples:

```text
l1
L1
lesson 1
Lesson 1
```

Canonical normalized result:

```text
Lesson 1
```

## Standard lesson behavior

For a normal Math lesson:

```text
In Class: Lesson {lessonNumber}
```

Suggested homework is determined by lesson parity unless overridden:

```text
Odd lesson number  → Odds
Even lesson number → Evens
```

Examples:

```text
Lesson 1 → SM5: Lesson 1 Odds
Lesson 2 → SM5: Lesson 2 Evens
```

An explicit teacher override outranks the parity default.

## Power Up resolution

Each lesson resolves to its mapped Power Up from:

```text
lesson-power-up-map.json
```

The system must:

- preserve the exact canonical code;
- never infer a missing code;
- treat a missing lesson mapping as blocking;
- expose the Power Up in resource requirements;
- retain teacher corrections separately from canonical map data.

## Fact Test coverage

The canonical Fact Test map contains exactly:

```text
Fact Tests 1–23
```

Validated example:

```text
Fact Test 12 → Power Up E
```

Fact Test 12 also includes the approved division-practice description.

## Assessment family

A Math assessment family may include:

```text
Written Math Test
Fact Test
Study Guide
Assessment announcement
Assessment reminder
Required resources
```

Canonical internal family fields include:

```text
assessmentFamilyId
testNumber
writtenTestDate
factTestDate
studyGuideDate
announcementDraft
factTest
studyGuideSuppressesNormalHomework
suppressionReason
requiredResources
```

## Study Guide scheduling

The Study Guide belongs on the previous valid instructional day before the Math test.

It suppresses normal Math homework for that preparation day.

Existing canonical behavior:

```text
Study Guide {n} is the only Math homework before Test {n}.
```

Required resources may include:

```text
Study Guide {n} Blank
Study Guide {n} Completed
Power Up {code} practice
```

Missing required resources block final publication.

## Test naming

Approved assignment titles:

```text
SM5: Math Test {testNumber}
SM5: Fact Test {factTestNumber}
```

Examples:

```text
SM5: Math Test 1
SM5: Fact Test 1
```

The exact Study Guide assignment title remains unresolved and must not be guessed.

## Monday test prohibition

Math tests may not occur on Monday.

When disruption logic would move a test to Monday:

- move it to Tuesday;
- recalculate Study Guide placement;
- regenerate reminders;
- regenerate announcements;
- invalidate affected approvals and comparison results.

## Friday behavior

Friday instruction is allowed.

Default Friday homework behavior:

```text
none
```

A teacher may explicitly override this, but the system must not silently remove teacher-entered Friday content.

## Resource requirements

Potential required resources include:

```text
Student Book lesson
Power Up practice
Homework worksheet
Fact Test practice
Study Guide blank
Study Guide completed
Teacher-approved supporting resource
```

Only verified resources may be emitted as resolved links.

## Validation requirements

The validator must confirm:

- 120 lessons exist;
- lesson keys cover 1–120 exactly;
- Lesson 5 maps to A;
- Lesson 25 maps to D;
- Lesson 90 maps to F;
- 23 Fact Tests exist;
- Fact Test keys cover 1–23 exactly;
- Fact Test 12 maps to E;
- Fact Test 12 retains approved division-practice wording;
- title formatting matches canonical examples;
- odd/even homework behavior is deterministic;
- explicit teacher override outranks parity;
- missing mappings block generation;
- no Monday test is produced.
