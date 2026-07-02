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

*No entries yet. Add rows for high-value ideas only. Level 1 missions may report candidates in final reports without ledger entries.*

## Usage

1. Check this table for duplicates before adding a row
2. Prefer final-report Level 1 candidates for lightweight ideas
3. Reserve ledger rows for high-value, clearly connected, safe-to-record ideas
4. Optional detail files: `docs/proposals/<slug>.md`

See `docs/proposals/README.md`.
