# Raycast ↔ cosd (P1b.3)

Raycast is a **client surface** for the same persistent Chief of Staff runtime as Chief.app and `bin/cos` (when daemon mode is on). It does not own sessions, tasks, policy, or models.

## Location

`integrations/raycast/chief-of-staff/`

## Architecture

```text
Raycast extension (TypeScript)
  → read cosd.pid + api.token from ~/Library/Application Support/ChiefOfStaff/
  → loopback HTTP + Bearer auth
  → cosd
  → SQLite task registry · execution queue · run_ask · PolicyGate
```

No direct SQLite access. No `bin/cos` spawn when cosd is required for these commands.

## Authentication

- Token path: `<stateDir>/cosd/api.token` (0600 on disk; read in the Raycast Node runtime).
- Never committed, logged, or copied into Raycast preferences.
- Non-loopback hosts in `cosd.pid` are rejected.
- `AUTH_ERROR` state when the token is missing or rejected (rotation: `bin/cosd rotate-token`).

Keychain storage is **not** used in P1b.3; the daemon and Chief.app already share the private state directory. A future milestone could mirror the token into Keychain without changing cosd authority.

## Commands

| Raycast title | Purpose |
| --- | --- |
| Ask Chief of Staff | Conversational ask via `/v1/ask` and configurable `sessionId` preference |
| Capture Task | Fast `POST /v1/tasks` with `kind: capture` (non-executable note) |
| Chief of Staff Tasks | List, filter, detail, history, cancel, retry |
| Chief of Staff Queue | Counts, running tasks, worker leases |
| Chief of Staff Status | Health, uptime, model/kill switch summary |

## Quick Capture

- Idempotency: one UUID per form session (`idempotency_key`).
- Priority 0–3; `data_class` public | internal | sensitive.
- Tasks remain `QUEUED` until an explicit execute path (registered kinds only).

## Connection states

`DISCONNECTED`, `AUTH_ERROR`, `VERSION_MISMATCH`, `DEGRADED`, `RECOVERING`, `CONNECTED`.

Unavailable cosd shows recovery steps (`bin/cosd start`); Raycast does **not** install LaunchAgents or spawn duplicate daemons.

## Notifications

Raycast toasts/HUD on capture success and errors. No parallel notification service; Chief.app remains the rich notification surface (SSE).

## Security

- Loopback-only HTTP client (`127.0.0.1` / `localhost`).
- Task IDs validated as 32-hex before mutating calls.
- List views omit task payloads; titles and safe metadata only.

## Testing

```bash
cd integrations/raycast/chief-of-staff
npm test
```

Hermetic tests mock HTTP and temp state dirs; no Ollama or live cosd required in CI.

## Limitations (P1b.3)

- No SSE live task stream in Raycast (poll on open).
- No `bin/cos` fallback for ask when cosd is down.
- Daily Brief still only in legacy `apps/raycast-chief-of-staff` (CLI) until a cosd brief endpoint exists.
- D-007 iPhone client remains separate (SwiftUI + Tailscale), not Raycast.

## Troubleshooting

See `integrations/raycast/chief-of-staff/README.md`.
