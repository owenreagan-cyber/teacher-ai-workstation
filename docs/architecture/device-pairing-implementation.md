# Device pairing and enrollment implementation (P1b.4c)

**Status:** Implemented locally. Remote enrollment, network access, Tailscale,
the TLS gateway, and remote credential delivery remain disabled (P1b.4d).

This builds on the P1b.4b device registry, permission profiles, Keychain
credential provider, lifecycle APIs, and hash-chained audit. There is no second
registry or credential system.

## Scope

| Capability | P1b.4c state |
| --- | --- |
| Owner-created pairing invitation | **Implemented** |
| One-time pairing code + QR payload | **Implemented** |
| Device-generated public identity | **Implemented** (X25519, client foundation) |
| Code redemption / replay prevention | **Implemented** |
| Owner approval/rejection/cancellation | **Implemented** |
| Independent credential issuance | **Implemented** via P1b.4b credential service |
| Authenticated delivery envelope | **Implemented contract + local harness** (X25519 + HKDF-SHA256 + AES-256-GCM) |
| Re-pairing / replacement | **Implemented** |
| Remote enrollment over TLS | **Not implemented** (P1b.4d) |
| Tailscale/ACLs/public listener | **Not implemented** |

`cosd` still binds only to `127.0.0.1`. The master daemon token is never part of
a pairing request, QR payload, enrollment response, or device credential.

## Enrollment states

`PENDING` → `AWAITING_OWNER_APPROVAL` → `APPROVED` → `COMPLETED`.

Terminal states: `REJECTED`, `EXPIRED`, `CANCELLED`, `COMPLETED`. There is no
transition out of a terminal state. Only service methods may transition; a
client cannot set `APPROVED` or `COMPLETED` directly.

| State | Meaning |
| --- | --- |
| `PENDING` | Owner created an invitation; the device has not redeemed the code. |
| `AWAITING_OWNER_APPROVAL` | A device redeemed the code and bound its public key; the owner must decide. |
| `APPROVED` | Owner approved; device + credential exist; encrypted delivery is pending. |
| `COMPLETED` | Device retrieved and decrypted the credential envelope. |
| `REJECTED` | Owner rejected before approval. |
| `EXPIRED` | Code or approval/delivery window elapsed, or too many bad codes. |
| `CANCELLED` | Owner cancelled before completion. |

## Pairing protocol

1. **Owner invitation.** Chief.app calls `POST /v1/enroll/request` with the
   requested name, category, platform, and proposed profile. The daemon creates
   a `PENDING` request, a one-time code, and a QR payload.
2. **Display.** Chief.app shows the QR and short code. The QR contains only
   `v`, `enrollment_id`, `code`, and `expires_at`. It contains no master token,
   private key, or permanent credential.
3. **Device identity.** The enrolling device generates an X25519 keypair. The
   private key stays in the device's secure store; only the public key is sent.
4. **Redeem.** The device calls `POST /v1/enroll/redeem` with the enrollment id,
   code, public key, nonce, display metadata, requested profile, and protocol
   version. The code is verified against a salted hash and consumed. State moves
   to `AWAITING_OWNER_APPROVAL`. A one-time enrollment request token is returned
   to the device for status/completion.
5. **Owner review.** Chief.app lists the request with name, category, platform,
   app version, requested profile, creation/expiry, and a permission summary.
   The owner selects the approved profile explicitly and confirms.
6. **Approval.** The daemon:
   - validates state, expiry, profile, confirmation, and key fingerprint;
   - requires explicit `allow_owner` if the owner selects `owner`;
   - handles optional explicit replacement (revoke old device first);
   - creates the device with the approved profile;
   - issues a P1b.4b device credential (secret in Keychain only);
   - encrypts a delivery payload to the device public key;
   - stores the ciphertext in the Keychain under an enrollment delivery reference
     and stores only that reference in SQLite;
   - moves state to `APPROVED` and audits the decision.
7. **Completion.** The device calls
   `POST /v1/enroll/status/{id}/complete` with its enrollment request token. The
   daemon returns the ciphertext envelope once, marks `COMPLETED`, and deletes
   the envelope. The device decrypts with its private key and stores the token
   in its secure store.

## Pairing codes

- 12 symbols from a 32-symbol ambiguity-free alphabet = **60 bits** of entropy.
- Generated with `secrets.choice`; displayed as three groups of four.
- Stored only as `sha256(salt + normalized_code)` with a random salt.
- Comparison uses `hmac.compare_digest`.
- Single-use: the hash is cleared on successful redemption; a second redemption
  is audited as `pairing.replay_denied` and rejected.
- Code TTL is at most **600 seconds**. The code expiry is separate from the
  post-redemption owner-approval window (default 1 hour).
- Per-enrollment failed-code attempts are bounded (default 5); the request
  expires after the limit. A durable per-source request/redeem rate limit is
  stored in `pairing_rate_limits`.
- Codes and QR payloads never appear in ordinary logs; audit records contain
  only code length/TTL, never the code.

## Device-generated identity

- Production clients use X25519 keys; the private key never leaves the device.
- `DeviceEnrollmentClient` uses a `SecureDeviceStore`; macOS uses the Keychain
  (`com.chiefofstaff.enrollment.device`). Tests use `MemoryDeviceStore`.
- The server stores the public key only on the enrollment record and a SHA-256
  fingerprint on the device row. A unique partial index prevents two active
  devices with the same key.
- Client-supplied names, platforms, and requested profiles are **requests**, not
  proof. The owner chooses the approved profile.

## Credential delivery

The delivery payload `{credential_id, token, device_id, profile, expires_at}` is
encrypted with X25519 ECDH + HKDF-SHA256 + AES-256-GCM using the established
`cryptography` package. Envelope includes an ephemeral public key, nonce,
ciphertext, and context hash. The context binds `enrollment_id` and the device
key fingerprint.

- Raw credential is never written to SQLite, logs, URLs, QR codes, preferences,
  Electron renderer, or Raycast.
- SQLite stores only credential metadata and the Keychain delivery reference.
- Enrolled credentials are long-lived by default; the P1b.4b `expires_at` field is
  supported and checked on every authentication. Revocation is the primary
  immediate control; automated refresh is not part of this phase.
- The production dependency is `requirements-cosd-pairing.txt`
  (`cryptography>=42`). Without it, owner approval fails closed with
  `503 crypto_unavailable`; there is no plaintext fallback.
- P1b.4c uses this envelope through local loopback only. P1b.4d will expose the
  approved enrollment operations through the authenticated TLS gateway.

## Owner approval and permissions

- The owner must select `device_profile` explicitly; a client-requested profile
  is never auto-approved.
- `owner` requires `allow_owner: true` plus explicit confirmation; it is never
  automatic.
- New unknown devices default to `capture_only`/`read_only` in the UI.
- `school`, `partner`, `read_only`, and `capture_only` restrictions come from the
  P1b.4b profile matrix and are shown before approval.
- Profile changes after enrollment remain owner-only (`devices.manage`).

## Re-pairing and replacement

A public key already registered cannot silently create a second active identity.
The owner must supply `replaces_device_id` matching that key. The old device is
revoked (credentials invalidated) and remains in the registry with its audit
history; the new device receives a new identity and credential. A replacement is
audited as `device.replaced` with the previous device id. Revoked devices follow
the same explicit replacement path.

## API

All routes are loopback-only in this phase.

| Method | Endpoint | Authentication | Permission |
| --- | --- | --- | --- |
| POST | `/v1/enroll/request` | owner master token | `devices.manage` |
| POST | `/v1/enroll/redeem` | one-time pairing code | none (rate-limited) |
| GET | `/v1/enroll/status/{id}` | `Authorization: Enrollment <request-token>` | enrollment token |
| POST | `/v1/enroll/status/{id}/complete` | enrollment token | enrollment token |
| GET | `/v1/devices/pending` | owner master token | `devices.read` |
| GET | `/v1/devices/pending/{id}` | owner master token | `devices.read` |
| POST | `/v1/devices/pending/{id}/approve` | owner master token | `devices.manage` |
| POST | `/v1/devices/pending/{id}/reject` | owner master token | `devices.manage` |
| POST | `/v1/devices/pending/{id}/cancel` | owner master token | `devices.manage` |

The master bearer token is not accepted as an enrollment request token, and a
device token cannot approve/reject/cancel enrollments. Status responses never
include the pairing code, request token hash, private key, or credential secret.
The encrypted envelope is returned only to the enrollment token holder on
completion.

Stable errors: `401 auth`, `403 forbidden`, `404 not_found`, `409 conflict`,
`410 expired`, `429 rate_limited`, `503 unavailable/crypto_unavailable/
delivery_unavailable`, `400 usage`.

## Recovery

| Condition | Behaviour |
| --- | --- |
| Expired invitation | `410`; state `EXPIRED`; owner creates a new request. |
| Wrong code | Bounded attempts; after the limit state `EXPIRED` and `429`. |
| Reused code | `409`; `pairing.replay_denied`. |
| Owner rejects/cancels | Terminal state; pending device/credential is not created (or is revoked if already approved). |
| Keychain unavailable at approval | Device/credential transaction rolls back; `503`; no partial enrollment. |
| Audit write failure | Transaction rolls back; `503`; enrollment does not proceed untrailed. |
| Daemon restart | Request, state, code hash, and Keychain delivery reference persist; status/completion resume. |
| Delivery expiry | `APPROVED` request expires; unclaimed device is revoked; envelope deleted. |
| Device loses private key | It cannot decrypt; owner cancels/rejects and creates a new request. |
| Re-pair / replacement | Explicit `replaces_device_id`; old identity revoked; provenance retained. |

## Audit

Events: `pairing.requested`, `pairing.code_generated`, `pairing.redeemed`,
`pairing.approved`, `pairing.rejected`, `pairing.expired`, `pairing.cancelled`,
`pairing.replay_denied`, `pairing.completed`, `device.enrolled`,
`device.enrollment_failed`, `device.credential_issued`, `device.replaced`.

Records include enrollment id, device id when known, actor, result, approved
profile/permission snapshot, credential id, and failure category. They never
include codes, private keys, permanent credentials, or student information.
Pairing events use `pairing:<enrollment_id>` as the device-event subject until a
device exists; completed/approved events use the real device id. Audit
provenance survives device removal.

## Chief.app

The Devices screen now has:

- **Pending Enrollments**: requested metadata, requested/approved profile,
  timestamps, permission restrictions, approve with explicit profile selection,
  reject, cancel.
- **Add Device**: name, category, platform, requested profile, QR code, one-time
  code, expiration countdown, cancel.
- **Completed devices**: existing P1b.4b device list/detail, credential status,
  profile, registration time, status.

Approval and all lifecycle actions require confirmation. The renderer never
receives tokens or Keychain references; the main process validates ids,
profiles, metadata, and confirmation flags.

## Concurrent redemption (P0.3a)

Redemption is a compare-and-set against authoritative database state, not a
read-then-hope sequence.

- **One authoritative read path.** `DeviceDatabase.query_one` / `query_all`
  (and the same helpers on the task `TaskDatabase`) materialize rows while
  holding the connection lock. Fetching from a cursor after the lock is released
  is forbidden across `cosd/`; a static test enforces it. This closes the defect
  where a concurrent commit reset an open statement and produced an all-NULL row
  (which surfaced as `TypeError: int() ... not 'NoneType'` in `_row_to_record`).
  The same pattern was present in the task registry and execution layer
  (`cosd/tasks.py`, `cosd/execution/`), so those reads were converted too.
- **Transition is validated inside the write transaction.** `redeem()`
  re-reads the enrollment with `_fetch_conn` inside `transaction()` and calls
  `_transition`, which uses `ensure_transition` and raises
  `DeviceError(kind="conflict", http_status=409)` for any illegal move. A
  request that read `PENDING` before another request consumed the code
  therefore cannot also succeed.
- **Invariant.** For one invitation, exactly one request may reach
  `AWAITING_OWNER_APPROVAL`; every other request receives 401 (unknown code),
  409 (already used / illegal transition) or 410 (expired). No request receives
  an unhandled exception, and no second device or credential is created.
- **Fail-closed record guard.** An enrollment row without a protocol version is
  rejected with a controlled 409 rather than a `TypeError`.
- **Retry semantics.** A client retry after an ambiguous response hits the
  same transition check and receives 409; the committed winner is unchanged.
- **Recovery.** A transaction that fails before commit rolls back, leaving the
  invitation `PENDING` with no device or credential. A committed redemption
  survives daemon restart because it lives in SQLite.

Enrollment remains **disabled in production**. This section describes verified
behaviour, not an activation decision.

### Independent review (D-010)

Reviewed by a different model family from the builder, in a separate review
session, against the uncommitted patch (storage helpers, service/registry/
credential read conversion, the fail-closed record guard, and the new tests).

**Verdict: APPROVE WITH REQUIRED CHANGES — no critical or high findings.**
The reviewer independently confirmed: single-winner redemption, replay
prevention, one-credential issuance through the approval flow, approval binding
to the enrollment fingerprint/profile, state-machine correctness, transactional
rollback, rate-limit preservation, no new secret exposure, and consistent
cross-device boundaries.

Follow-ups it raised, both medium/low and neither correctness-breaking:

1. **Lock scope during approval.** `approve()` performs credential-envelope
   encryption and credential-provider writes inside the DB transaction, so the
   shared connection lock is held across that I/O. Pre-existing in shape; a
   stalled provider could briefly serialize unrelated device reads. Deferred to
   a follow-up rather than changed here, because reordering provider writes and
   the commit would alter the failure/cleanup semantics that currently prevent
   a false APPROVED state. Recorded in the threat model as a residual risk.

   Measured in P0.3b with a provider delaying each write by 1.0 s: approval took
   2.01 s (credential + envelope) and unrelated `list_devices` reads waited up
   to 2.00 s. Correctness held: one device, one active credential, and a
   provider failure rolled back to `AWAITING_OWNER_APPROVAL` with no device.
   Classified **WARN** (availability only). A durable-reservation design that
   removes provider I/O from the transaction is specified in
   `docs/operations/master-chief-runtime-reliability.md` §5a but not yet
   implemented.
2. **Guard breadth.** The static guard now flags any `.execute(...).fetch*`
   whose receiver is not a lock-held connection (`conn`, `c`, `active_conn`,
   `self._conn`). Verified against the pre-fix `registry.py` (10 sites flagged)
   and the patched tree (0 flagged).

## Testing

`tests/cosd/devices/pairing/` covers code generation/entropy/expiry, single use,
replay, concurrency, rate limits, owner approval/rejection/cancellation,
profile escalation, credential issuance/binding/replacement, restart/keychain/
audit/database recovery, API authentication, six device classes, audit chain,
and real X25519/AES-GCM when the dependency is installed. All tests use temporary
state and fake credential stores/ciphers; the real Keychain is never touched.

`test_pairing_concurrency.py` adds 18 deterministic cases for P0.3a: two- and
ten-way contention, differing identities, races with expiry/cancellation/
approval, repeated approval, missing and unsupported protocol versions,
interrupted transactions, restart, retry, write-lock contention, independent
invitations, audit consistency, read coherency under concurrent writes, and a
static guard against cursor-fetch reads. Barriers and hooks are used instead of
sleeps, so the interleavings reproduce.

## Explicitly deferred

Remote enrollment over TLS, Tailscale/ACLs, public listeners, gateway, remote
credential delivery, iPhone/iPad app implementation, NAS doorman, Wake-on-LAN,
and remote notifications remain P1b.4d/P1c.
