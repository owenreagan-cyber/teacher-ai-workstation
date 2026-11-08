# cosd — local Chief of Staff daemon (P1b.1a)

`cosd` is a persistent loopback HTTP service that wraps the existing `cos` runtime. It does not replace `PolicyGate`, tools, sessions, or audit logic.

## Layout

| Path | Role |
| --- | --- |
| `cosd/server.py` | Threaded `http.server` API |
| `cosd/auth.py` | Bearer token in private state (`cosd/api.token`) |
| `cosd/lifecycle.py` | PID file, spawn/stop, process identity checks |
| `cosd/cli.py` | `serve`, `start`, `status`, `health`, `stop`, `restart`, `rotate-token` |
| `bin/cosd` | Python 3.12 entrypoint |
| `cos/service.py` | Shared `run_ask` / `run_status` for CLI and HTTP |
| `cosd/storage.py` | SQLite WAL task database |
| `cosd/tasks.py` | Task registry service |
| `cosd/task_http.py` | `/v1/tasks` HTTP routing |

API contract: `docs/architecture/cosd-api-contract.md`.

## Manual operation

```bash
cd ~/Projects/teacher-ai-workstation
bin/cosd start          # background on 127.0.0.1:8765
bin/cosd health
bin/cosd status
bin/cosd stop
bin/cosd restart
```

Foreground (debug or tests):

```bash
bin/cosd serve --port 8765
```

No LaunchAgent is installed in P1b.1a; the daemon does not start at login.

## State

| File | Purpose |
| --- | --- |
| `cosd/cosd.pid` | Running process record (service name `cosd`) |
| `cosd/api.token` | API bearer secret (`0600`) |
| `cosd/auth.meta.json` | Token version metadata |

Uses the same `COS_STATE_DIR` / Chief private directory as `cos`.

## Security boundaries

- Binds only to `127.0.0.1`.
- Bearer token required for all endpoints except `/health`.
- `/v1/ask` uses the same policy gate and kill switch as `bin/cos ask`.
- Authentication failures are audit-logged without recording supplied tokens.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| `cosd is already running` | `bin/cosd status`; if stale, remove pid after confirming no cosd process |
| `401 unauthorized` | Ensure client uses current token; run `bin/cosd rotate-token` if rotated elsewhere |
| Stop refused | PID file may point at a non-cosd process; fix pid file manually after verification |

## Task registry (P1b.1b)

SQLite store: `docs/architecture/cosd-task-registry.md`. CLI: `bin/cosd tasks …`.

## Limitations

- No Tailscale/TLS/remote pairing
- No autonomous scheduler or executor (P1b.1c)
- No Chief.app or Raycast migration yet
- `bin/cos` remains the primary one-shot CLI

## Future milestones

- P1b.1b+: HTTPS on Tailscale, device pairing, read-only remote clients
- P1b+: NAS doorman
- Persistent task graph (SQLite WAL) after daemon hardening
