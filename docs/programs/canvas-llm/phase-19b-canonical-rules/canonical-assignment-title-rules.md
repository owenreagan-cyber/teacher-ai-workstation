# Canonical Assignment Title Rules

## Status

Canonical planning specification.

## Global Rule

Assignment existence must be deterministic.

AI may draft wording only after deterministic rules decide an assignment exists.

AI may not invent assignments.

## Canonical Math Assessment Titles

Math assessment titles:

```text
SM5: Test {number}
SM5: Fact Test {number}
SM5: Study Guide {number}
```

Examples:

```text
SM5: Test 1
SM5: Fact Test 1
SM5: Study Guide 1
```

## Math Test Triple Rule

A Math Test creates:

1. Written Test
2. Fact Test
3. Study Guide

Placement:

- Written Test: test day
- Fact Test: test day
- Study Guide: day before test when possible

## Legacy Alias Examples

Legacy aliases may be recognized for migration/search only:

```text
SM5: Lesson {number} Test
SM5: Test — Lesson {number}
SM5: Study Guide — Lesson {number}
```

## Still-Unresolved Title Rules

Phase 19B does not finalize these until Owen/school review:

- exact Math homework title format
- whether Fact Test number means test number or lesson number in every case
- exact Reading homework title format
- exact Reading Checkout title format
- exact Spelling Test number/lesson endpoint convention
- exact ELA Chapter Checkup assignment/resource behavior
- History/Science assignment exceptions

## Required Future Tables

Before implementation, create reviewed tables for:

- assignment title format by subject and type
- assignment group routing
- due date rules
- grading settings
- alias mapping
- title validator patterns
