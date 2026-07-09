# Rule Review Workflow

## Status

Preview-only workflow specification.

## Purpose

The Rule Review Workflow defines how evidence becomes an approved rule.

## Workflow

```text
1. Capture evidence
2. Classify evidence
3. Link source authority
4. Detect conflicts
5. Draft rule candidate
6. Review with Owen / applicable school guidance
7. Approve, reject, or mark unknown
8. Add validation requirements
9. Add regression-safe handoff breadcrumbs
10. Only then use in preview/diagnostics
```

## Required Review Gates

A rule cannot become approved unless it has:

- evidence reference
- classification
- source authority level
- conflict review
- privacy review
- blocked actions
- validation requirements

## Owen Approval Required

Owen approval is required for:

- classroom-specific assignment behavior
- grading behavior
- newsletter/family communication behavior
- Friday exceptions
- Reading/Spelling relationship changes
- file operation policy
- any future Canvas write candidate

## Automatic Approval Not Allowed

AI may not approve rules.

Legacy code may not approve rules.

Historical Canvas content may not approve rules.

## Regression Requirement

When a rule changes handoff or phase memory, preserve older historical breadcrumbs required by previous status scripts.

See:

```text
docs/programs/canvas-llm/handoff-regression-rule.md
```

## Boundary

This workflow does not authorize implementation or Canvas writes.
