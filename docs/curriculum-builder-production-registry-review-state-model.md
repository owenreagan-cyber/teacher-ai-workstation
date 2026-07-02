# Production Registry Review State Model (Planning Only)

Last updated: 2026-07-02

```text
Status: planning_only
Classification: future governance model — not implemented in code
Owen checklist item: 7 — Review states (pending)
Implementation: blocked until Owen accepts or revises this model
```

## Purpose

Planning-only review gate model for a future production registry workflow. Mirrors planning brief § D. States are **not** enforced by runtime code today.

## Proposed States

| State | Meaning | May write to production? |
| --- | --- | --- |
| `draft` | Work in progress; not validated | No |
| `candidate` | Submitted for validation | No |
| `validated` | Passed dry-run / schema checks | No |
| `teacher_reviewed` | Owen reviewed metadata; not approved for production | No |
| `approved` | Approved for production write | Only in future governed write mission |
| `rejected` | Rejected; must not write | No |
| `quarantined` | Held for policy/safety review | No |
| `archived` | Retired; retained for audit | No |

## Gate Rule (Planning)

Only records in `approved` state may be written to a future production registry in a separately authorized write mission.

## Relationship to v0 Schema

v0 `registry-schema.json` includes `review_status` / `approval_status` enums. Production workflow must reconcile with canonical schema before any implementation mission.

## Owen Decision

Owen may accept this model, revise states, or defer. Acceptance is recorded in the checklist tracker — not by this doc alone.

## Related Documents

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-production-registry-workflow-planning-brief.md` | § D source |
| `docs/curriculum-builder-production-registry-audit-rollback-planning-stub.md` | Audit pairing |

## Non-Activation

This model does not activate validators, writes, or intake.
