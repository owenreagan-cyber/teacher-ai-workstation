# Device registry and credential foundation (P1b.4b)

**Status:** Implemented locally (P1b.4b/P1b.4c). Remote access, pairing over
networks, QR-based remote enrollment, Tailscale, and the gateway remain disabled.

This document records the implementation that follows ADR-021 and
`docs/architecture/device-registry.md`. It does not change an accepted
architectural decision.

## Scope and activation

| Capability | P1b.4b state |
| --- | --- |
| Persistent device registry | **Implemented** (SQLite, local) |
| Independent device identities | **Implemented** |
| Permission profiles + central authorization | **Implemented** |
| Device credential lifecycle (Keychain references) | **Implemented** (local host) |
| Credential rotation/revocation | **Implemented** |
| Device security audit events | **Implemented** (hash-chained JSONL + SQLite events) |
| Authenticated local device APIs | **Implemented** (`/v1/devices`) |
| Chief.app device management | **Implemented** (local owner only) |
| Remote enrollment / QR pairing | **Implemented locally** (P1b.4c); remote delivery not enabled |
| Tailscale / TLS gateway | **Not implemented** (P1b.4d) |
| Remote credential distribution | **Not implemented** |

`cosd` still binds only to `127.0.0.1`. The existing master token, Chief.app,
Raycast, and `bin/cos` paths are unchanged.

## Storage

The device tables live in the existing cosd database file
(`<state>/cosd/tasks.sqlite3`). There is no second database. A separate
`schema_meta` key (`device_schema_version`) version-controls this migration so
a device migration failure cannot take down the task registry; `cosd` catches
device-registry startup failures and continues serving the existing local API.

### Tables

`devices`

| Column | Notes |
| --- | --- |
| `device_id` | Random 128-bit identity (`uuid4().hex`, 32 lowercase hex). Never derived from IP, hostname, or display name. |
| `display_name` | Editable, 1–80 characters. |
| `device_type` | `mac`, `iphone`, `ipad`, `other`. |
| `platform` | `macos`, `ios`, `ipados`, `unknown`. |
| `owner_id` | Assigned owner label. |
| `device_profile` | `owner`, `personal`, `partner`, `school`, `read_only`, `capture_only`, `revoked`. |
| `trust_level` | `owner`, `trusted`, `limited`, `restricted`, `untrusted`. |
| `status` | `active`, `disabled`, `revoked`, `removed` (terminal tombstone; removal deletes the row). |
| `app_version` | Last reported client version (bounded). |
| `registered_at`, `last_seen_at`, `updated_at`, `revoked_at` | UTC ISO 8601 timestamps. |
| `metadata_json` | Bounded non-sensitive labels. Secret-looking keys and student/PII-looking keys are refused. |
| `is_primary_owner` | Unique partial index; at most one primary owner device. |

`device_credentials`

| Column | Notes |
| --- | --- |
| `credential_id` | Random opaque id. |
| `device_id` | Foreign key to `devices` with `ON DELETE CASCADE`. |
| `credential_type` | `device_access`. |
| `keychain_ref` | Keychain account reference, never the secret. |
| `verifier` / `verifier_salt` | Salted SHA-256 verifier (one-way) used as an integrity check. |
| `status` | `active`, `rotated`, `expired`, `revoked`. |
| `created_at`, `expires_at`, `rotated_at`, `revoked_at` | Lifecycle timestamps. |

`device_events`

No foreign key, so audit provenance survives device removal. It stores
`device_id`, `display_name`, `event_type`, `result`, `profile`,
`credential_id`, `actor`, `details_json`, and `created_at`.

Raw credentials, private keys, and Keychain contents are **never** written to
SQLite or the audit log.

## Device identity and lifecycle

Registration generates a random device id once. All later operations use the
stored id; restarting `cosd` does not change it.

```text
register -> active
active   -> disabled -> active (re-enable, same identity)
active   -> revoked
disabled -> revoked
revoked  -> removed (delete row; audit retained)
disabled -> removed (policy: only disabled or revoked devices may be removed)
```

- **Disable** blocks authentication and authorization immediately.
- **Re-enable** restores a disabled device without a new identity.
- **Revoke** permanently invalidates credentials and trust. It cannot be undone.
- **Remove** deletes the registry row only after the device is disabled or
  revoked. Credentials cascade; `device_events` and the JSONL audit remain.

### Primary Mac bootstrap

The primary Mac is registered with an explicit confirmation:

```bash
bin/cosd devices bootstrap --confirm --name "Primary Mac"
```

The API equivalent is `POST /v1/devices/bootstrap` with `{"confirm": true}`.
The operation is idempotent: if a primary owner already exists, the existing
record is returned and no duplicate is created. The device receives the
`owner` profile and trust level. Local platform metadata (`os_release`,
`architecture`) is stored; no hardware serial or MAC address is collected.

The existing master token is not changed and is not copied to the device
credential. Device credentials are separate.

### Primary owner protection and recovery

The primary owner device cannot be disabled, revoked, removed, or moved off
the `owner` profile. Recovery is explicit:

```bash
bin/cosd devices recover-primary <device_id> --confirm-phrase "RECOVER PRIMARY OWNER"
```

This releases the primary flag (audited as `device.primary_recovery`). The
operator can then revoke/remove it and bootstrap a new primary Mac. This is
deliberately a two-step operation, not an accidental click.

## Permission profiles

Profiles are fixed sets defined in `cosd/devices/permissions.py`. Nothing
inherits from `owner`; unknown profiles and permissions fail closed.

| Profile | Grants |
| --- | --- |
| `owner` | All permissions. |
| `personal` | `ask`, status/tasks read/create/edit/cancel/retry/execute, history, sessions. |
| `partner` | `ask`, `status.read`, `tasks.read`, `tasks.create`. No private history or execution. |
| `school` | `ask` (restricted workflow), `status.read`, `tasks.create`. No task listing, history, sessions, execution, or administration. |
| `read_only` | `status.read`, `tasks.read`, `history.read`. Cannot mutate. |
| `capture_only` | `status.read`, `tasks.create`. Cannot ask, read, or execute. |
| `revoked` | Nothing. |

Granular permissions: `ask`, `status.read`, `tasks.read`, `tasks.create`,
`tasks.edit`, `tasks.cancel`, `tasks.retry`, `tasks.execute`, `history.read`,
`sessions.read`, `sessions.create`, `runtime.manage`, `devices.read`,
`devices.manage`, `credentials.manage`.

`ask` is a distinct permission because asking is neither task capture nor
execution. This is the only addition to the list in the mission; it is required
to enforce the ADR's school/partner ask boundaries.

### Central authorization

`DeviceAuthorizationService` resolves a principal and authorizes every protected
operation. A request is allowed only when all checks pass:

1. Device identity is unambiguous.
2. Device status is `active`.
3. The credential row is `active` and not expired.
4. The credential is not revoked or rotated.
5. The profile grants the required permission.
6. The kill switch is evaluated for execution/ask/mutating device requests.
7. Policy restrictions in the profile matrix apply.

Two principal kinds are distinguished:

- **Local owner** — a valid existing master bearer token. It keeps the existing
  local behaviour and receives the owner permission set. It is not represented
  as a remote device.
- **Device** — `Authorization: Chief-Device <credential_id>.<secret>`. It has
  only its profile permissions and never falls back to the master token.

Network membership is not consulted for authorization. A future gateway may
add network policy, but application authorization stays here.

## Pairing and enrollment (P1b.4c)

P1b.4c adds owner-created pairing invitations, one-time codes/QR payloads,
device-generated X25519 identities, explicit owner approval, authenticated
credential-delivery envelopes, re-pairing/replacement, and enrollment audit.
The implementation lives in `cosd/devices/pairing/` and reuses this registry and
credential service. Codes are 60-bit, single-use, salted-hash verified, expire
within 10 minutes, and are rate-limited/replay-audited. Raw credentials are
never stored in SQLite; the encrypted delivery envelope is held in Keychain and
the device decrypts it with its private key.

**Remote enrollment remains disabled.** All pairing endpoints are loopback-only
until P1b.4d supplies the authenticated TLS gateway. Full protocol:
`docs/architecture/device-pairing-implementation.md`.

## Credentials

### Provider interface

`CredentialProvider` has `get_secret`, `set_secret`, and `delete_secret`.
Production macOS uses `KeychainCredentialProvider`, which calls `security` with
an argument list (no shell). The service name is
`com.chiefofstaff.cosd.device`; the account is the credential's Keychain
reference. Tests use `MemoryCredentialProvider` or a fake `security` runner.
There is no plaintext fallback.

`COSD_CREDENTIAL_PROVIDER=memory` selects the ephemeral provider for tests and
non-macOS development hosts. The production target is macOS.

### Token and verification

A device credential is `<credential_id>.<secret>`, where the secret is 32
random bytes encoded with `token_urlsafe`. Only the credential id and a salted
SHA-256 verifier are stored. Verification re-reads the secret from the
protected store and compares it with the presented secret using
`hmac.compare_digest`, then checks the stored verifier. A Keychain outage fails
closed (`503` for the device request); it never falls back to the master token.

### Rotation, expiration, revocation

- **Rotate:** marks the old row `rotated`, issues a new credential id/secret,
  and removes the old Keychain secret where possible. The old token is rejected
  even if the Keychain delete fails because its status is no longer `active`.
- **Expire:** `expires_at` is checked on every verification; an expired
  credential is invalid.
- **Revoke:** marks the row `revoked` and deletes the secret best-effort.
  Authorization re-checks the row on every request, so a stolen credential stops
  working immediately.
- **Device revoke:** revokes every active credential for that device.

## Local API

All routes require authentication. Profile management requires
`devices.manage`; read routes require `devices.read`; credential mutation
requires `credentials.manage`. Only the owner profile has those permissions.

| Method | Endpoint | Permission | Purpose |
| --- | --- | --- | --- |
| GET | `/v1/devices` | `devices.read` | List (bounded; `status`, `device_profile`, `limit`, `offset`). |
| POST | `/v1/devices` | `devices.manage` | Register an approved local device. |
| POST | `/v1/devices/bootstrap` | `devices.manage` | Register the primary Mac (confirm required, idempotent). |
| GET | `/v1/devices/{id}` | `devices.read` | Detail. |
| PATCH | `/v1/devices/{id}` | `devices.manage` | Rename, profile, metadata, app version. |
| DELETE | `/v1/devices/{id}` | `devices.manage` | Remove a disabled/revoked device. |
| POST | `/v1/devices/{id}/disable` | `devices.manage` | Disable. |
| POST | `/v1/devices/{id}/enable` | `devices.manage` | Re-enable. |
| POST | `/v1/devices/{id}/revoke` | `devices.manage` | Revoke permanently. |
| POST | `/v1/devices/{id}/recover-primary` | `devices.manage` | Release primary protection with the exact phrase. |
| GET | `/v1/devices/{id}/credentials` | `devices.read` | Credential metadata only. |
| POST | `/v1/devices/{id}/credentials/rotate` | `credentials.manage` | Rotate; returns metadata, never the secret. |
| POST | `/v1/devices/{id}/credentials/revoke` | `credentials.manage` | Revoke one or all active credentials. |

Responses never contain raw credentials, Keychain contents, or `keychain_ref` /
`verifier` fields. Errors are stable:
`401 auth`, `403 forbidden`, `404 not_found`, `409 conflict`, `400 usage`,
`503 unavailable`.

The existing `/v1/status`, `/v1/tasks/*`, `/v1/ask`, `/v1/events`,
`/v1/runtime`, and `/v1/stop` routes now evaluate a permission for the
principal. A valid master token remains the local owner and keeps its former
behaviour.

## Audit

Every lifecycle operation writes both a `device_events` row and a hash-chained
JSONL record in `audit.jsonl`. Event kinds:

`device.registered`, `device.renamed`, `device.metadata_changed`,
`device.profile_changed`, `device.disabled`, `device.re_enabled`,
`device.credential_created`, `device.credential_rotated`,
`device.credential_revoked`, `device.revoked`, `device.removed`,
`device.primary_recovery`, `device.auth_ok`, `device.auth_failed`,
`authorization.denied`, `device.registry_unavailable`.

Records include device id, operation, timestamp, result, credential id (where
applicable), profile, and actor. Tokens, secrets, private keys, raw credential
material, and student information are never recorded. Audit provenance survives
device removal because `device_events` has no foreign key and `audit.jsonl` is
append-only. A security change whose audit write fails rolls back and returns a
`503` rather than proceeding untrailed.

## Chief.app

`Devices` is a local owner screen in the rail (⌘6). It lists name, type,
platform, profile, status, registration date, last seen, and app version; it
supports detail, rename, profile change, disable, re-enable, revoke, remove,
credential rotation/revocation, and primary bootstrap. Profile changes and
every access-changing lifecycle action require a confirmation dialog.

Electron boundaries are unchanged: the main process owns all HTTP and tokens,
the preload exposes fixed typed IPC calls, and the renderer receives only bounded
device/credential metadata. It never receives a token or Keychain reference.

Raycast remains a cosd client and does not manage devices in this milestone.

## Privacy boundaries

- School devices: restricted ask + task capture + status only. No personal
  session history, no task listing (which would expose other devices' tasks), no
  execution, no device administration, no master credential.
- Partner devices: shared task/ask capabilities only. No private personal
  history or sessions by default, no execution, no administration.
- Personal devices: personal workflows, but no device/credential administration
  and no runtime management.
- Read-only devices cannot mutate records. Capture-only devices cannot execute.
- Device metadata refuses secret-like and student/PII-like keys. Student
  information must not be placed in device metadata.

## Failure and recovery

| Condition | Behaviour |
| --- | --- |
| Device registry missing or migration fails | `cosd` keeps serving existing local routes; `/v1/devices` returns `503`; log records the reason. |
| Database unavailable | Device operations fail closed; local daemon startup catches the device failure and continues. |
| Keychain unavailable | Credential issue/rotation/verification fails closed (`503` for device auth); no plaintext fallback. |
| Audit write failure | Security change rolls back (`503`); authentication that cannot be audited fails closed. |
| Revoked device presents old credential | `401`; no master fallback. |
| Disabled/expired/rotated credential | `401`; device must be re-enabled, re-issued, or re-enrolled by the owner. |
| Primary owner needs replacement | `recover-primary` with the exact phrase, then revoke/remove and bootstrap a new primary. |

## Explicitly deferred (P1b.4d / P1c)

QR pairing, one-time remote enrollment, Tailscale install/ACLs, remote gateway,
remote TLS endpoint, public network access, iPhone/iPad connectivity, remote
device credentials, NAS doorman, Wake-on-LAN, and remote notifications are not
part of P1b.4b/P1b.4c remote activation. P1b.4c implements the local pairing and
delivery primitives only; remote delivery remains P1b.4d.

## Credential rotation reservation (P0.3c.2)

`rotate_credential()` now reserves durably before touching the provider. The
table `credential_rotation_reservations` is keyed by the **credential id being
rotated**, so two concurrent rotations of one credential cannot both proceed;
the loser gets `409`.

Sequence: short transaction validates the credential is still `active` and
inserts the reservation -> provider writes the new secret with **no database
lock held** -> a second short transaction claims the reservation (`rowcount =
1`), fences on the exact credential observed at reservation time
(`UPDATE ... WHERE credential_id = ? AND status = 'active'`), marks the old row
`rotated`, inserts the new active row, audits, and deletes the reservation. The
old credential stays usable until that commit; the new one exists only after it.

After commit the old provider secret is deleted. If deletion fails, a
`cleanup_failed` row is recorded and `reconcile_credential_rotations()` retries
it at startup. Interrupted rotations (pending reservations) are cleared at
startup together with their orphaned new secret; nothing is ever activated by
reconciliation.

Measured with a 1 s provider delay: rotation total 1.01 s, unrelated
`list_devices` p95 **0 ms** (268 samples). Note: rotation already wrote the
provider outside the transaction before this change; the gap closed here is
crash consistency and orphan cleanup, not lock scope.
