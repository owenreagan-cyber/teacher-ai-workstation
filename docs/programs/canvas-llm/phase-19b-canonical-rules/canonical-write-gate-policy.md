# Canonical Write Gate Policy

## Status

APPROVED_PATTERN for safety model.

## Rule

Canvas writes remain disabled until explicitly approved in a future write-gate phase.

## Required Before Any Canvas Mutation

A future write gate must define:

1. exact smallest operation
2. exact target course
3. exact target object
4. exact preview
5. exact human approval phrase
6. validation status
7. rollback or cleanup expectation
8. stop conditions
9. redaction proof
10. post-action validation proof

## Blocked Until Approved

- Canvas API writes
- page creation
- assignment creation
- announcement creation
- file upload
- file rename
- file move
- file delete
- publish action
- front-page change
- historical-course mutation

## Permanent Restrictions

No write gate may allow:

- student data access unless separately approved
- token exposure
- school Canvas URL commits
- raw `.local` metadata commits
- silent mutation
- unreviewed AI-generated content publishing

## Recommended First Write Candidate

Phase 19B does not approve a first write.

A later phase may evaluate a tiny setup operation such as:

```text
one unpublished module shell in one approved current empty course
```

But that must be separately specified and approved.
