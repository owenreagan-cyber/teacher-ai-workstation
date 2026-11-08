# Chief.app ↔ cosd integration (P1b.1e)

Chief.app (`apps/chief-desktop`) is a first-class client of the persistent `cosd` runtime.

## Architecture

```text
Renderer (sandboxed) → preload (`window.chief`) → Electron main → cosd (loopback HTTP)
                                                      ↘ cos CLI (execFile fallback)
```

- **Renderer:** no tokens, no Node, no network (`connect-src 'none'` unchanged).
- **Main:** reads `ChiefOfStaff/cosd/api.token`, discovers `cosd.pid`, authenticated HTTP only on `127.0.0.1`.
- **cosd:** authoritative for `ask`, `status`, tasks, queue, policy, audit, sessions.

## Operations via cosd

| UI / IPC | API |
| --- | --- |
| Chat `ask` | `POST /v1/ask` when connected |
| Status dot / Settings | `GET /v1/status` when connected |
| Task center | `/v1/tasks`, `/v1/queue`, history/cancel/retry |

Brief, home, config, history (session read), warm, kill switch remain **`bin/cos` via execFile** (same policy path as before).

## Modes

`CHIEF_USE_DAEMON` or `COS_USE_DAEMON`: `auto` (default), `required`, `disabled`.

- **auto:** use cosd for ask/status/tasks when authenticated; otherwise standalone cos (not unrestricted).
- **required:** ask/status fail clearly if cosd unavailable.
- **disabled:** never contact cosd.

## Connection states

`DISCONNECTED`, `CONNECTING`, `CONNECTED`, `DEGRADED`, `AUTH_ERROR`, `VERSION_MISMATCH`, `RECOVERING`.

Main polls every 15s (60s when **Live task events** is on) with bounded backoff. Renderer receives `chief:event` updates for `cosd-connection`, `cosd-task-event`, and `ask-chunk`.

## Streaming

- **Ask:** `POST /v1/ask/stream` (NDJSON chunks) when Settings → *Streaming ask* is enabled; otherwise `POST /v1/ask`.
- **Tasks:** `GET /v1/events` SSE authenticated stream; Task center refreshes on push events.

## Lifecycle

Settings → **Runtime & notifications** can `start` / `stop` / `restart` via main-process `bin/cosd` (stop/restart require confirmation). LaunchAgent remains opt-in CLI only; Chief does not install login items for cosd.

## Security

- `contextIsolation: true`, `nodeIntegration: false`, narrow preload IPC.
- Tokens never logged or sent to renderer.
- Task IDs validated (`[a-f0-9]{32}`); ask/session strings bounded.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Task center empty, DISCONNECTED | `bin/cosd start` |
| AUTH_ERROR | `bin/cosd rotate-token` and restart daemon |
| Standalone mode | cosd not running; start daemon or use `CHIEF_USE_DAEMON=disabled` |
