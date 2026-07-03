# Production Registry Next-Gate Decision Packet

Last updated: 2026-07-03

```text
Status: next_gate_decision_packet_complete
Classification: Owen decision prep only — no gate approved
Proof: --curriculum-production-registry-next-gate-status
Baseline: first record + post-first-record hardening complete
```

## Purpose

Help Owen choose the next production registry gate **without** implementing any blocked gate. This packet compares four options, documents risks, and states exact approval required before any implementation prompt.

## What Has Been Safely Built

| Deliverable | Proof |
| --- | --- |
| First governed manual metadata record | `resource-math-lesson-108-presentation` |
| Pre-write empty-shell snapshot | `production-registry-20260703T042100Z-pre-write.json` |
| Sentinel choice A (intact) | `BLOCKED-NO-WRITES.sentinel` |
| First-record validator + negative fixtures | `--curriculum-production-registry-first-record-status` |
| Sentinel semantics + next-gate classification | planning docs |
| Post-first-record hardening | PR #232 |

## What Remains Blocked

| Gate | Status |
| --- | --- |
| Writer scripts | blocked |
| Active `--write` | blocked |
| Second production record | blocked |
| Batch import / auto-promotion | blocked |
| Metadata pilot expansion beyond first record | blocked |
| Real curriculum file access | blocked |
| Source auto-resolution | blocked |
| Integrations | blocked |

## Option Comparison

### Option A — Writer / `--write` Tooling Design

| Dimension | Detail |
| --- | --- |
| Purpose | Design (not implement) repeatable governed write mechanics |
| Teacher workflow value | Faster future record adds **after** Owen approves each write mission |
| Would enable | Snapshot-before-write, diff-after-write, restore drills, dry-run validation |
| Must not enable | Batch import, auto-promotion, source auto-resolution, sentinel removal without mission |
| Owen approval required | Explicit write-tooling mission + ChatGPT review recommended |
| Preflight docs | `writer-tooling-design-boundary.md`, audit/rollback preflight, sentinel semantics |
| Tests required before implementation | Negative tests, dry-run only first, no live write without mission |
| Rollback model | Pre-write snapshot mandatory; git revert fallback |
| Status updates | New write-tooling status (future); sentinel handling decision |
| Risk level | **High** — easiest path to accidental bulk writes if scope creeps |
| Blocked boundaries | No implementation in decision-prep mission |
| Recommended PR size | Small design doc first; implementation in separate mission(s) |
| Safe next prompt shape | "Implement read-only write dry-run validator only" before any active `--write` |

### Option B — Second-Record Worksheet Flow

| Dimension | Detail |
| --- | --- |
| Purpose | Prepare Owen manual metadata for one additional `resource-*` record |
| Teacher workflow value | Catalog a second classroom resource when Owen has a concrete need |
| Would enable | One more governed PR edit (same pattern as first record) |
| Must not enable | Writer tooling, batch import, real curriculum reads, copied content |
| Owen approval required | Explicit second-record write mission + completed worksheet + acceptance review |
| Preflight docs | `second-record-worksheet-plan.md`, field contracts, acceptance criteria |
| Tests required before implementation | First-record validator still PASS; second-record negative tests extended |
| Rollback model | Snapshot with `records` count 1 before write; restore to one-record state |
| Status updates | Second-record status (future) or extend first-record checks |
| Risk level | **Medium** — bounded if one-record-at-a-time discipline holds |
| Blocked boundaries | Worksheet is blank template only until mission |
| Recommended PR size | Single-record PR edit only (mirror first-record mission) |
| Safe next prompt shape | "Governed single-record write for worksheet ID X" with Owen-provided metadata |

### Option C — Metadata Pilot Expansion Planning

| Dimension | Detail |
| --- | --- |
| Purpose | Plan protocol for additional pilot records beyond the first |
| Teacher workflow value | Low immediate value; mostly process rehearsal |
| Would enable | Documentation only in this phase |
| Must not enable | Second record, writer tooling, real curriculum access |
| Owen approval required | Explicit pilot-expansion planning or execution mission |
| Preflight docs | Extend metadata pilot execution plan |
| Tests required | Planning-only status; no new production records |
| Rollback model | N/A for planning-only |
| Risk level | **Medium** — can blur into de facto second-record approval |
| Blocked boundaries | No expansion execution without separate write mission |
| Recommended PR size | Docs/status only |
| Safe next prompt shape | "Metadata pilot expansion planning doc only" |

### Option D — Parked State (No Next Registry Work)

| Dimension | Detail |
| --- | --- |
| Purpose | Keep first record as proof-of-concept; shift effort to other lanes |
| Teacher workflow value | **Highest safety** — avoids registry complexity until classroom need is clear |
| Would enable | Continued read-only monitoring via existing status commands |
| Must not enable | Any registry mutation |
| Owen approval required | None for parking; re-open when classroom need arises |
| Preflight docs | This packet + parked-state section below |
| Tests required | Existing first-record + next-gate status PASS |
| Rollback model | N/A |
| Risk level | **Lowest** |
| Blocked boundaries | All write gates remain blocked |
| Recommended PR size | None until Owen chooses A/B/C |
| Safe next prompt shape | N/A — monitor with `--curriculum-production-registry-next-gate-status` |

## Parked State (Option D Detail)

```text
first record remains as proof of concept
no writer tooling
no second record
no integration
no runtime behavior
status scripts continue to monitor safety
next work can shift to another Teacher AI Workstation lane
parked_state_allowed
```

Parking is a **valid and recommended default** until Owen has a concrete second resource to catalog or a proven need for write automation.

## Risk Matrix

| Option | Safety | Classroom utility now | Implementation complexity | False-approval risk |
| --- | --- | --- | --- | --- |
| A Writer tooling | Low | Low until records exist | High | High |
| B Second record | Medium | Medium (if resource ready) | Low (PR edit pattern) | Medium |
| C Pilot expansion planning | Medium | Low | Low | Medium |
| D Parked | **High** | Depends on other lanes | **None** | **Low** |

## Recommendation for Owen's Classroom Workflow

**Recommended default: Option D (parked)** unless Owen already has a specific second resource ready to catalog.

**If Owen has a ready second resource:** Option B (second-record worksheet → governed PR edit) is safer and more useful than Option A, because it reuses the proven first-record pattern without introducing write automation.

**Option A** should wait until Owen expects multiple future records and wants repeatable snapshot/diff/restore mechanics — still as separate approved missions, never bulk-approved.

## Exact Owen Approval Required Before Implementation

| Gate | Owen must explicitly approve |
| --- | --- |
| Writer / `--write` tooling | Separate write-tooling mission; sentinel handling choice; no batch import |
| Second record | Separate governed single-record write mission; completed worksheet; acceptance criteria PASS |
| Pilot expansion execution | Separate mission distinct from planning |
| Un-parking | Choosing A, B, or C in writing (worksheet, mission prompt, or checklist update) |

## Related Documents

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-production-registry-writer-tooling-design-boundary.md` | Option A planning boundary |
| `docs/curriculum-builder-production-registry-second-record-worksheet-plan.md` | Option B worksheet plan |
| `docs/curriculum-builder-production-registry-next-gate-classification.md` | Blocked gate summary |
| `docs/curriculum-builder-production-registry-sentinel-semantics.md` | Sentinel choice A |

## Non-Activation

This packet does not approve any option. All next gates remain blocked pending explicit Owen decision.
