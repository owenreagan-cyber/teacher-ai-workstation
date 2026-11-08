# cosd local API contract (P1b.1a)

Version: `v1` · Service: `cosd` · Binding: loopback only (`127.0.0.1`)

## Authentication

All endpoints except `GET /health` require:

```http
Authorization: Bearer <token>
```

The token is a 256-bit hex secret stored outside the repository under the Chief private state directory (`cosd/api.token`, mode `0600`). Missing or invalid tokens receive `401` with body `{"ok":false,"error":"unauthorized","error_kind":"auth"}`. Authentication failures are audited without logging the supplied credential.

Rotation: `bin/cosd rotate-token` (or `cosd.auth.rotate_token`) issues a new token and invalidates the previous one.

## Limits

| Limit | Value |
| --- | --- |
| Max request body | 65,536 bytes |
| Ask processing timeout | 305 s (matches model budget; worker isolated per request) |
| Binding | `127.0.0.1` only (non-loopback hosts are rejected at startup) |

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

### `POST /v1/stop`

Authenticated graceful **daemon** shutdown (not the `cos` kill switch).

**200**

```json
{"ok":true,"stopping":true}
```

After responding, the server initiates shutdown. Clients should not send further requests.

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

## Errors

| HTTP | `error_kind` | Meaning |
| --- | --- | --- |
| 401 | `auth` | Missing/invalid bearer token |
| 404 | `not_found` | Unknown route or task |
| 409 | `conflict` | Invalid transition or idempotency conflict |
| 405 | `method` | Unsupported HTTP method |
| 413 | `usage` | Body too large |
| 504 | `timeout` | Ask exceeded server timeout |

## Versioning

URL prefix `/v1/` is stable for P1b.1a. Breaking changes require a new prefix; `cosd` version is reported on `/health`.

## Logging

Request paths and status are logged at INFO. Tokens, bearer headers, and session contents must never appear in logs.

## Explicitly not exposed

- Arbitrary shell execution
- Unrestricted tool invocation
- Remote or non-loopback listeners
- TLS (deferred)
