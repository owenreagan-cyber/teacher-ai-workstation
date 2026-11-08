# ADR-020: cosd persistent task registry (deferred)

**Status:** Proposed (design only — not implemented in P1b.1a)
**Date:** 2026-11-08

## Context

Future `cosd` milestones need durable background work: scheduled briefs, multi-step agent tasks, and client-submitted jobs from Chief.app / Raycast / mobile without blocking HTTP workers.

## Decision (planned)

Store tasks in SQLite with WAL mode under the Chief private state directory, separate from `cos` session JSONL:

- Table `tasks`: id, created_at, updated_at, state, priority, kind, payload_json, lease_owner, lease_until
- Table `task_events`: append-only audit of state transitions
- Workers poll with short leases; crashed workers expire leases for retry
- API surface remains authenticated; no arbitrary shell execution

## Consequences

- P1b.1a ships HTTP + lifecycle only; no queue tables or workers
- Session and audit hash chains for `cos` remain unchanged
- Implementation requires a dedicated mission with CERT coverage for lease safety and idempotency

## Alternatives considered

- File-based job queue — rejected for lack of atomic leasing
- In-memory queue — rejected; incompatible with daemon restarts
