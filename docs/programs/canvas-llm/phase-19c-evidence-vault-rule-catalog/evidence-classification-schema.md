# Evidence Classification Schema

## Status

Preview-only schema specification.

## Classification Labels

Use these labels from Phase 19B:

```text
APPROVED_PATTERN
WORKFLOW_EVIDENCE
LEGACY_FORMAT_ONLY
UNKNOWN_NEEDS_REVIEW
```

## APPROVED_PATTERN

Meaning:

```text
Approved by Owen or current governance as a future-safe rule/pattern.
```

Allowed future use:

- rule catalog entry
- preview builder requirement
- diagnostic check
- validation gate

Not allowed:

- direct Canvas write
- silent mutation
- unreviewed generation outside a preview

## WORKFLOW_EVIDENCE

Meaning:

```text
Evidence of prior workflow or legacy behavior that appears useful but is not automatically canonical.
```

Allowed future use:

- candidate rule
- review queue
- conflict analysis
- migration mapping

Not allowed:

- canonical rule without review
- write gate input without approval

## LEGACY_FORMAT_ONLY

Meaning:

```text
Old format useful for aliasing, migration, search, or recognition, but not approved for future generation.
```

Allowed future use:

- legacy alias table
- historical matching
- migration notes
- diagnostic explanation

Not allowed:

- new output format
- canonical future title

## UNKNOWN_NEEDS_REVIEW

Meaning:

```text
Evidence, behavior, or rule candidate that needs Owen/school review.
```

Allowed future use:

- unanswered question
- review queue
- diagnostic warning

Not allowed:

- implementation
- generation
- Canvas write
- automated decision

## Classification Promotion

Promotion path:

```text
UNKNOWN_NEEDS_REVIEW
  → WORKFLOW_EVIDENCE
  → APPROVED_PATTERN
```

Demotion path:

```text
APPROVED_PATTERN
  → superseded or rejected
```

Promotion requires:

- source authority check
- conflict check
- privacy/safety check
- Owen approval when classroom-specific
- regression-friendly status update

## Conflict Handling

If two evidence records conflict:

1. Do not pick automatically.
2. Record both records.
3. Link them through `conflict_refs`.
4. Mark resulting rule candidate as `UNKNOWN_NEEDS_REVIEW`.
5. Surface it in diagnostics/review queue.

## Boundary

Classification does not authorize Canvas writes.
