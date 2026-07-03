# Production Registry Write Mission — Backlog

Last updated: 2026-07-02

```text
Status: backlog
Classification: future implementation mission — not authorized
Phase 2 preflight: complete — see docs/curriculum-builder-production-registry-phase-2-preflight.md
Registry mutation: blocked until separate explicit write mission prompt
```

## Purpose

Backlog pointer for **future** governed production registry mutation missions. Phase 2 preflight is **complete**. Registry mutation remains **blocked**.

## Mission Types (Distinct — Not Bulk Approved)

| Mission type | Status | Authorizes |
| --- | --- | --- |
| Phase 2 preflight | **complete** | Docs/status/tests/audit readiness only |
| Future empty-file mission | **not approved** | Creating `production-registry.json` with `records: []` |
| Future writer / `--write` mission | **not approved** | Write handler or script |
| Future real metadata mission | **blocked** — item 3 deferred | Real titles/labels in registry |
| Future source-reference mission | **blocked** — item 4 deferred | Real manual path/URL labels |
| Future governed single-record write | **blocked** | Record mutation; requires items 3/4 if real metadata + separate prompt |

## Prerequisites

| Prerequisite | Status |
| --- | --- |
| Governance foundation (CB-PROD-GOV) | **complete** |
| Owen path decision (item 1) | **approved** |
| Write behavior allowed (item 2) | **approved in principle** |
| Phase 2 preflight | **complete** |
| Rollback accepted (item 6) | **approved** |
| Review states accepted (item 7) | **approved** |
| ID namespace chosen (item 10) | **approved** — `resource-*` |
| Governance-first PR scope (item 11) | **approved** |
| Real metadata (item 3) | **deferred** |
| Real source references (item 4) | **deferred** |
| Phase 3+ write mission prompt | **not issued** |

## Approved Future Production Surface (Not Created)

| Field | Value |
| --- | --- |
| Production path | `assistant/curriculum-builder/registry/v0-2/production-registry.json` |
| ID namespace | `resource-*` |
| Writable | **Blocked** |
| Create file | **Blocked** |
| Remove sentinel | **Blocked** |
| Real metadata | **Blocked** — item 3 deferred |
| Real source references | **Blocked** — item 4 deferred |

## Preflight Checklist (Write Mission — Phase 3+)

| # | Gate | Owner | Status |
| ---: | --- | --- | --- |
| 1 | Owen updated checklist tracker rows | Owen | **done** |
| 2 | ChatGPT review of implementation prompt | Owen + ChatGPT | pending |
| 3 | Production path recorded | Owen | **done** |
| 4 | ID namespace recorded | Owen | **done** |
| 5 | `BLOCKED-NO-WRITES.sentinel` present until write mission removes it | Repo | yes |
| 6 | Audit/rollback preflight accepted | Owen | **done** — Phase 2 |
| 7 | Review-state model accepted | Owen | **approved** |
| 8 | No `--curriculum-registry-write` handler | CI | yes |
| 9 | Dry-run validator passes on fake candidates | CI | yes |
| 10 | No real metadata without items 3–5 approval | Policy | blocked |
| 11 | Item 2 write behavior approved | Owen | **approved in principle** |
| 12 | Phase 2 preflight complete | Repo | **done** |

## Future PR Boundaries (Write Mission — Phase 3+)

**In scope (smallest possible):**

- Governed single-record manual write with pre-write snapshot
- Post-write validator + diff proof
- Rollback procedure execution on failure

**Explicitly out of scope:**

- Batch import, auto-promotion, global `--write`
- Network, OAuth, scanning
- Real metadata without items 3 and 4 approval
- Removing sentinel without Owen-approved mission

## Related

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-production-registry-phase-2-preflight.md` | Phase 2 closure |
| `docs/curriculum-builder-production-registry-audit-rollback-preflight.md` | Audit model |
| `docs/curriculum-builder-production-registry-snapshot-diff-restore-readiness.md` | Snapshot readiness |

## Non-Activation

This backlog does not authorize registry mutation.
