# Production Registry Writer Tooling Design Boundary

Last updated: 2026-07-03

```text
Status: writer_tooling_design_boundary_planning_only
Classification: planning-only — no writer scripts, no active --write
Proof: --curriculum-production-registry-next-gate-status
```

## Why Writer Tooling Is Not Active

| Reason | Detail |
| --- | --- |
| Sentinel choice A | `BLOCKED-NO-WRITES.sentinel` remains intact |
| First record only | Exactly one governed manual record exists |
| Owen decision pending | Writer tooling requires explicit separate mission |
| Safety | Automated writes increase batch-import and false-approval risk |

## What a Future Writer Could Theoretically Do (If Approved)

| Capability | Scope constraint |
| --- | --- |
| Append one manual record | Single-record per mission only |
| Validate against field contracts | Before any file mutation |
| Emit diff report | Against pre-write snapshot |
| Dry-run mode | Default first implementation surface |

## What a Future Writer Must Not Do (Even If Approved)

| Blocked | Rationale |
| --- | --- |
| Batch import | Sentinel and governance forbid |
| Auto-promotion from fixtures | Dry-run must not promote |
| Source auto-resolution | Manual labels only |
| Read real curriculum files | Separate blocked mission |
| Remove sentinel without mission | Sentinel handling is explicit gate |
| Student data fields | Absolute prohibition |

## Single-Record-First Rule

Any future writer implementation must default to **one record per explicit Owen-approved mission**. Multi-record writes require a separate mission class — not implied by writer-tooling approval.

## Snapshot / Diff / Restore Requirements

| Step | Requirement |
| --- | --- |
| Pre-write | Mandatory snapshot of current `production-registry.json` |
| Post-write | Validator PASS on new state |
| Diff | Human-readable `records.length` and ID changes |
| Restore | Revert to snapshot or `git revert` on validation FAIL |

## Dry-Run Requirements

1. Dry-run must not mutate `production-registry.json`.
2. Dry-run output must label `planning_only` or `dry_run_only`.
3. PASS on dry-run must not authorize live write.

## Manual Review Requirements

1. Owen reviews worksheet or acceptance checklist before write mission.
2. ChatGPT review recommended before write-tooling implementation prompt.
3. PR diff must show exactly one record change (or tooling-only change for dry-run missions).

## Negative Test Requirements (Future Implementation)

| Test | Expectation |
| --- | --- |
| No `--write` handler until mission | chief-of-staff grep negative |
| No writer script files | `scripts/curriculum-*-write*.sh` absent |
| Dry-run does not mutate registry | cmp before/after |
| Batch second record rejected | validator FAIL |

## Sentinel Handling Choices (Future — Not Decided)

| Choice | Meaning |
| --- | --- |
| A (current) | Keep sentinel; manual PR edits only |
| B (future mission) | Remove sentinel only with explicit audit mission |

**Current state:** Choice A. Decision packet does not approve Choice B.

## Owen Approval Before Implementation

```text
Explicit write-tooling mission prompt required.
PASS on planning docs does not authorize --write or writer scripts.
```

## Non-Activation

This document is planning-only. No writer scripts. No active `--write`.
