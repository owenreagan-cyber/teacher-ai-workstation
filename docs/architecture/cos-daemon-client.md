# cos smart client (P1b.1d)

`bin/cos` can route selected commands through the persistent `cosd` runtime while preserving standalone fallback.

## Compatibility matrix

| Command | Daemon when healthy | Notes |
| --- | --- | --- |
| `ask` | yes | Same `run_ask` path on server |
| `status` | yes | `GET /v1/status` |
| `history` | no | Local session read |
| `chat`, `brief`, `home`, `needs`, `warm` | no | Standalone runtime |
| `config`, `auto-search` | no | Local config |
| `stop`, `resume` | no | Kill switch local |
| `tools`, `audit` | no | Local registry / audit file |
| Task / queue ops | N/A | `bin/cosd tasks` / `queue` only |

## `COS_USE_DAEMON`

| Value | Behavior |
| --- | --- |
| `auto` (default) | Use daemon when discoverable and authenticated; else standalone |
| `required` | Fail clearly if daemon unavailable |
| `disabled` | Never contact daemon |

## Discovery

`cosd/client.py` reads `cosd/cosd.pid`, verifies process identity, `GET /health`, then probes `GET /v1/status` with the private bearer token. Loopback only.

## Sessions

Daemon `ask` uses the same `COS_STATE_DIR` sessions and audit as standalone `run_ask`.

## Tasks

Use `bin/cosd tasks` / `bin/cosd queue` for SQLite-backed tasks (no direct DB access from `bin/cos`).

## Performance (fixture mode, representative)

Local one-shot `status --json` with `COS_FIXTURE_DIR` set (no Ollama call):

| Path | Approx. wall time |
| --- | --- |
| Standalone (`COS_USE_DAEMON=disabled`) | ~0.02 s (new Python process) |
| Daemon client (`COS_USE_DAEMON=auto`, cosd running) | ~0.02 s (HTTP + auth probe; no model) |

`ask` adds model or fixture responder time on top of the above; the daemon removes repeated cold imports inside the long-lived server process.

## Troubleshooting

- `COS_USE_DAEMON=required` + `bin/cosd start` first.
- Stale pid: `bin/cosd status` then `bin/cosd stop` if needed.
