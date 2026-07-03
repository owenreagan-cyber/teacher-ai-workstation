# Production Registry Phase 2 Preflight

Last updated: 2026-07-02

```text
Status: phase_2_preflight_complete
Classification: read-only preflight — no registry mutation
Owen checklist: item 2 approved in principle (2026-07-02)
Implementation: preflight docs/status/tests only — no file, no record, no --write
```

## Purpose

Canonical closure for **Phase 2 preflight** — audit/rollback readiness, negative guardrails, and status proof required before any future registry mutation mission.

**PASS on `--curriculum-production-registry-phase-2-preflight-status` does not authorize writes, file creation, or records.**

## Owen § J Checklist State (2026-07-02)

| Item | Status | Relevance to Phase 2 |
| --- | --- | --- |
| 1 Production registry path | approved | Option B — `assistant/curriculum-builder/registry/v0-2/production-registry.json` |
| 2 Write behavior allowed | approved in principle | Manual-only; Phase 2 preflight scope |
| 3 Real curriculum metadata | approved | Manual-only boundary; intake blocked |
| 4 Real source references | approved | Non-resolving labels only; resolution blocked |
| 6 Rollback requirements | approved | Snapshot + diff + restore model |
| 7 Review states | approved | § D gate model |
| 10 ID namespace | approved | `resource-*` |

## Phase 2 Approved Scope

| In scope | Detail |
| --- | --- |
| Preflight foundation doc | This document |
| Audit/rollback preflight spec | `docs/curriculum-builder-production-registry-audit-rollback-preflight.md` |
| Snapshot/diff/restore readiness | `docs/curriculum-builder-production-registry-snapshot-diff-restore-readiness.md` |
| Read-only status command | `--curriculum-production-registry-phase-2-preflight-status` |
| Negative guardrail tests | No mutation, sentinel intact, no writer |
| Write-mission backlog refinement | Preflight vs mutation distinction |

## Phase 2 Blocked Scope

| Blocked | Reason |
| --- | --- |
| Creating `production-registry.json` | Future separate mission |
| Creating `resource-*` records | No write mission; intake not authorized |
| Writer scripts | Phase 3+ only |
| Active `--write` / `--curriculum-registry-write` handler | Manifest-blocked |
| Removing `BLOCKED-NO-WRITES.sentinel` | Explicit write mission only |
| Real metadata intake | Boundary approved; pilot execution blocked |
| Real source references | Boundary approved; resolution blocked |
| Real curriculum file access | Always blocked |
| Integrations, scanning, generation | Constitution |

## Approved Future Production Surface (Not Created)

| Field | Value |
| --- | --- |
| Path | `assistant/curriculum-builder/registry/v0-2/production-registry.json` |
| Namespace | `resource-*` |
| File exists today | **No** |
| Records exist today | **No** |

## Future Mutation Prerequisites

Before any registry file or record mutation:

1. Phase 2 preflight PASS (this phase)
2. Items 3 and 4 decided if real metadata/source references required
3. Separate explicit write or empty-file mission prompt
4. ChatGPT review recommended
5. Snapshot before mutation per audit model
6. Post-write validator + diff proof
7. Rollback procedure ready

## Audit / Rollback Expectations

See `docs/curriculum-builder-production-registry-audit-rollback-preflight.md` and `docs/curriculum-builder-production-registry-snapshot-diff-restore-readiness.md`.

Planning model only — no active snapshot tooling until a future write mission.

## Readiness Gates

| Gate | Proof |
| --- | --- |
| Owen item 2 approved in principle | Checklist tracker row |
| Path + namespace documented | Path options doc |
| Audit/rollback preflight docs exist | This mission |
| Sentinel present | `BLOCKED-NO-WRITES.sentinel` |
| No production file | Negative check |
| No writer handler | CLI/manifest negative test |
| Phase 2 status PASS | `--curriculum-production-registry-phase-2-preflight-status` |

## Required Status Commands

```bash
bin/chief-of-staff --curriculum-production-registry-phase-2-preflight-status
bin/chief-of-staff --curriculum-production-registry-owen-checklist-status
bin/chief-of-staff --curriculum-production-registry-governance-status
```

## Required Tests

```bash
bash tests/curriculum-builder-production-registry-phase-2-preflight-status-test.sh
bash tests/curriculum-builder-production-registry-owen-checklist-status-test.sh
bash tests/curriculum-builder-production-registry-governance-status-test.sh
```

## Escalation Conditions

Stop any future mutation mission if:

- Student-data fields requested
- Real metadata without item 3 approval
- Real source references without item 4 approval
- Batch import requested
- Sentinel removal without explicit mission
- PASS/WARN/FAIL semantics would need weakening

## Related Documents

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-production-registry-post-decision-implementation-map.md` | Phase routing |
| `docs/proposals/backlog/production-registry-write-mission.md` | Future write backlog |
| `docs/curriculum-builder-production-registry-governance-foundation.md` | CB-PROD-GOV |

## Non-Activation

Phase 2 preflight does not create production-registry.json, resource-* records, writer scripts, or --write.
