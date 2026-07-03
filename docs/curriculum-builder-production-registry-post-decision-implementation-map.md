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

## Phase 1 — Governance Affirmations Recorded (No Writes)

**Superseded 2026-07-02** by path + namespace decision sync.

## Phase 1b — Path + Namespace Recorded (No Writes)

**Superseded 2026-07-02** by item 2 write behavior tracker sync.

## Phase 2 — Current: Write Behavior Approved in Principle (Preflight Eligible)

**Trigger:** Owen approved item 2 in principle (2026-07-02); items 3 and 4 remain deferred.

| Mission | Scope | Blocked |
| --- | --- | --- |
| Tracker + doc refresh | Item 2 recorded in tracker | Registry mutation |
| **Phase 2 preflight** (separate explicit prompt) | Docs/status/tests/audit/rollback hardening only | `production-registry.json`, records, `--write`, sentinel removal |
| Metadata intake session | Items 3 and 4 remain deferred | Real metadata or source references |

**Approved path:** `assistant/curriculum-builder/registry/v0-2/production-registry.json` (file does not exist yet)

**Approved namespace:** `resource-*`

**Write behavior:** manual-only, single-record, snapshot-first, rollback-required — **in principle only**

**Expected checklist WARN:** 1 (2 deferred items). Item 2 approval does **not** authorize registry mutation.

### Phase 2 Preflight Boundaries (When Explicitly Prompted)

| In scope | Out of scope |
| --- | --- |
| Checklists, negative tests, audit stub refinement | `--write` handler |
| Dry-run validation hardening (fake candidates only) | Creating `production-registry.json` |
| Status proof that mutation remains blocked | Creating `resource-*` records |
| Rollback planning test expansion | Removing `BLOCKED-NO-WRITES.sentinel` |

See `docs/proposals/backlog/production-registry-write-mission.md` § Preflight Checklist.

## Phase 3 — Single-Record Manual Write (Future Separate Mission)

**Trigger:** Phase 2 complete + Owen issues explicit write mission prompt + ChatGPT review + items 3/4 if real metadata required.

| Requirement | Detail |
| --- | --- |
| Smallest scope | One manual record, snapshot before/after |
| Rollback | Per audit stub |
| Review state | Must be `approved` before write |
| Production path | `assistant/curriculum-builder/registry/v0-2/production-registry.json` |
| ID namespace | `resource-*` per item 10 decision |
| Real metadata | Requires items 3 and 4 approved |

## Phase 4 — Metadata Pilot (Separate from Writes Unless Both Approved)

**Trigger:** Items 3, 4, 5 approved (manual metadata boundaries).

Blocked until approved: real metadata in production registry. Items 3 and 4 remain **deferred** as of 2026-07-02.

## Phase 5 — Integrations (Per-System Missions)

Item 9 approval affirms integrations **remain blocked** in v1 unless separate missions.

## Non-Activation

This map does not authorize any phase transition automatically. Phase 2 preflight requires a separate explicit mission prompt.
