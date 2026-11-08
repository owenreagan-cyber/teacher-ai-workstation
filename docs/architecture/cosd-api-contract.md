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

## Errors

| HTTP | `error_kind` | Meaning |
| --- | --- | --- |
| 401 | `auth` | Missing/invalid bearer token |
| 404 | `not_found` | Unknown route |
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
