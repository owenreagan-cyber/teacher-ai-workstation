# Production Registry Write Mission — Backlog

Last updated: 2026-07-02

```text
Status: backlog
Classification: future implementation mission — not authorized
Phase 2 preflight: complete
Metadata boundaries: approved (items 3 and 4)
Metadata-boundary refinement: complete
Registry mutation: blocked until separate explicit write mission prompt
```

## Purpose

Backlog pointer for **future** governed production registry mutation missions. Metadata-boundary refinement is **complete**. Registry mutation remains **blocked**.

## Mission Types (Distinct — Not Bulk Approved)

| Mission type | Status | Authorizes |
| --- | --- | --- |
| Phase 2 preflight | **complete** | Audit/rollback readiness only |
| Metadata-boundary refinement | **complete** | Field contracts, guardrails, planning validator |
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
| Items 3 and 4 boundaries | **approved** |
| Metadata-boundary refinement | **complete** |
| Rollback accepted (item 6) | **approved** |
| Review states accepted (item 7) | **approved** |
| ID namespace chosen (item 10) | **approved** — `resource-*` |
| Empty-file mission prompt | **not issued** |
| Governed write mission prompt | **not issued** |

## Next Gates

| Gate | Status |
| --- | --- |
| Empty-file mission | Separate explicit prompt — **recommended next** |
| Metadata pilot execution | Separate explicit prompt |
| Governed single-record write | After empty file + separate prompt |
| Writer / `--write` | Separate explicit prompt |

## Approved Future Production Surface (Not Created)

| Field | Value |
| --- | --- |
| Production path | `assistant/curriculum-builder/registry/v0-2/production-registry.json` |
| ID namespace | `resource-*` |
| Writable | **Blocked** |
| Create file | **Blocked** |
| Metadata intake | **Blocked** |
| Source resolution | **Blocked** |

## Preflight Checklist (Future Write Missions)

| # | Gate | Status |
| ---: | --- | --- |
| 1 | Metadata-boundary refinement complete | **done** |
| 2 | Phase 2 preflight complete | **done** |
| 3 | Owen checklist complete | **done** |
| 4 | Empty-file mission | pending |
| 5 | Governed write mission prompt | pending |

## Related

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-production-registry-metadata-source-boundaries.md` | Canonical boundaries |
| `docs/curriculum-builder-production-registry-manual-metadata-field-contract.md` | Allowed fields |
| `docs/curriculum-builder-production-registry-blocked-field-guardrails.md` | Blocked guardrails |
| `docs/curriculum-builder-production-registry-phase-2-preflight.md` | Phase 2 closure |

## Non-Activation

This backlog does not authorize registry mutation.
