# Production Registry Write Mission — Backlog

Last updated: 2026-07-02

```text
Status: backlog
Classification: future implementation mission — not authorized
Blocked until: Owen § J checklist items 1, 2, 6, 7, 10, 11 approved + governance foundation merged
```

## Purpose

Backlog pointer for the **governed single-record manual write** mission (planning brief § I second PR). CB-PROD-GOV governance foundation is **complete**. This mission remains **blocked** until Owen approves prerequisites.

## Prerequisites

| Prerequisite | Status |
| --- | --- |
| Governance foundation (CB-PROD-GOV) | **complete** — `docs/curriculum-builder-production-registry-governance-foundation.md` |
| Owen path decision (item 1) | pending |
| Write behavior allowed (item 2) | pending |
| Rollback accepted (item 6) | pending |
| Review states accepted (item 7) | pending |
| ID namespace chosen (item 10) | pending |
| Governance-first PR scope (item 11) | pending — foundation delivered; write still blocked |

## Preflight Checklist (Before Any Write Mission Prompt)

| # | Gate | Owner |
| ---: | --- | --- |
| 1 | Owen updated checklist tracker rows (not worksheet alone) | Owen |
| 2 | ChatGPT review of implementation prompt complete | Owen + ChatGPT |
| 3 | Production path recorded in path-options doc | Owen |
| 4 | ID namespace recorded | Owen |
| 5 | `BLOCKED-NO-WRITES.sentinel` still present until write mission explicitly removes it | Repo |
| 6 | Audit/rollback stub accepted | Owen |
| 7 | Review-state model accepted | Owen |
| 8 | Negative tests pass: no `--curriculum-registry-write` handler | CI |
| 9 | Dry-run validator passes on fake candidates only | CI |
| 10 | No real metadata without items 3–5 approval | Policy |

## Future PR Boundaries (Write Mission)

**In scope (smallest possible):**

- Governed single-record manual write with pre-write snapshot
- Post-write validator + diff proof
- Rollback procedure execution on failure
- Read-only status proving write occurred under audit rules

**Explicitly out of scope:**

- Batch import
- Auto-promotion from dry-run or v0.2 fixtures
- Active global `--write` without per-record review
- Network, OAuth, scanning
- Real metadata without separate metadata approval
- Removing sentinel without Owen-approved mission

## Future Tests List (Planning)

| Test | Purpose |
| --- | --- |
| Snapshot created before write | Audit requirement |
| Rollback restores prior state | Audit requirement |
| Write rejected when review_state ≠ approved | Gate model |
| No write when sentinel present | Blocked path |
| No promotion from `samples/` to production | Authority map |

## Dry-Run-Only Validation Plan

Until write mission: only `scripts/curriculum-builder-registry-v0-2-dry-run.sh` on fake candidates in `samples/registry-v0-2-dry-run/`. PASS does not authorize promotion.

## Escalation Gates

Stop write mission if:

- Student-data fields requested
- Integration required for source resolution
- Batch import requested
- PASS/WARN/FAIL semantics would need weakening

## Related

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-production-registry-owen-decision-worksheet.md` | Owen decisions |
| `docs/curriculum-builder-production-registry-post-decision-implementation-map.md` | Phase routing |
| `docs/proposals/blocked/production-registry-real-metadata-intake.md` | Metadata intake blocked |

## Non-Activation

This backlog entry does not authorize implementation.
