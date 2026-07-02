# Production Registry Post-Decision Implementation Map

Last updated: 2026-07-02

```text
Status: planning_only
Classification: post-Owen-decision routing — not implementation authority
```

## Purpose

Map Owen § J checklist outcomes to **safe next missions** without implying approval. Use after Owen updates the checklist tracker.

## Phase 0 — Current (No Write Authorization)

| Condition | Repo state |
| --- | --- |
| All 11 items `pending` | CB-PROD-GOV complete; writes blocked; 1 expected checklist WARN |
| Governance status PASS | Blocked-write proof only |

## Phase 1 — Owen Affirmations Only (No Writes)

**Trigger:** Owen approves items 5, 6, 7, 8, 9, 11 (governance affirmations) without items 1, 2, 10.

| Mission | Scope | Blocked |
| --- | --- | --- |
| Tracker + doc refresh | Update tracker rows; cross-link path decision | Write code |
| Path decision doc update | Record Owen's choice in path-options doc | Creating registry files |

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

Blocked until approved: real metadata in production registry.

## Phase 5 — Integrations (Per-System Missions)

**Trigger:** Item 9 opened per integration + separate Owen mission each.

Never bulk-approved via § J alone.

## Non-Activation

This map does not authorize any phase transition automatically.
