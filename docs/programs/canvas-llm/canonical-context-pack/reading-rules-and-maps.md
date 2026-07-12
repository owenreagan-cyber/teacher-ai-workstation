# Reading Rules and Maps

## Status

```text
APPROVED
```

## Curriculum

```text
Reading Mastery 4
```

## Canonical sources

```text
config/curriculum/reading/reading-mastery-4/comprehension-location-map.json
config/curriculum/reading/reading-mastery-4/checkout-passage-map.json
scripts/canvas_llm_phase22/validate_canonical_knowledge.py
scripts/canvas_llm_phase22/phase22_workstation.py
```

## Course routing

Current 2026–2027 routing:

```text
Subject: Reading
Canvas course ID: 26442
Canonical prefix: RM4
```

Reading and Spelling currently share this Canvas course and weekly agenda surface while remaining separate instructional subjects.

## Lesson coverage

The comprehension-location map contains exactly:

```text
Lessons 1–140
```

Validated examples:

```text
Lesson 25  → Reader D, page 114
Lesson 140 → Reader E, page 750
```

The complete lesson map remains in JSON.

## Standard lesson assignment

Approved title pattern:

```text
RM4: Lesson {lessonNumber} Workbook and Comprehension
```

Example:

```text
RM4: Lesson 4 Workbook and Comprehension
```

## Comprehension resolution

A Reading lesson may resolve:

```text
reader volume
page
workbook work
comprehension work
lesson number
supporting resources
```

The system must not guess a Reader or page when the map is missing.

## Reading tests

Reading tests are assessment-family records.

Internal fields may include:

```text
assessmentFamilyId
readingTestNumber
writtenTestDate
checkoutNumber
checkoutDate
readingTest
checkout
announcementDraft
sourceCheckoutKey
checkoutStudyGuideAllowed
warnings
```

The exact student-facing Reading Test title remains unresolved.

## Checkout coverage

The canonical Checkout map contains exactly:

```text
Checkouts 1–13
```

No Checkout 14 exists.

Validated fluency examples:

```text
Checkout 1  → 100 WPM / 2 errors
Checkout 7  → 100 WPM / 2 errors
Checkout 8  → 115 WPM / 2 errors
Checkout 10 → 115 WPM / 2 errors
Checkout 11 → 130 WPM / 2 errors
Checkout 13 → 130 WPM / 2 errors
```

## Reading Test 14 exception

Reading Test 14 has no Checkout.

Required behavior:

- do not generate Checkout 14;
- do not create a Checkout 14 warning;
- do not include Checkout 14 in announcements;
- do not request a Checkout 14 resource;
- do not create a Checkout 14 dependency;
- do not create a Checkout 14 assignment.

## Checkout terminology

The canonical source distinguishes historical terminology from current terminology.

The current map and validator are authoritative.

Historical labels must not silently replace canonical Checkout wording.

## Checkout study guides

Checkout study guides are not currently authorized by the canonical assessment-family behavior.

Current field:

```text
checkoutStudyGuideAllowed: false
```

The system must not create one unless a later owner-approved rule changes this.

## Reading announcement content

Assessment notices may include:

```text
assessment date
Reading Test number
covered lesson range
vocabulary review
story-detail review
tracking and tapping
read-aloud practice
Checkout passage
Reader volume
page
```

For Reading Test 14, all Checkout-specific content must be omitted.

## Resource requirements

Potential Reading resources include:

```text
Reader volume
comprehension page
workbook pages
Checkout passage
teacher-approved practice resource
assessment notice resource
```

Required unresolved resources block final publication.

## Together Logic boundary

Reading and Spelling may share:

- Canvas course;
- weekly agenda page;
- some communication surfaces.

They must not be merged into one subject record.

Math remains separate.

The precise shared-page behavior is defined in:

```text
together-logic.md
```

## Validation requirements

The validator must confirm:

- 140 lesson records exist;
- lesson keys cover 1–140 exactly;
- Lesson 25 maps to Reader D, page 114;
- Lesson 140 maps to Reader E, page 750;
- Checkouts 1–13 exist exactly;
- fluency thresholds match canonical records;
- Checkout 14 does not exist;
- Reading Test 14 returns no Checkout;
- Reading Test 14 creates no Checkout warning;
- Reading Test 14 announcements omit Checkout language;
- missing Reader/page mappings block generation;
- fake links are forbidden.
