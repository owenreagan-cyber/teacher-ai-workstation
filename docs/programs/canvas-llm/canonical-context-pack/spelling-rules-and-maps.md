# Spelling Rules and Maps

## Status

```text
APPROVED_WITH_OWNER_DECISIONS_REQUIRED
```

## Curriculum

The current tracked canonical source is:

```text
config/curriculum/spelling/cumulative-test-word-lists.json
```

## Current verified coverage

The tracked JSON contains exactly:

```text
Spelling Tests 1–24
```

Each test contains:

```text
25 cumulative words
5 focus words
```

The current focus-word rule selects cumulative positions:

```text
21–25
```

Validated example:

```text
Spelling Test 24 focus words:
Refreshing
Light
Should
Planned
Undefeated
```

## Current verified word evidence

The active canonical file contains:

```text
Test 6: Delighted
Test 15: Defeated
```

These values must not be replaced, standardized, or corrected without an exact owner-approved source comparison.

The repository contains no tracked evidence for automatic replacement with similarly spelled alternatives.

## Test 25 conflict

The current JSON and validator support Tests 1–24.

Recovered owner context indicates a possible Test 25, but no exact tracked Test 25 word list currently exists.

Therefore:

```text
Test 25 status: OWNER_SOURCE_REQUIRED
```

Until the exact owner-approved list is supplied and reviewed:

- do not invent Test 25;
- do not copy Test 24;
- do not infer words from patterns;
- do not expand the validator to 25;
- do not generate a Test 25 assignment;
- do not report Tests 1–25 as canonical.

## Prefix conflict

Current course configuration and validator use:

```text
SPELL
```

Current owner-approved assignment-title example uses:

```text
RM4: Spelling Test 1
```

These may represent separate concepts:

```text
routing/internal prefix
student-facing assignment title prefix
```

But that distinction is not yet encoded in the current schema.

Status:

```text
OWNER_DECISION_REQUIRED
```

Until resolved:

- preserve `SPELL` in current routing configuration;
- preserve `RM4: Spelling Test 1` as the owner-approved title example;
- do not alter the mapping JSON;
- do not alter the validator;
- do not silently choose one value for both purposes.

## Course sharing

Spelling currently shares the Reading Canvas course:

```text
Canvas course ID: 26442
```

Spelling remains a separate instructional subject.

It may share an agenda surface with Reading under Together Logic.

## Assignment title

Owner-approved current example:

```text
RM4: Spelling Test 1
```

Provisional title pattern:

```text
RM4: Spelling Test {testNumber}
```

This remains authoritative for the context-pack acceptance example, while the routing-prefix conflict remains open.

## Announcement behavior

A Spelling assessment notice may include:

```text
test number
assessment date
25-word cumulative list
five focus words
approved study guidance
```

It must not include:

- invented Test 25 content;
- altered spellings;
- unapproved answer material;
- fake links;
- teacher-only resources.

## Resource requirements

Potential resources include:

```text
approved cumulative word list
student-safe practice material
teacher-approved review material
assessment reminder content
```

Secure answer content must never appear in student-facing artifacts.

## Required reconciliation process

To add Test 25:

1. obtain the exact owner-provided Test 25 source;
2. preserve it as evidence without modifying the canonical file;
3. create a word-by-word comparison;
4. review capitalization, punctuation, apostrophes, and duplicates;
5. review focus-word positions;
6. record owner approval;
7. update JSON;
8. update validator;
9. update this contract;
10. rerun full validation.

## Validation requirements

Current validator expectations:

- Tests 1–24 exist exactly;
- every test has 25 words;
- every test has five focus words;
- Test 24 focus words are positions 21–25;
- `Delighted` and `Defeated` remain unchanged unless approved;
- no Test 25 is treated as canonical;
- prefix conflict remains visible;
- fake links are prohibited.
