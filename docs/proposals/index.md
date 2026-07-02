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
| Registry Authority Map (v0 vs v0.2 fixture vs production) | Curriculum Builder Registry | 2 | high | low | low | none | none | none | proposed | Create docs/status authority map; link from lane closure and boundaries | Level 2 Registry Lane Review 2026-07-02 | 2026-07-02 |
| Aggregate `--curriculum-registry-lane-status` command | Curriculum Builder Registry | 2 | medium | low | low | none | none | none | proposed | Single CLI aggregating CB-IMPL-1–4 status outputs | Level 2 Registry Lane Review 2026-07-02 | 2026-07-02 |
| Dry-run to fixture promotion planning spec | Curriculum Builder Registry | 2 | medium | low | low | none | none | none | proposed | Planning doc only; document blocked promotion path and human gates | Level 2 Registry Lane Review 2026-07-02 | 2026-07-02 |
| A4–A7 schema cross-validation on fake fixtures | Curriculum Builder Registry | 2 | medium | low | medium | none | none | none | proposed | Extend fixture validator to check against canonical contract JSON schemas | Level 2 Registry Lane Review 2026-07-02 | 2026-07-02 |
| Production registry workflow planning brief | Curriculum Builder Registry | 2 | high | medium | medium | possible | possible | future | proposed | ChatGPT + Owen planning brief before any write mission | Level 2 Registry Lane Review 2026-07-02 | 2026-07-02 |

Detail: `docs/proposals/curriculum-builder-registry-lane-discovery-review.md`

## Usage

1. Check this table for duplicates before adding a row
2. Prefer final-report Level 1 candidates for lightweight ideas
3. Reserve ledger rows for high-value, clearly connected, safe-to-record ideas
4. Optional detail files: `docs/proposals/<slug>.md`

See `docs/proposals/README.md`.
