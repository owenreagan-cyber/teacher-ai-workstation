# cosd local operations (P1b.2)

Daily-use controls: lifecycle, notifications, SSE task events, chunked ask streaming, runtime monitoring, optional LaunchAgent.

## Lifecycle

- CLI: `bin/cosd start|stop|restart|health|status` (authoritative).
- Chief.app Settings → **Runtime & notifications**: start/stop/restart via main process (`execFile` on `bin/cosd`). Stop/restart require confirmation in the UI.

## Notifications

Main-process macOS notifications with 60s deduplication per event/task. Preferences in `ops-prefs.json` under Electron `userData`. No task payloads or tokens in notification bodies.

## Event stream

`GET /v1/events?since=<id>` — authenticated SSE (`text/event-stream`). Bounded buffer (256 events), max 8 subscribers. Task registry publishes on `task_events` insert.

Chief.app subscribes when **Live task events** is enabled; connection polling relaxes to 60s.

## Conversation streaming

`POST /v1/ask/stream` — NDJSON (`chunk` lines + final `done`). Uses existing `run_ask` then chunks text. **Ollama token streaming is not yet wired**; true token streaming would extend `ModelClient` without a second agent path.

## Runtime monitoring

`GET /v1/runtime` — version, uptime, task counts, queue pause, workers summary, storage sizes, model status (via `run_status`). No secrets.

## LaunchAgent (opt-in)

```bash
bin/cosd launchagent show
bin/cosd launchagent install --confirm
bin/cosd launchagent remove --confirm
```

`RunAtLoad` is **false** by default. No credentials in plist `ProgramArguments`.

## Troubleshooting

| Issue | Action |
| --- | --- |
| No SSE | Confirm cosd running and bearer auth; check subscriber cap |
| Duplicate notifications | Dedup window 60s; reconnect refreshes state without replaying mutations |
| Stream stalls | Client disconnect cancels; use `/v1/ask` for non-streaming |
