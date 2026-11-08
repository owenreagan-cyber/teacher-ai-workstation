# cosd execution queue (P1b.1c)

Execution layer on top of the P1b.1b task registry. Tasks are persisted first; workers claim, lease, execute registered handlers, checkpoint, recover, and retry.

## Components

| Module | Role |
| --- | --- |
| `cosd/execution/queue.py` | Eligibility, pause/resume, atomic claim |
| `cosd/execution/leases.py` | One active lease per task, TTL + heartbeat |
| `cosd/execution/worker.py` | Handler invocation, KillSwitch gate, outcomes |
| `cosd/execution/dispatcher.py` | Registered kinds: `noop`, `calc`, `diagnostic` |
| `cosd/execution/checkpoints.py` | Durable per-attempt checkpoints |
| `cosd/execution/recovery.py` | Startup scan for interrupted RUNNING work |
| `cosd/execution/retry.py` | Bounded exponential backoff metadata |
| `cosd/execution/engine.py` | Facade used by HTTP and tests |

## Schema v2

`execution_attempts`, `worker_leases`, `execution_checkpoints`, `tasks.retry_after_at`.

## Recovery

On daemon start, expired leases on RUNNING tasks are reconciled using handler `recovery_policy`:

- `safe_replay` → task `QUEUED`
- `checkpoint_resume` with checkpoint → `BLOCKED` (manual)
- otherwise → `BLOCKED` (no blind replay)

## API

See `docs/architecture/cosd-api-contract.md` — `/v1/tasks/{id}/execute`, `/attempts`, `/checkpoints`, `/v1/queue`, `/v1/workers`.

## CLI

`bin/cosd queue …`, `bin/cosd workers list`, `bin/cosd tasks attempts|checkpoints …`.

## Deferred

Autonomous scheduling, multi-agent orchestration, Canvas writes, shell execution.
