# Reading Test and Checkout Rules

Status: owner-confirmed.
Valid Checkouts are 1-13 only. Reading Test 14 has no Checkout.

## Canonical terminology

Use one word: `Checkout`.

Titles:

- `RM4: Reading Test {number}`
- `RM4: Checkout {number}`

## Reading Test

Defaults:

- Assignment group: Tests/Assessments
- Points: 100
- Grade display: Percentage
- Submission type: On Paper
- Assigned to: All Students
- Due date: teacher-selected assessment date
- Due time: 12:00 AM unless later superseded by an approved global rule

Reading Test N covers ten lessons:

- ending lesson = N × 10
- starting lesson = ending lesson − 9

Examples:

- Test 1: Lessons 1–10
- Test 2: Lessons 11–20
- Test 10: Lessons 91–100

Description pattern:

`Review Lessons {start}-{end}, including vocabulary and story details. Use the attached study guide to help you review.`

Attach the student-facing study guide when available.

Do not expose teacher-only answer documents unless explicitly approved for student use.

## Checkout

Defaults:

- Assignment group: Checkouts
- Points: 100
- Grade display: Percentage
- Submission type: On Paper
- Assigned to: All Students
- Due date: same date as the linked Reading Test unless overridden
- Due time: 12:00 AM unless later superseded by an approved global rule

Description structure:

- Target Fluency Goal
- Tracking and tapping
- Read out loud every day
- Practice passage resolved from the Checkout passage map

The system must never invent a passage, WPM target, or maximum-error value.

## Checkout resources

A Checkout does not have:

- a Checkout worksheet
- a Checkout study guide
- a blank Checkout document
- a completed Checkout document
- a dedicated Checkout resource link

Missing Checkout study-guide resources must not create validation warnings.

## Assessment family

A Reading Test and its Checkout form one assessment family.

Example teacher input:

`Reading Test 2 and Checkout 2 on Tuesday, July 21`

Expected records:

1. `RM4: Reading Test 2`
2. `RM4: Checkout 2`
3. One parent announcement
4. Reading Test study-guide references when available

## Parent announcement

Title pattern:

`Reading Test and Checkout - {date}`

Body includes:

1. Greeting
2. Assessment date
3. Reading Test number
4. Lessons covered
5. Vocabulary and story-details reminder
6. Study-guide attachment or verified link
7. Checkout number
8. Fluency target
9. Maximum-error target
10. Tracking-and-tapping reminder
11. Daily read-aloud reminder
12. Checkout passage
13. Closing
14. `Mr. Reagan`

## Weekly agenda reminder

When the assessment date is within the next 10 calendar days:

- show one bullet for the Reading Test and Checkout
- place verified Reading Test study-guide links directly underneath
- include concise Checkout fluency-practice information
- do not create a Checkout study-guide link

## Confirmed fluency example

Checkout 2:

- 100 words per minute
- 2 or fewer errors
- tracking and tapping
- read out loud every day

Confirmed fluency bands:

- Checkouts 1-7: 100 words per minute, 2 or fewer errors
- Checkouts 8-10: 115 words per minute, 2 or fewer errors
- Checkouts 11-13: 130 words per minute, 2 or fewer errors

Checkout 14 does not exist.
