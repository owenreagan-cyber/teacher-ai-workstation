# cosd local API contract (P1b.1a)

Version: `v1` · Service: `cosd` · Binding: loopback only (`127.0.0.1`)

## Authentication

All endpoints except `GET /health` require:

```http
Authorization: Bearer <token>
```

The token is a 256-bit hex secret stored outside the repository under the Chief private state directory (`cosd/api.token`, mode `0600`). Missing or invalid tokens receive `401` with body `{"ok":false,"error":"unauthorized","error_kind":"auth"}`. Authentication failures are audited without logging the supplied credential.

Rotation: `bin/cosd rotate-token` (or `cosd.auth.rotate_token`) issues a new token and invalidates the previous one.

### Device principals (P1b.4b)

An independently registered device uses:

```http
Authorization: Chief-Device <credential_id>.<secret>
```

The device is resolved from the registry. Its status, credential status,
expiration, profile, and the required route permission are checked on every
request. A failed device credential receives `401`; it **never** falls back to
the master bearer token. A Keychain outage receives `503`.

The existing `Authorization: Bearer <master-token>` path remains the trusted
local owner context and keeps its former behaviour.

## Limits

| Limit | Value |
| --- | --- |
| Max request body | 65,536 bytes |
| Ask processing timeout | 305 s (matches model budget; worker isolated per request) |
| Binding | `127.0.0.1` only (non-loopback hosts are rejected at startup) |

## Authorization

Every protected route evaluates a granular permission centrally. Local owner
(master token) has all permissions; a device has only its profile's permissions.

| Route family | Permission |
| --- | --- |
| `GET /v1/status`, `GET /v1/events` | `status.read` |
| `POST /v1/ask`, `POST /v1/ask/stream` | `ask` |
| `GET /v1/tasks`, `GET /v1/tasks/{id}` | `tasks.read` |
| `POST /v1/tasks` | `tasks.create` |
| `POST /v1/tasks/{id}/cancel` | `tasks.cancel` |
| `POST /v1/tasks/{id}/retry` | `tasks.retry` |
| `POST /v1/tasks/{id}/execute` | `tasks.execute` |
| `GET /v1/tasks/{id}/history|attempts|checkpoints` | `history.read` |
| `GET /v1/queue` | `tasks.read` |
| `POST /v1/queue/*`, `/v1/runtime`, `/v1/workers`, `/v1/stop` | `runtime.manage` |
| `GET /v1/devices*` | `devices.read` |
| `POST|PATCH|DELETE /v1/devices*` | `devices.manage` |
| `POST /v1/devices/{id}/credentials/*` | `credentials.manage` |

Profiles and the full matrix: `docs/architecture/device-registry.md`.

## Endpoints

### `GET /health`

Unauthenticated liveness probe.

**200**

```json
{"ok":true,"service":"cosd","version":"0.1.0"}
```

Must not include secrets, session content, or audit payloads.

### `GET /v1/status`

Authenticated runtime snapshot. Delegates to existing `cos status --json` data plus `cosd` version.

**200** — same fields as `cos status --json`, plus `"cosd": "<version>"`.

### `POST /v1/ask`

Authenticated ask through the existing `cos` responder path (`run_ask`).

**Request**

```json
{"question":"what time is it","session_id":null}
```

`session_id` is optional (`[a-z0-9-]{1,40}` when present).

**200** — successful ask body (includes `text`, `answer`, tool metadata).

**400** — usage errors (`error_kind":"usage"`).

**503** — kill switch or model unavailable (`stopped`, `model_unavailable`).

**504** — handler timeout (`error_kind":"timeout"`).

**500** — internal errors.

Idempotency: not guaranteed; each call appends session turns when `session_id` is set.

### `POST /v1/ask/stream`

Authenticated NDJSON stream after `run_ask` completes (chunked `text` for UI). Same policy gate as `/v1/ask`. Final line has `"type":"done"`.

### `GET /v1/events`

Authenticated SSE (`text/event-stream`). Query `since=<event_id>`. Bounded buffer; no secrets in event payloads.

### `GET /v1/runtime`

Authenticated monitoring snapshot (counts, queue, workers, storage sizes, model status). No tokens or session content.

### `POST /v1/stop`

Authenticated graceful **daemon** shutdown (not the `cos` kill switch).

**200**

```json
{"ok":true,"stopping":true}
```

After responding, the server initiates shutdown. Clients should not send further requests.

## Devices (P1b.4b)

Local owner only. All responses exclude raw credentials, Keychain contents,
`keychain_ref`, and verifier material.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/v1/devices` | List (`status`, `device_profile`, `limit` ≤100, `offset`) |
| POST | `/v1/devices` | Register an approved local device |
| POST | `/v1/devices/bootstrap` | Register the primary Mac (`confirm: true`, idempotent) |
| GET | `/v1/devices/{id}` | Detail |
| PATCH | `/v1/devices/{id}` | Rename, profile, metadata, app version |
| DELETE | `/v1/devices/{id}` | Remove a disabled/revoked device |
| POST | `/v1/devices/{id}/disable` | Disable |
| POST | `/v1/devices/{id}/enable` | Re-enable |
| POST | `/v1/devices/{id}/revoke` | Revoke permanently |
| POST | `/v1/devices/{id}/recover-primary` | Release primary protection (exact phrase) |
| GET | `/v1/devices/{id}/credentials` | Credential metadata only |
| POST | `/v1/devices/{id}/credentials/rotate` | Rotate; returns metadata only |
| POST | `/v1/devices/{id}/credentials/revoke` | Revoke one or all active credentials |

No remote enrollment, pairing, or credential-distribution endpoints exist.

## Tasks (P1b.1b)

All task endpoints require authentication. Task IDs are 32-character hex strings.

### `POST /v1/tasks`

Create a queued task.

**Request**

```json
{
  "kind": "brief",
  "title": "Morning brief",
  "description": "",
  "payload": {},
  "priority": 0,
  "idempotency_key": "optional-unique-key",
  "requested_by": "",
  "source": "api",
  "data_class": "internal"
}
```

**201** — `{"ok":true,"task":{...},"reused":false}`
**200** — idempotent replay (`"reused":true`)
**409** — idempotency key conflict (different content)

### `GET /v1/tasks`

Query: `state`, `kind`, `limit` (≤100), `offset`.

**200** — `{"ok":true,"tasks":[...],"total":N,"limit":L,"offset":O}`

### `GET /v1/tasks/{id}`

**200** — `{"ok":true,"task":{...}}`
**404** — unknown id

### `POST /v1/tasks/{id}/cancel`

Optional body: `{"reason":"..."}`.

**200** — cancelled task (from `QUEUED`, `RUNNING`, or `BLOCKED`)

### `POST /v1/tasks/{id}/retry`

**200** — task returned to `QUEUED` from `FAILED` or `BLOCKED`

### `GET /v1/tasks/{id}/history`

**200** — `{"ok":true,"task_id":"...","events":[...]}`

Task records never execute tools or agents in P1b.1b.

## Execution (P1b.1c)

### `POST /v1/tasks/{id}/execute`

Claim (if `QUEUED`) and run through a **registered** handler only (`noop`, `calc`, `diagnostic`).

### `GET /v1/tasks/{id}/attempts` / `GET /v1/tasks/{id}/checkpoints`

Durable execution history for the task.

### `GET /v1/queue`

`paused`, `task_counts`, `active_leases`.

### `POST /v1/queue/pause` / `POST /v1/queue/resume`

### `GET /v1/workers`

Active and historical lease records (bounded).

## Errors

| HTTP | `error_kind` | Meaning |
| --- | --- | --- |
| 401 | `auth` | Missing/invalid bearer or device credential |
| 403 | `forbidden` | Authenticated principal lacks the required permission |
| 404 | `not_found` | Unknown route, task, device, or credential |
| 409 | `conflict` | Invalid transition, duplicate/primary constraint, or idempotency conflict |
| 405 | `method` | Unsupported HTTP method |
| 413 | `usage` | Body too large |
| 504 | `timeout` | Ask exceeded server timeout |
| 503 | `unavailable` | Device registry, credential store, or audit unavailable (fail closed) |

## CLI client (`bin/cos`)

P1b.1d: `bin/cos` may call this API for `ask` and `status` when `COS_USE_DAEMON` is `auto` or `required` and a healthy authenticated `cosd` instance is discovered via the pid file (`COS_STATE_DIR`). Task and queue operations remain on `bin/cosd` (same API, not duplicated in `bin/cos`). See `docs/architecture/cos-daemon-client.md`.

## Versioning

URL prefix `/v1/` is stable for P1b.1a. Breaking changes require a new prefix; `cosd` version is reported on `/health`. `cosd.client.CosdClient` requires `version >= 0.1.0` from `GET /health` and probes `GET /v1/status` before treating the daemon as authenticated.

## Logging

Request paths and status are logged at INFO. Tokens, bearer headers, and session contents must never appear in logs.

## Explicitly not exposed

- Arbitrary shell execution
- Unrestricted tool invocation
- Remote or non-loopback listeners
- TLS (deferred)
- QR pairing / remote enrollment (P1b.4c)
- Remote credential distribution (P1b.4c/P1b.4d)
- Tailscale gateway or public network access (P1b.4d)
