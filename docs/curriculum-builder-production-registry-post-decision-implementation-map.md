# Production Registry Post-Decision Implementation Map

Last updated: 2026-07-02

```text
Status: planning_only
Classification: post-Owen-decision routing — not implementation authority
```

## Purpose

Map Owen § J checklist outcomes to **safe next missions** without implying approval. Use after Owen updates the checklist tracker.

## Phase 0 — Prior (All Pending)

| Condition | Repo state |
| --- | --- |
| All 11 items `pending` | CB-PROD-GOV complete; writes blocked; 1 expected checklist WARN |

**Superseded 2026-07-02** by governance affirmation batch.

## Phase 1 — Current: Governance Affirmations Recorded (No Writes)

**Trigger:** Owen approved items 5, 6, 7, 8, 9, 11; deferred items 1, 2, 3, 4, 10 (2026-07-02).

| Mission | Scope | Blocked |
| --- | --- | --- |
| Tracker + doc refresh | Governance batch recorded in tracker | Write code |
| Path + namespace session | Owen decides items 1 and 10 together | Creating registry files |
| Write behavior | Item 2 remains deferred | Any `--write` or writer scripts |

**Expected checklist WARN:** 1 (5 deferred items). Approved governance rows do **not** authorize production writes.

## Phase 2 — Governed Write Preflight (Still No Writer)

**Trigger:** Items 1, 2, 6, 7, 10, 11 approved; item 2 explicitly `yes` manual-only.

| Mission | In scope | Out of scope |
| --- | --- | --- |
| Write preflight docs/tests expansion | Checklists, negative tests, audit stub refinement | `--write` handler |
| Dry-run validation hardening | Fake candidate validation only | Promotion to production |

See `docs/proposals/backlog/production-registry-write-mission.md` § Preflight Checklist.

## Phase 3 — Single-Record Manual Write (Future Separate Mission)

**Trigger:** Phase 2 complete + Owen issues explicit write mission prompt + ChatGPT review.

| Requirement | Detail |
| --- | --- |
| Smallest scope | One manual record, snapshot before/after |
| Rollback | Per audit stub |
| Review state | Must be `approved` before write |
| ID namespace | Per item 10 decision |

## Phase 4 — Metadata Pilot (Separate from Writes Unless Both Approved)

**Trigger:** Items 3, 4, 5 approved (manual metadata boundaries).

| Mission | Scope |
| --- | --- |
| Metadata pilot planning | `docs/curriculum-builder-metadata-pilot-planning-boundary.md` |
| Fake-only field examples | No real titles/paths |

Blocked until approved: real metadata in production registry. Items 3 and 4 remain **deferred** as of 2026-07-02.

## Phase 5 — Integrations (Per-System Missions)

**Trigger:** Item 9 opened per integration + separate Owen mission each.

Item 9 approval affirms integrations **remain blocked** in v1 unless separate missions. Never bulk-approved via § J alone.

## Non-Activation

This map does not authorize any phase transition automatically. Phase 1 does not authorize writes.
