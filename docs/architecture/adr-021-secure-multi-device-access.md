# ADR-021: Secure multi-device access to cosd

**Status:** Accepted (architecture — P1b.4a)
**Date:** 2026-11-08
**Deciders:** Owen Reagan (owner); implementation gated per `docs/implementation-approval-gate.md`

## Context

P1b.1–3 delivered a loopback-only `cosd`, a single local bearer token, and clients (Chief.app, Raycast, `bin/cos`). D-007 and D-015 describe iPhone and NAS-assisted access over Tailscale with pairing and revocable tokens — **not yet implemented**.

Mission P1b.4a requires an implementation-ready design without activating remote access.

## Decision

1. **Keep `cosd` bound to `127.0.0.1`** for the foreseeable implementation track. Do not weaken `validate_bind_host` for convenience.

2. **Introduce a separate remote access gateway** (on the primary Mac, tailnet-facing) that:
   - Terminates TLS.
   - Validates **per-device credentials**.
   - Enforces **permission profiles** per HTTP route.
   - Proxies to loopback `cosd` using an internal mechanism that does not expose the master `api.token` to remote clients.

3. **Maintain an authoritative device registry** (SQLite + Keychain-backed secrets) as described in `docs/architecture/device-registry.md`.

4. **Never distribute the daemon master `api.token` to remote devices.** Local clients may continue reading the token from private state until a future Keychain migration (P1b.4b).

5. **Align transport wake/queue with D-015** — NAS doorman forwards or holds E2E encrypted work; it does not replace application authentication.

6. **Network trust is separate from application authorization** — Tailscale ACLs alone are insufficient.

## Options considered

| Option | Outcome |
| --- | --- |
| A. Bind cosd to Tailscale IP | Rejected — couples core daemon to network exposure |
| B. Loopback cosd + gateway | **Selected** |
| C. Dedicated local proxy only | Accepted as B variant with stricter process isolation |

## Consequences

### Positive

- Local clients unchanged in P1b.4a.
- Per-device revocation without rotating all credentials.
- Clear path to SwiftUI (P1c) with stable JSON API.

### Negative

- Additional process to deploy, monitor, and patch (gateway).
- Two-layer auth ops complexity (Tailscale + device profile).

## Conflict with prior docs

| Source | Conflict? | Resolution |
| --- | --- | --- |
| D-007 iPhone over Tailscale | None | ADR specifies gateway + device cred; consistent |
| D-015 NAS doorman | None | Doorman is transport; ADR adds app auth layer |
| `cosd.md` "No Tailscale" | None until 4d | Still true for P1b.4a; gateway ships later |
| D-006 "Raycast is launcher only" | Minor | P1b.3 Raycast is cosd HTTP client on same Mac; not a second runtime — unchanged |

No superseding of D-007 or D-015 required.

## Implementation approval

P1b.4b through P1b.4d and P1c each require separate mission approval per implementation gate.

## References

- `docs/security/p1b4-multi-device-architecture.md`
- `docs/security/p1b4-threat-model.md`
- `docs/architecture/remote-access-gateway.md`
- `docs/architecture/device-registry.md`
