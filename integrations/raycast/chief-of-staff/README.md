# Chief of Staff — Raycast (cosd client)

Raycast commands talk to the **persistent `cosd` daemon** on loopback. They do not start a second Python runtime or read the task SQLite database directly.

| Command | API |
| --- | --- |
| Ask Chief of Staff | `POST /v1/ask` |
| Capture Task | `POST /v1/tasks` (`kind: capture`, idempotent) |
| Chief of Staff Tasks | `/v1/tasks`, cancel, retry, history |
| Chief of Staff Queue | `/v1/queue`, `/v1/workers` |
| Chief of Staff Status | `/v1/status`, `/v1/runtime` |

## Install (local dev)

```bash
cd ~/Projects/teacher-ai-workstation/integrations/raycast/chief-of-staff
npm ci
npm run typecheck
npm test
npm run dev   # imports into Raycast; Ctrl-C when listed
```

1. Start cosd: `bin/cosd start`
2. Raycast → **Settings → Extensions → Chief of Staff**
3. Confirm **Chief state directory** (default `~/Library/Application Support/ChiefOfStaff`)

Authentication reads `cosd/api.token` from that directory (same as Chief.app). Tokens are never shown in Raycast UI or logs.

## Legacy extension

The older `apps/raycast-chief-of-staff` extension called `bin/cos` via `execFile`. New work lives here and targets **cosd** only (no silent CLI fallback).

## Troubleshooting

| Issue | Fix |
| --- | --- |
| Disconnected | `bin/cosd start` |
| Auth error | `bin/cosd rotate-token` and restart cosd |
| Ask timeout | Ollama cold start; use Chief.app for long streams |

See `docs/architecture/raycast-chief-of-staff.md`.
