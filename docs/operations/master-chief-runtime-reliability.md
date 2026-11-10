# Chief runtime reliability (P0.3b)

```text
Status: source change certified in isolation; production daemon not restarted
Scope: lifecycle hardening, runtime provenance, health classification, credential lock analysis
Production activation: separate owner-approved step
```

This record covers how `cosd` behaves across start, stop, crash, restart and version drift. It does
not authorize restarting the running daemon or replacing Chief.app.

---

## 1. Lifecycle state machine

The pid file is the only authority for "a daemon claims to be running here", and it is never trusted
without identity and health checks.

```text
                 no pid file
                     │
                 start ─────────────► running ──(health ok, identity ok)──┐
                     │                   ▲                               │
                     │                   └── healthy ◄───────────────────┘
                     │
        (start refused)                  │ stop / crash
   ┌─────────────────┴──────────┐        ▼
   │ port already in use        │   stale_pid  (pid alive, identity/health fails)
   │ pid points at another proc │        │
   │ already running            │        └── explicit stop clears the pid file
   └────────────────────────────┘
                                          ▼
                                     not_running (pid dead, file left behind)
```

| Transition | Mechanism | Failure behavior |
| --- | --- | --- |
| start | `spawn_server` writes the pid only after `/health` answers, bounded at 15 s | raises, no pid file written |
| already running | pid alive + identity match + health | refuses with "cosd is already running" |
| pid points elsewhere | `process_is_cosd` marker check | refuses; never signals an unrelated process |
| port occupied | `port_in_use` before spawn | refuses; no duplicate daemon |
| stop | authenticated `/v1/stop`, then SIGTERM, bounded at 10 s, then SIGKILL | reports failure instead of hanging |
| crash | pid file remains; health fails | classified `stale_pid`, not `running` |
| restart | stop then start, each bounded | same guarantees as above |

`process_is_cosd` no longer matches a bare `cosd` substring. It requires a daemon-specific marker
(`from cosd.cli import main`, `cosd.cli`, `cosd/__main__.py` or ` -m cosd `), so a shell that merely
mentions the word cannot be mistaken for the daemon.

**No automatic restart loops exist.** Nothing supervises or relaunches `cosd`; a crash leaves the
daemon down until the owner starts it. The opt-in LaunchAgent remains uninstalled by default.

---

## 2. Runtime provenance

`cosd/provenance.py` takes a **frozen snapshot** when the daemon process starts:

| Field | Meaning |
| --- | --- |
| `version` | `cosd.__version__` of the loaded package |
| `python` | loaded interpreter version |
| `environment` | `venv` or `system` |
| `loaded_commit` | git commit at process start, or `null` |
| `loaded_branch` | branch at process start, or `null` |
| `loaded_dirty` | whether tracked files were modified at start |
| `source_available` | whether a checkout was readable at all |
| `started_at` | process start timestamp |

The snapshot never re-reads the repository, so a later `git pull` cannot make an old process claim it
is current. `drift()` compares the snapshot with the checkout on demand:

- HEAD changed → `restart_required: true`, with both commits in the payload.
- New uncommitted edits to tracked files → `restart_required: true`.
- Checkout missing or unreadable → `restart_required: null`, and **the daemon still serves**.
  A missing commit is reported as `null`; no hash is invented.
- No absolute filesystem paths are exposed by the API.

Cached for 5 s so polling does not repeatedly shell out to git.

---

## 3. Health classification

`cosd/health.py` derives one of:

| State | Meaning |
| --- | --- |
| `HEALTHY` | serving, database readable, no attention needed |
| `DEGRADED` | serving, but restart required, queue paused, or device registry unavailable |
| `RECOVERING` | startup reconciliation repaired interrupted work within the last 30 s |
| `BLOCKED` | kill switch engaged, or the state database is unreadable |
| `DISCONNECTED` | client-side only: Chief.app cannot reach the daemon |

The HTTP socket answering is **not** sufficient for `HEALTHY`. `/health` stays a liveness probe;
`/v1/status` and `/v1/runtime` carry the classification and its reasons.

---

## 4. Recovery and persistence

Verified behavior (execution/recovery suites, 8 tests, plus cosd 112):

- Completed tasks are never replayed.
- An interrupted RUNNING task is reconciled at startup: `safe_replay` → `QUEUED`,
  `checkpoint_resume` without a checkpoint → `BLOCKED`, otherwise `BLOCKED`.
- Expired leases are expired before reconciliation, so a live lease is not stolen.
- Attempts record `RECOVERING` with an `interrupted` marker.
- Checkpoints survive restart; retry scheduling uses bounded exponential backoff.
- Cancellation is durable (state, not deletion).
- Recovery runs before the HTTP server accepts work and respects the KillSwitch and permissions.

The startup recovery report is now captured and exposed through `/v1/runtime` (`recovery.repaired`)
instead of being discarded.

---

## 5. Credential-provider lock scope

`approve()` performs credential issuance and envelope encryption inside one database transaction,
which holds the shared connection lock. Measured with a provider that delays each write by 1.0 s:

| Measurement | Result |
| --- | --- |
| Approval total | **2.01 s** (two provider writes: device credential + delivery envelope) |
| Unrelated `list_devices` reads during approval | n=2, mean **1.00 s**, max **2.00 s** |
| Correctness under the delay | one device, one active credential, enrollment APPROVED once |
| Provider failure on envelope write | `DeviceError` 503, transaction rolled back, enrollment stays `AWAITING_OWNER_APPROVAL`, no device |

**Classification: WARN.** With the real Keychain provider (10 s timeout) worst-case blocking of
unrelated device reads is bounded by that timeout per write. This is an availability concern, not an
integrity or authorization defect: issuance still happens only after committed approval, and a
failure rolls back cleanly.

**Why not reordered in this phase.** Moving the provider write outside the transaction would require
a reservation + compensation state (credential `PENDING`, then activate after the write) to preserve
the current guarantee that no device is ever `APPROVED` without a delivered credential. That is a
state-machine change, not a small fix, and doing it without a crash-consistent reservation would be
worse than the current cost. It is recorded as the next reliability task.

---

## 6. Safe restart procedure (owner action)

```bash
cd ~/Projects/teacher-ai-workstation
./bin/cosd status          # must say "running" before you begin
./bin/cosd stop            # bounded: SIGTERM, then SIGKILL after 10 s
./bin/cosd start           # writes the pid only after /health answers
./bin/cosd status          # state=running
```

Before restarting, confirm `git rev-parse HEAD` is the intended commit; after restarting,
`/v1/status.runtime.loaded_commit` should match it and `restart_required` should be `false`.

No credential, database, or audit file is touched by start/stop. Stopping is a graceful shutdown:
the execution engine pauses the queue, then the process exits.

---

## 7. Owner-controlled startup policy

| Mode | Behavior |
| --- | --- |
| **Manual (default)** | The owner runs `bin/cosd start`. Nothing supervises the process. |
| **Opt-in supervised (not installed)** | The existing LaunchAgent definition can supervise `cosd` if the owner later approves it. |

The LaunchAgent is inspected and its safety is covered by `tests/cosd/test_launchagent.py`. It is
**not installed or enabled** by this mission, login items are unchanged, and launchd state was not
modified. Any future activation needs explicit approval and a documented bounded restart policy.

---

## 8. Known limitations

1. **Credential lock scope is WARN** (see §5). Unrelated device reads serialize behind provider I/O.
2. **No automatic recovery supervisor.** A crashed daemon stays down until restarted by the owner.
3. **Provenance is best-effort.** A packaged runtime without a git checkout reports `null` commits
   rather than a fabricated hash.
4. **`DISCONNECTED` is client-only.** The server cannot report it about itself.
5. **Restart-required is informational.** The daemon never restarts itself because the checkout
   moved.
