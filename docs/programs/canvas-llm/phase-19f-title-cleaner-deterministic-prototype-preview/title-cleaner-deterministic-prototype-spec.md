# Title Cleaner Deterministic Prototype Preview Spec

## Status

Preview-only prototype spec.

## Purpose

Create a deterministic local prototype that reads committed Phase 19D fixture examples and produces preview-only normalization decisions.

The prototype must not read Canvas, write Canvas, or mutate any files except its generated report during this phase.

## Required Prototype Behavior

The prototype must classify committed fixture rows into one of these statuses:

```text
normalized
needs_review
```

The prototype must produce canonical outputs for approved fixture examples:

```text
SM5: Test {number}
SM5: Fact Test {number}
SM5: Study Guide {number}
ELA4: Test {number}
RM4: Test {number}
RM4: Spelling Test {number}
```

The prototype must preserve the detected number.

The prototype must keep ambiguous inputs review-required.

## Required Fixture Behaviors

The prototype must prove:

- `SM5 Test 1` normalizes to `SM5: Test 1`
- `SM 5: Test 1` normalizes to `SM5: Test 1`
- `SM5 Fact Test 2` normalizes to `SM5: Fact Test 2`
- `SM5 Study Guide 3` normalizes to `SM5: Study Guide 3`
- `ELA4 Test 4` normalizes to `ELA4: Test 4`
- `RM4 Test 5` normalizes to `RM4: Test 5`
- `Spelling Test 6` normalizes to `RM4: Spelling Test 6`
- `SP4 Spelling Test 6` normalizes to `RM4: Spelling Test 6`
- `Test 7` remains `needs_review`

## Non-Goals

Phase 19F does not:

- normalize live Canvas titles
- write corrected titles to Canvas
- classify ambiguous Canvas data
- create pages
- create assignments
- create announcements
- move files
- rename files
- implement UI
- create a database
