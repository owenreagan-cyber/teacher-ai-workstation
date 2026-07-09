# Canonical Study Guide Grading Rules

## Status

APPROVED_PATTERN

## Rule

Math Study Guides are preparation/review artifacts.

They must not affect final grade calculation.

## Canonical Settings

```text
points_possible = 0
exclude_from_final_grade = true
Does Not Count Toward Final Grade = checked
```

## Canvas Requirement

When a Study Guide assignment is created in Canvas, the Canvas setting/checkbox equivalent to:

```text
Does Not Count Toward Final Grade
```

must be enabled.

## Purpose

Study Guides support review and preparation.

They are not written assessments and are not fact assessments.

## Placement

Preferred placement:

```text
day before Math Test when possible
```

If day-before placement is impossible, the preview must warn and require human review.

## Legacy Conflict Resolution

Legacy implementations included conflicting behavior:

```text
100 percent / omitted from final
0 points / pass-fail / omitted from final
```

Canonical owner decision:

```text
0 points + Does Not Count Toward Final Grade checked
```

The owner-approved rule overrides legacy behavior.

## Validation Requirements

Future validators must check:

- Study Guide exists for Math Test when required
- Study Guide points are zero
- Study Guide is excluded from final grade
- Study Guide does not route to Written Assessments
- Study Guide does not route to Fact Assessments
