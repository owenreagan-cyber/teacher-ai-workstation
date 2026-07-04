# Production Registry Options — Owen Decision Packet

Last updated: 2026-07-03

```text
Status: decision packet — not Owen approval
Classification: Owen decision prep only — does not implement runtime behavior
Canonical detail: docs/curriculum-builder-production-registry-next-gate-decision-packet.md
Current default posture: Option D — parked state
Production registry writes: blocked
```

## Purpose

Help Owen compare production registry next gates **without** approving writes, writer scripts, or a second record. This packet summarizes Options A–D; the canonical comparison table lives in `docs/curriculum-builder-production-registry-next-gate-decision-packet.md`.

**This packet does not choose an option for Owen. Chief of Staff does not choose options for Owen.**

## Current Parked-State Proof

| Check | State |
| --- | --- |
| Records in production registry | **1** (`resource-math-lesson-108-presentation`) |
| `BLOCKED-NO-WRITES.sentinel` | intact |
| `--curriculum-registry-write` handler | **no** |
| Writer scripts | **no** |
| Recommended default | **Option D — parked** |

## Option Comparison (Summary)

### Option A — Writer / `--write` Tooling Foundation

| Dimension | Detail |
| --- | --- |
| Would allow (if Owen approves separate mission) | Design/read-only dry-run for governed write mechanics |
| Would not allow | Batch import, auto-promotion, sentinel removal, live writes without mission |
| Risk | **High** — scope creep toward bulk writes |
| Validation if approved | Negative tests, dry-run only first, dashboard + validate-all |
| Follow-on mission | "Production Registry Write Dry-Run Design Mission" |
| Remains blocked until | Explicit Owen write-tooling mission |

### Option B — Second Governed Production Record

| Dimension | Detail |
| --- | --- |
| Would allow (if Owen approves) | One additional `resource-*` record via governed PR edit |
| Would not allow | Writer automation, real curriculum reads, copied content |
| Risk | **Medium** — bounded if one-record-at-a-time |
| Validation if approved | First-record validator PASS; snapshot before write |
| Follow-on mission | "Governed Second Production Record Mission" |
| Remains blocked until | Completed worksheet + explicit write mission |

### Option C — Metadata Pilot Expansion Planning

| Dimension | Detail |
| --- | --- |
| Would allow (if Owen approves) | Expanded pilot scope **planning** for metadata fields |
| Would not allow | Parser/validator activation, real curriculum binding |
| Risk | **Medium** — planning creep into schema activation |
| Validation if approved | Planning status only; schema missions separate |
| Follow-on mission | "Metadata Pilot Expansion Planning Mission" |
| Remains blocked until | Owen scope decision |

### Option D — Parked State (Current Default)

| Dimension | Detail |
| --- | --- |
| Allows | Continue docs/status lanes; maintain 1 record + sentinel |
| Does not allow | Any production registry mutation |
| Risk | **Low** — no write surface |
| Validation | `--curriculum-production-registry-next-gate-status` PASS |
| Follow-on mission | Safe docs/status missions (e.g. decision packets, coherence) |
| Owen decision | **None required** to maintain parked state |

## What PASS Does Not Mean

- Does **not** approve Option A, B, or C
- Does **not** authorize `--write` or writer scripts
- Does **not** imply second record approval
- Does **not** implement runtime behavior

## Blocked Runtime / Product Writes

```text
production registry writes
second production registry record
active --write
writer scripts
batch import / auto-promotion
real curriculum file access
student data
```

## Owen Decision Required

Owen must explicitly choose A, B, C, or affirm D before any registry mutation mission proceeds.
