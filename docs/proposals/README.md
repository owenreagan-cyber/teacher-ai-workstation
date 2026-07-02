# Proposals

Last updated: 2026-07-02

## Purpose

Persistent proposal ledger for Teacher Workstation feature and improvement ideas. Chat history is not the source of truth — `docs/proposals/index.md` is.

## Proposal Lifecycle

States progress from idea to shipped work only with explicit Owen Reagan approval at each gate:

```text
proposed → under_review → approved_for_* → (implementation missions) → implemented
```

Branches: `deferred`, `rejected`, `superseded` — always recorded with reason.

See `docs/cursor-operating-modes-and-approval-gates.md` for approval levels and lifecycle definitions.

## Unified Ledger Schema

`docs/proposals/index.md` uses columns:

`Candidate`, `Area`, `Level`, `Value`, `Risk`, `Technical Complexity`, `Student-Data Risk`, `Curriculum-Content Risk`, `API/Network Requirement`, `Status`, `Recommended Next Step`, `Source Mission`, `Date`

## Three-Level Discovery Relationship

| Level | When | Ledger |
| --- | --- | --- |
| **1** End-of-Mission Scan | Automatic at end of major missions | Final-report table; ≤3 candidates; optional ledger row |
| **2** End-of-Lane Review | Explicit Owen-approved mission; lane `complete_pending_review` | ≤5 full ledger entries; template: `templates/lane-level-discovery-mission.md` |
| **3** Full-Product Strategy | Explicit mission near full-build completion | Ranked portfolio; no hard cap |

**Discovery is proposal-only.** It does not authorize implementation, prototypes, or runtime behavior.

Authority: `docs/cursor-operating-modes-and-approval-gates.md` § `{#three-level-discovery-governance}`

## Approval Chain

```text
Cursor proposal → ChatGPT review → Owen Reagan approval → scoped implementation prompt → Cursor implementation
```

## Adding a Proposal

1. Check `index.md` for near-duplicates
2. Decide Level 1 final-report vs formal ledger entry
3. Add a row to the ledger table when the idea is high-value and safe to record
4. Optionally add `docs/proposals/<slug>.md` for detail
5. Do not implement until status reaches required approval level

## File Layout

| Path | Purpose |
| --- | --- |
| `docs/proposals/index.md` | Canonical ledger table |
| `docs/proposals/<slug>.md` | Optional detail files (pre-folder reviews) |
| `docs/proposals/lane-reviews/` | Level 2 lane discovery review docs |
| `docs/proposals/ideas/` | Early unclassified ideas |
| `docs/proposals/backlog/` | Deferred safe work detail |
| `docs/proposals/blocked/` | Approval-gated planning detail |
| `docs/proposals/implemented/` | Implemented ledger archive pointers |
| `docs/proposals/templates/` | Level 2 and Level 3 mission templates |
