# Curriculum Builder — Production Registry Governance Foundation

Last updated: 2026-07-02

```text
Status: documentation/status only
Program: CB-PROD-GOV — Governance-First Production Registry Foundation
Closure status: complete_cb_prod_gov_foundation
Production registry writes: blocked
Active --write: blocked
Real metadata intake: blocked
Implementation: governance scaffolding only — not write mission
```

## Purpose

Canonical closure index for the **governance-first production registry foundation** described in planning brief § I and the Owen review packet. This foundation prepares docs, status proof, candidate path skeleton, and guardrails **without** authorizing production writes or real metadata intake.

**PASS on governance status does not authorize writes.** Owen § J checklist: all 11 items decided 2026-07-02; items 3 and 4 approved with manual-only boundaries; metadata intake and registry mutation remain blocked.

## Definition of Done

| # | Deliverable | Status |
| --- | --- | --- |
| 1 | Governance foundation closure (this doc) | complete |
| 2 | Path options (Owen decision pending) | `docs/curriculum-builder-production-registry-path-options.md` |
| 3 | Manual-only candidate path skeleton | `assistant/curriculum-builder/registry/candidate-v0-2-production/` |
| 4 | Review state model planning | `docs/curriculum-builder-production-registry-review-state-model.md` |
| 5 | Audit/rollback planning stub | `docs/curriculum-builder-production-registry-audit-rollback-planning-stub.md` |
| 6 | Local-first storage reference model | `docs/curriculum-builder-local-first-storage-reference-model.md` |
| 7 | Governance status script | `scripts/curriculum-builder-production-registry-governance-status.sh` |
| 8 | `--curriculum-production-registry-governance-status` | `bin/chief-of-staff` |
| 9 | Guardrail tests | `tests/curriculum-builder-production-registry-governance-status-test.sh` |
| 10 | Promotion prevention cross-link | `docs/curriculum-builder-registry-dry-run-fixture-promotion-planning-spec.md` |
| 11 | Owen decision worksheet | `docs/curriculum-builder-production-registry-owen-decision-worksheet.md` |
| 12 | Post-decision implementation map | `docs/curriculum-builder-production-registry-post-decision-implementation-map.md` |
| 13 | Metadata pilot planning boundary | `docs/curriculum-builder-metadata-pilot-planning-boundary.md` |
| 14 | Manual metadata boundary | `docs/curriculum-builder-manual-metadata-boundary.md` |
| 15 | Write mission preflight expansion | `docs/proposals/backlog/production-registry-write-mission.md` |
| 16 | Phase 2 preflight foundation | `docs/curriculum-builder-production-registry-phase-2-preflight.md` |
| 17 | Metadata-boundary refinement | `docs/curriculum-builder-production-registry-manual-metadata-field-contract.md` |

## Decision Readiness (Post–PR #218)

| Artifact | Role |
| --- | --- |
| Decision worksheet | Owen-facing checklist workflow |
| Post-decision map | Phase routing after Owen updates tracker |
| Metadata pilot boundary | Future metadata-only pilot — no intake |

## What This Foundation Authorizes

| Authorized | Not authorized |
| --- | --- |
| Read-only status and docs | Production registry writes |
| Blocked-write proof | Active `--write` |
| Candidate path skeleton (empty/blocked) | Real metadata records |
| Planning stubs for audit/rollback/review | Real curriculum intake |
| Negative guardrail tests | Auto-promotion from fixtures |
| Cross-links to Owen review packet | Integrations/API/OAuth/network |

## Relationship to Owen § J Checklist

Path and namespace recorded 2026-07-02: items 1 and 10 **approved**. Write behavior approved in principle 2026-07-02: item 2 **approved** (Phase 2 preflight complete). Metadata boundaries approved 2026-07-02: items 3 and 4 **approved** (manual-only; intake blocked). Governance affirmation batch recorded 2026-07-02: items 5, 6, 7, 8, 9, 11 **approved**.

## Orchestrated Proof

```bash
bin/chief-of-staff --curriculum-production-registry-governance-status
bash scripts/curriculum-builder-production-registry-governance-status.sh
bash tests/curriculum-builder-production-registry-governance-status-test.sh
bin/chief-of-staff --curriculum-registry-lane-status
```

## Recommended Next Mission (After Owen Decides)

1. Owen completes review packet § 7 decision table
2. Owen approves governance-first PR scope (checklist item 11) — **done**
3. Owen chooses production registry path (item 1) and ID namespace (item 10) — **done 2026-07-02**
4. Owen decides write behavior (item 2) — **done 2026-07-02; in principle; Phase 2 preflight eligible**
5. **Separate** Phase 2 preflight mission — docs/status/tests/audit only; no registry mutation
6. **Separate** future mission: governed single-record manual write — after Phase 2 + items 3/4 if real metadata

## Non-Activation

No production writes, `--write`, real intake, generation, APIs, network, scanning, or student-data workflows.
