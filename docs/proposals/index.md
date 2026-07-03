# Proposal Ledger

Last updated: 2026-07-02

```text
Status: documentation/status only
Ledger: active
Schema: unified v2 (2026-07-02)
Implementation: none approved by entries in this table alone
```

## Purpose

Canonical index of proposed features and improvements. Cursor must check this ledger before creating near-duplicate proposals.

## Migration Note (2026-07-02)

Ledger schema upgraded to unified columns for Three-Level Discovery Governance. Prior placeholder row `*(none yet)*` under the old `Proposal | Area | Status | Risk | Approval Needed | Last Reviewed | Link` schema had no substantive data and was not migrated. New entries use the schema below.

## Approval Chain

```text
Cursor proposal → ChatGPT review → Owen Reagan approval → scoped implementation prompt → Cursor implementation
```

Discovery alone does not authorize implementation. See `docs/cursor-operating-modes-and-approval-gates.md` § Three-Level Discovery Governance.

## Approved Status Values

`proposed` · `under_review` · `approved_for_planning` · `approved_for_docs_status` · `approved_for_implementation` · `approved_for_runtime` · `approved_for_live_integration` · `deferred` · `rejected` · `superseded` · `implemented`

Rejected, deferred, and superseded entries must remain with enough note/context to avoid rediscovery loops.

## Level 1 / 2 / 3 Discovery

| Level | Name | Output |
| --- | --- | --- |
| 1 | End-of-Mission Discovery Scan | Final-report table; optional ledger entry |
| 2 | End-of-Lane Discovery Review | Lane review; up to 5 ledger entries |
| 3 | Full-Product Discovery Strategy Review | Ranked portfolio |

Templates: `docs/proposals/templates/lane-level-discovery-mission.md`, `docs/proposals/templates/full-product-discovery-mission.md`

## Ledger

| Candidate | Area | Level | Value | Risk | Technical Complexity | Student-Data Risk | Curriculum-Content Risk | API/Network Requirement | Status | Recommended Next Step | Source Mission | Date |
| --------- | ---- | ----- | ----- | ---- | -------------------- | ----------------- | ----------------------- | ----------------------- | ------ | --------------------- | -------------- | ---- |
| Registry Authority Map (v0 vs v0.2 fixture vs production) | Curriculum Builder Registry | 2 | high | low | low | none | none | none | implemented | complete — `docs/curriculum-builder-registry-authority-map.md` | Level 2 Registry Lane Review 2026-07-02 | 2026-07-02 |
| Aggregate `--curriculum-registry-lane-status` command | Curriculum Builder Registry | 2 | medium | low | low | none | none | none | implemented | complete — `bin/chief-of-staff --curriculum-registry-lane-status` | Level 2 Registry Lane Review 2026-07-02 | 2026-07-02 |
| Dry-run to fixture promotion planning spec | Curriculum Builder Registry | 2 | medium | low | low | none | none | none | implemented | complete — `docs/curriculum-builder-registry-dry-run-fixture-promotion-planning-spec.md` | Level 2 CB-REG-HARDEN Review 2026-07-02 | 2026-07-02 |
| A4–A7 schema cross-validation on fake fixtures | Curriculum Builder Registry | 2 | medium | low | medium | none | none | none | implemented | complete — `--curriculum-registry-a4-a7-fixture-schema-status` | Level 2 Registry Lane Review 2026-07-02 | 2026-07-02 |
| Production registry workflow planning brief | Curriculum Builder Registry | 2 | high | medium | medium | possible | possible | future | approved_for_planning | Owen checklist review in planning brief § J before implementation mission | Level 2 Registry Lane Review 2026-07-02 | 2026-07-02 |
| Autonomous Build Engine governance foundation | Cursor / Governance | 2 | high | low | low | none | none | none | implemented | complete — `docs/cursor-autonomous-build-engine.md` | CB-AUTO-GOV mission 2026-07-02 | 2026-07-02 |
| Proposal folder structure (lane-reviews, ideas, backlog, blocked, implemented) | Cursor / Governance | 2 | high | low | low | none | none | none | implemented | complete — `docs/proposals/README.md` § File Layout | ABE Safe Work Sprint 2026-07-02 | 2026-07-02 |
| Safe Work Class H in Autonomous Build Engine governance | Cursor / Governance | 2 | medium | low | low | none | none | none | implemented | complete — `docs/cursor-autonomous-build-engine.md` | ABE Safe Work Sprint 2026-07-02 | 2026-07-02 |
| Aggregate `--governance-lane-status` command | Cursor / Governance | 2 | medium | low | low | none | none | none | implemented | complete — `bin/chief-of-staff --governance-lane-status` | Backlog Implementation Sprint 2026-07-02 | 2026-07-02 |
| Production registry Phase 2 preflight | Curriculum Builder Registry | 2 | high | low | low | none | possible | none | implemented | complete — `--curriculum-production-registry-phase-2-preflight-status`; audit/rollback readiness; no mutation | Production Registry Phase 2 Preflight 2026-07-02 | 2026-07-02 |
| Production registry empty-file shell | Curriculum Builder Registry | 2 | high | low | low | none | possible | none | implemented | complete — empty `production-registry.json`; `--curriculum-production-registry-empty-file-status` | Production Registry Empty-File 2026-07-02 | 2026-07-02 |
| Production registry metadata pilot execution planning | Curriculum Builder Registry | 2 | high | low | low | none | possible | none | implemented | complete — one-record protocol; first record executed | Production Registry Metadata Pilot Planning 2026-07-02 | 2026-07-02 |
| Production registry first governed record | Curriculum Builder Registry | 2 | high | low | low | none | possible | none | implemented | complete — one manual metadata record; `--curriculum-production-registry-first-record-status` | Production Registry First Record 2026-07-03 | 2026-07-03 |
| Production registry metadata boundary refinement | Curriculum Builder Registry | 2 | high | low | low | none | possible | none | implemented | complete — field contracts, guardrails, planning validator; `--curriculum-production-registry-metadata-boundary-status` | Production Registry Metadata Boundary Refinement 2026-07-02 | 2026-07-02 |
| Owen § J production registry checklist tracker | Curriculum Builder Registry | 2 | medium | low | low | none | possible | none | implemented | items 3+4 boundaries approved 2026-07-02 — 11 approved, 0 deferred; `--curriculum-production-registry-owen-checklist-status` | Owen § J Items 3+4 Metadata Boundary Sync 2026-07-02 | 2026-07-02 |
| Owen § J production registry review packet | Curriculum Builder Registry | 2 | high | low | low | none | possible | none | implemented | complete — `docs/curriculum-builder-production-registry-owen-review-packet.md` | Owen Review Packet mission 2026-07-02 | 2026-07-02 |
| Governance-first production registry foundation (CB-PROD-GOV) | Curriculum Builder Registry | 2 | high | low | low | none | possible | none | implemented | complete — `bin/chief-of-staff --curriculum-production-registry-governance-status` | Governance-First Foundation mission 2026-07-02 | 2026-07-02 |
| Owen decision worksheet + post-decision map | Curriculum Builder Registry | 2 | high | low | low | none | possible | none | implemented | complete — decision worksheet + implementation map docs | Post-#218 Mega Run 2026-07-02 | 2026-07-02 |
| Metadata pilot planning boundary (no intake) | Curriculum Builder Registry | 2 | medium | low | low | none | possible | none | implemented | complete — `docs/curriculum-builder-metadata-pilot-planning-boundary.md` | Post-#218 Mega Run 2026-07-02 | 2026-07-02 |
| F1 fake widget/shortcut catalog index | Widget and Shortcut Builder | 2 | medium | low | low | none | none | none | implemented | complete — `docs/widget-shortcut-builder-fake-catalog-index.md` | Master Build Plan Safe Autopilot 2026-07-02 | 2026-07-02 |
| CAL1 fake prototype inventory template | Classroom App Lab | 2 | medium | low | low | none | none | none | implemented | complete — `docs/classroom-app-lab-fake-prototype-inventory-template.md` | Master Build Plan Safe Autopilot 2026-07-02 | 2026-07-02 |
| CAL1 vs G1 lane boundary doc | Classroom App Lab | 2 | medium | low | low | none | none | none | implemented | complete — `docs/classroom-app-lab-vs-lovable-lane-boundary.md` | Master Build Plan Safe Autopilot 2026-07-02 | 2026-07-02 |
| Classroom utility apps external ideas (blocked) | Classroom App Lab | 2 | medium | low | low | possible | none | none | implemented | complete — `docs/proposals/blocked/classroom-utility-apps-external-ideas.md` | Master Build Plan Safe Autopilot 2026-07-02 | 2026-07-02 |
| Dry-run PASS does not authorize promotion banner | Curriculum Builder Registry | 2 | low | low | low | none | none | none | implemented | complete — dry-run status output banner | Master Build Plan Safe Autopilot 2026-07-02 | 2026-07-02 |
| Program B vs full CLI surface map | Chief of Staff | 2 | medium | low | low | none | none | none | implemented | complete — `docs/chief-of-staff-program-b-vs-full-cli-surface-map.md` | Curriculum Source Readiness Sprint 2026-07-02 | 2026-07-02 |
| H+I aggregate read-only lane status command | Workstation Ops | 2 | medium | low | low | none | none | none | implemented | complete — `bin/chief-of-staff --workstation-ops-lane-status` | Backlog Implementation Sprint 2026-07-02 | 2026-07-02 |
| Curriculum Source Readiness fake metadata foundation | Curriculum Builder | 2 | high | low | low | none | none | none | implemented | complete — `bin/chief-of-staff --curriculum-source-readiness-status` | Curriculum Source Readiness Sprint 2026-07-02 | 2026-07-02 |
| External planning input intake map | Cursor / Governance | 2 | medium | low | low | none | none | none | implemented | complete — `docs/proposals/ideas/external-planning-input-intake-map.md` | Curriculum Source Readiness Sprint 2026-07-02 | 2026-07-02 |
| Status-banner hardening across lane status scripts | Cross-cutting | 2 | medium | low | low | none | none | none | implemented | complete — runtime activation / fake-fixture banners in aggregate + registry scripts | Backlog Implementation Sprint 2026-07-02 | 2026-07-02 |
| Lane-review hardening sprint (banners + negative guardrails) | Cross-cutting | 2 | medium | low | low | none | none | none | implemented | complete — `tests/lane-review-hardening-guardrails-test.sh` | Lane-Review Hardening Sprint 2026-07-02 | 2026-07-02 |
| Negative non-mutation guardrail tests | Curriculum Builder Registry | 2 | medium | low | low | none | none | none | implemented | complete — `tests/backlog-non-mutation-guardrails-test.sh` + renderer/retrieval tests | Backlog Implementation Sprint 2026-07-02 | 2026-07-02 |

Detail: `docs/proposals/lane-reviews/README.md` (index); prior registry review: `docs/proposals/curriculum-builder-registry-lane-discovery-review.md`

## Usage

1. Check this table for duplicates before adding a row
2. Prefer final-report Level 1 candidates for lightweight ideas
3. Reserve ledger rows for high-value, clearly connected, safe-to-record ideas
4. Optional detail files: `docs/proposals/<slug>.md`

See `docs/proposals/README.md`.
