# cosd task registry (P1b.1b)

Authoritative durable task store for `cosd`. Separate from `cos` session JSONL, Canvas manifests, and audit hash chains.

## Database

| Item | Value |
| --- | --- |
| Path | `$COS_STATE_DIR/cosd/tasks.sqlite3` |
| Mode | `0600` (parent `cosd/` dir `0700`) |
| Engine | SQLite 3, WAL, `foreign_keys=ON`, `busy_timeout=5000ms` |
| Schema version | `1` (`schema_meta`) |

### Tables

- **tasks** — current task record (state, payload, timestamps, idempotency, `data_class`)
- **task_events** — append-only transition history
- **task_metadata** — key/value extension point (reserved)

See `cosd/storage.py` for DDL.

## Lifecycle

| State | Meaning |
| --- | --- |
| `QUEUED` | Persisted, not executing |
| `RUNNING` | Claimed by an executor (future P1b.1c) |
| `COMPLETED` | Success terminal |
| `FAILED` | Failure; retry allowed |
| `CANCELLED` | User cancel terminal |
| `BLOCKED` | Policy/dependency block; retry allowed |

Enforced in `cosd/tasks.py`. Clients cannot set arbitrary states; API exposes create, cancel, retry, and read paths. Internal `transition_task` is for future executors.

### P1b.1c recovery (documented only)

`RUNNING` tasks are **not** auto-failed on daemon startup. Executors must reclaim or reconcile stale `RUNNING` rows in a later milestone.

## Idempotency

Optional `idempotency_key` (unique). Same key + same content fingerprint → existing task. Same key + different content → `409 conflict`.

## API

Documented in `docs/architecture/cosd-api-contract.md` (task section). All endpoints require bearer auth except `/health`.

## CLI

`bin/cosd tasks {list,show,create,cancel,retry,history}` — HTTP client only (no direct SQLite).

## Security

- Loopback binding unchanged.
- Parameterized SQL only; task IDs validated as 32-char hex in routes.
- No secrets in payloads/logs; `data_class` ∈ `{public, internal, sensitive}`.
- Retention: history kept by default (no auto-delete in P1b.1b).

## Migrations

Bump `SCHEMA_VERSION` in `cosd/storage.py` and add upgrade steps inside `_migrate()`.
