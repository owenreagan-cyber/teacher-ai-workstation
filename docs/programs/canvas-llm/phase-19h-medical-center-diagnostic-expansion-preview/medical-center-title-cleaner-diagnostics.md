# Medical Center Title Cleaner Diagnostics

## Status

Preview-only diagnostic spec.

## Purpose

The Medical Center checks title-cleaner review packets before any future write-gate action.

## Diagnostic Checks

| check_id | level | condition | message |
| --- | --- | --- | --- |
| MC-TITLE-001 | PASS | canonical title matches approved pattern | Title matches canonical rule. |
| MC-TITLE-002 | PASS | spelling maps to RM4 | Spelling correctly maps to RM4. |
| MC-TITLE-003 | WARN | confidence is medium | Human review recommended before use. |
| MC-TITLE-004 | FAIL | proposed title uses forbidden prefix SP4 or SPELL4 | Spelling title must not output SP4 or SPELL4. |
| MC-TITLE-005 | BLOCKED | ambiguous input has proposed title | Ambiguous input must not produce a final title. |
| MC-TITLE-006 | BLOCKED | needs_review is false for ambiguous title | Ambiguous input must remain review-required. |
| MC-TITLE-007 | BLOCKED | Canvas write requested before write gate approval | Canvas writes remain disabled. |

## Required Blockers

The Medical Center must block:

```text
Canvas API calls
Canvas writes
live Canvas fetches
student data access
raw .local metadata reads
silent Canvas mutation
ambiguous final classification
```

## Relationship To Phase 19F

Phase 19F proves deterministic preview behavior.

Phase 19H defines diagnostic checks for that behavior.

Phase 19H does not write to Canvas.
