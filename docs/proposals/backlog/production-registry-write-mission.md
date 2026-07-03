# Production Registry Write Mission — Backlog

Last updated: 2026-07-02

```text
Status: backlog
Classification: future implementation mission — not authorized
Phase 2 preflight: complete
Metadata boundaries: approved (items 3 and 4 — 2026-07-02)
Registry mutation: blocked until separate explicit write mission prompt
```

## Purpose

Backlog pointer for **future** governed production registry mutation missions. Owen § J checklist decisions are **complete**. Metadata/source-reference boundaries are **approved**. Registry mutation remains **blocked**.

## Mission Types (Distinct — Not Bulk Approved)

| Mission type | Status | Authorizes |
| --- | --- | --- |
| Phase 2 preflight | **complete** | Docs/status/tests/audit readiness only |
| Metadata-boundary refinement | **next recommended** | Allowed/blocked field docs, status checks, negative tests |
| Future empty-file mission | **not approved** | Creating `production-registry.json` with `records: []` |
| Future writer / `--write` mission | **not approved** | Write handler or script |
| Metadata pilot execution | **not approved** | Entering real school materials |
| Future governed single-record write | **not approved** | Record mutation; separate explicit prompt |

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
| Real metadata boundary (item 3) | **approved** — manual-only |
| Real source references boundary (item 4) | **approved** — non-resolving labels |
| Metadata-boundary refinement | **not started** — separate prompt |
| Empty-file mission prompt | **not issued** |
| Governed write mission prompt | **not issued** |

## Approved Future Production Surface (Not Created)

| Field | Value |
| --- | --- |
| Production path | `assistant/curriculum-builder/registry/v0-2/production-registry.json` |
| ID namespace | `resource-*` |
| Writable | **Blocked** |
| Create file | **Blocked** |
| Remove sentinel | **Blocked** |
| Metadata intake | **Blocked** — boundary approved; pilot execution not authorized |
| Source resolution | **Blocked** — non-resolving labels only when write mission approved |

## Next Gates

| Gate | Status |
| --- | --- |
| Metadata-boundary refinement docs/status/tests | **recommended next** |
| Empty-file mission | Separate explicit prompt after refinement |
| Governed single-record write | Separate explicit prompt after empty file |
| Writer / `--write` | Separate explicit prompt |

## Preflight Checklist (Write Mission — Future)

| # | Gate | Owner | Status |
| ---: | --- | --- | --- |
| 1 | Owen updated checklist tracker rows | Owen | **done** — all 11 items |
| 2 | ChatGPT review of implementation prompt | Owen + ChatGPT | pending |
| 3 | Production path recorded | Owen | **done** |
| 4 | ID namespace recorded | Owen | **done** |
| 5 | `BLOCKED-NO-WRITES.sentinel` present until write mission removes it | Repo | yes |
| 6 | Audit/rollback preflight accepted | Owen | **done** — Phase 2 |
| 7 | Review-state model accepted | Owen | **approved** |
| 8 | No `--curriculum-registry-write` handler | CI | yes |
| 9 | Dry-run validator passes on fake candidates | CI | yes |
| 10 | Items 3 and 4 boundaries recorded | Owen | **done** |
| 11 | Item 2 write behavior approved | Owen | **approved in principle** |
| 12 | Phase 2 preflight complete | Repo | **done** |
| 13 | Metadata-boundary refinement complete | Repo | pending |

## Future PR Boundaries (Write Mission)

**In scope (smallest possible):**

- Governed single-record manual write with pre-write snapshot
- Post-write validator + diff proof
- Rollback procedure execution on failure
- Fields per `docs/curriculum-builder-production-registry-metadata-source-boundaries.md`

**Explicitly out of scope:**

- Batch import, auto-promotion, global `--write`
- Network, OAuth, scanning, source auto-resolution
- Real curriculum file reading, copied content
- Metadata pilot execution without separate mission
- Removing sentinel without Owen-approved mission

## Related

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-production-registry-metadata-source-boundaries.md` | Items 3 and 4 boundaries |
| `docs/curriculum-builder-production-registry-phase-2-preflight.md` | Phase 2 closure |
| `docs/curriculum-builder-production-registry-audit-rollback-preflight.md` | Audit model |
| `docs/curriculum-builder-production-registry-snapshot-diff-restore-readiness.md` | Snapshot readiness |

## Non-Activation

This backlog does not authorize registry mutation, metadata pilot execution, or source resolution.
