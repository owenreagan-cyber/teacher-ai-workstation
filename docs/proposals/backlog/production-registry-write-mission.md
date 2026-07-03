# Production Registry Write Mission — Backlog

Last updated: 2026-07-02

```text
Status: backlog
Classification: future implementation mission — not authorized
Phase 2 preflight: eligible via separate explicit mission — not authorized by item 2 tracker sync alone
Registry mutation: blocked until Phase 2 complete + explicit write mission prompt
```

## Purpose

Backlog pointer for the **governed single-record manual write** mission (planning brief § I second PR) and **Phase 2 preflight** routing. CB-PROD-GOV governance foundation is **complete**. Path, namespace, and write behavior in principle are **recorded**. Registry mutation remains **blocked** until Phase 2 preflight completes and Owen issues a separate write mission prompt.

## Prerequisites

| Prerequisite | Status |
| --- | --- |
| Governance foundation (CB-PROD-GOV) | **complete** |
| Owen path decision (item 1) | **approved** — `assistant/curriculum-builder/registry/v0-2/production-registry.json` |
| Write behavior allowed (item 2) | **approved in principle** — Phase 2 preflight eligible; mutation blocked |
| Rollback accepted (item 6) | **approved** |
| Review states accepted (item 7) | **approved** |
| ID namespace chosen (item 10) | **approved** — `resource-*` |
| Governance-first PR scope (item 11) | **approved** |
| Phase 2 preflight complete | **not started** |
| Real metadata (item 3) | **deferred** |
| Real source references (item 4) | **deferred** |

## Approved Future Production Surface (Not Created)

| Field | Value |
| --- | --- |
| Production path | `assistant/curriculum-builder/registry/v0-2/production-registry.json` |
| ID namespace | `resource-*` (e.g. `resource-sm5-textbook-001`) |
| Writable | **Blocked** — no Phase 2 preflight or write mission yet |
| Create file | **Blocked** |
| Remove sentinel | **Blocked** |
| Real metadata | **Blocked** — item 3 deferred |
| Real source references | **Blocked** — item 4 deferred |

## Phase 2 Preflight (Eligible — Separate Mission Required)

**Not authorized by item 2 tracker sync alone.** Owen must issue an explicit Phase 2 preflight mission prompt.

| In scope | Out of scope |
| --- | --- |
| Audit/rollback test expansion | `--write` handler |
| Negative guardrail tests | `production-registry.json` creation |
| Dry-run hardening on fake candidates | `resource-*` records |
| Status proof mutation remains blocked | Sentinel removal |

## Preflight Checklist (Before Any Write Mission Prompt)

| # | Gate | Owner | Status |
| ---: | --- | --- | --- |
| 1 | Owen updated checklist tracker rows (not worksheet alone) | Owen | **done** — item 2 |
| 2 | ChatGPT review of implementation prompt complete | Owen + ChatGPT | pending |
| 3 | Production path recorded in path-options doc | Owen | **done** — Option B |
| 4 | ID namespace recorded | Owen | **done** — `resource-*` |
| 5 | `BLOCKED-NO-WRITES.sentinel` still present until write mission explicitly removes it | Repo | yes |
| 6 | Audit/rollback stub accepted | Owen | **approved** |
| 7 | Review-state model accepted | Owen | **approved** |
| 8 | Negative tests pass: no `--curriculum-registry-write` handler | CI | yes |
| 9 | Dry-run validator passes on fake candidates only | CI | yes |
| 10 | No real metadata without items 3–5 approval | Policy | blocked |
| 11 | Item 2 write behavior explicitly approved | Owen | **approved in principle** |
| 12 | Phase 2 preflight mission complete | Owen + Cursor | **not started** |

## Future PR Boundaries (Write Mission — Phase 3+)

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
- Real metadata without items 3 and 4 approval
- Removing sentinel without Owen-approved mission

## Future Tests List (Planning)

| Test | Purpose |
| --- | --- |
| Snapshot created before write | Audit requirement |
| Rollback restores prior state | Audit requirement |
| Write rejected when review_state ≠ approved | Gate model |
| No write when sentinel present | Blocked path |
| No promotion from `samples/` to production | Authority map |
| Production IDs match `resource-*` pattern | Namespace enforcement |

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

This backlog entry does not authorize Phase 2 preflight or registry mutation without a separate explicit mission prompt.
