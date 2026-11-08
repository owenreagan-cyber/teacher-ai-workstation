# P1b.4a — Multi-device threat model

**Scope:** Chief of Staff (`cosd`) and future remote clients over Tailscale + gateway.
**Status:** Design-time; mitigations marked **existing**, **planned**, or **gap**.

Legend: **PASS** = adequately mitigated at target architecture; **WARN** = partial / depends on implementation discipline; **FAIL** = unacceptable without planned control.

## Summary matrix

| Category | PASS | WARN | FAIL |
| --- | ---: | ---: | ---: |
| Device | 2 | 4 | 1 |
| Authentication | 1 | 3 | 2 |
| Network | 2 | 3 | 1 |
| Application | 3 | 2 | 1 |
| Operational | 2 | 4 | 0 |

---

## Device threats

| Threat | Likelihood | Impact | Existing mitigation | Required mitigation | Detection | Recovery | Class |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Lost personal iPhone | Medium | High | D-007 Face ID (planned); no remote today | Device credential in Secure Enclave; remote wipe via revoke | Failed auth spike | Revoke device; re-pair | **WARN** |
| Stolen MacBook (remote client) | Low | High | None for remote | Gateway + device token; no master token on laptop | Audit auth_failed | Revoke; rotate device cred | **WARN** |
| Shared household iPad | Medium | Medium | None | `capture_only` / school profile default | Profile audit | Disable device | **WARN** |
| Compromised tailnet peer | Low | Critical | None | ACL least-privilege; app-layer device auth | Gateway deny logs | Revoke all device creds on peer | **WARN** |
| Formerly authorized device | Medium | High | Local token only today | Central revoke without master rotation | `last_seen_at` stale + revoke | Re-enroll | **PASS** (planned) |
| School-managed MDM wipe | Medium | Low | N/A | No master token on school devices | Enrollment audit | Re-pair personal | **PASS** (planned) |
| Outdated client app | High | Medium | Version check in Chief desktop | Min client version in gateway | `app_version` field | Block + force upgrade | **WARN** |

---

## Authentication threats

| Threat | Likelihood | Impact | Existing mitigation | Required mitigation | Detection | Recovery | Class |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Stolen `api.token` from disk | Low | Critical | File mode 0600; loopback bind | Keep master local; device tokens for remote | audit auth failures | rotate-token | **PASS** (local) |
| Master token on remote | High (if mis-designed) | Critical | Not deployed | **Never distribute** master token | Code review CERT | Revoke devices | **FAIL** without 4b |
| Replayed pairing code | Medium | High | No pairing yet | Single-use TTL codes | audit pairing.rejected | Invalidate pending | **PASS** (planned) |
| Token leakage in logs | Medium | High | cosd does not log bearer | Gateway scrub headers; no debug dumps | Log review | Rotate cred | **WARN** |
| Session hijacking (HTTP) | Low | High | Loopback only today | TLS on tailnet path | TLS termination audit | Revoke session device | **PASS** (planned) |
| Unauthorized enrollment | Medium | Critical | No enroll endpoint | Owner approval + rate limit | enroll deny audit | Block source | **PASS** (planned) |

---

## Network threats

| Threat | Likelihood | Impact | Existing mitigation | Required mitigation | Detection | Recovery | Class |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Public internet exposure | Low | Critical | `validate_bind_host` | No public bind; gateway only on tailnet | Port scan monitor | Kill gateway | **PASS** |
| Wrong Tailscale ACL | Medium | High | None | Documented ACL template; review checklist | Connection anomalies | Tighten ACL | **WARN** |
| Compromised tailnet device | Low | Critical | None | Device cred + profile | auth_failed burst | Revoke | **WARN** |
| DNS spoofing on tailnet | Low | Medium | MagicDNS controlled | TLS + cert pin optional | TLS errors | Fail closed | **PASS** (planned TLS) |
| Host Mac unavailable | High | Medium | D-015 doorman queue (planned) | Queue + notify; local unchanged | Health checks | WoL / wait | **WARN** |
| MITM without TLS | Medium | High | N/A remote | TLS 1.2+ on gateway | Cert validation | Disable remote | **FAIL** without TLS in 4d |

---

## Application threats

| Threat | Likelihood | Impact | Existing mitigation | Required mitigation | Detection | Recovery | Class |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Privilege escalation via API | Medium | High | PolicyGate; no shell in cosd | Profile matrix on gateway | gateway.request_denied | Patch profile | **PASS** |
| Unauthorized task execute | Medium | High | Registered handlers only | Deny execute for school/readonly | audit execute_denied | Cancel task | **PASS** |
| Cross-device data exposure | Medium | High | Local sessions today | Task/session scoping by profile | Access audit | Revoke device | **WARN** |
| API abuse / flood | Medium | Medium | Timeouts | Rate limits at gateway | Metrics | Throttle IP/device | **WARN** |
| Replay mutating requests | Low | Medium | Idempotency keys (tasks) | Optional request nonces for gateway | Duplicate idempotency | Reject | **PASS** (tasks exist) |
| Inadequate revocation | Medium | High | rotate-token is global today | Per-device credential revoke | Registry state | Instant gateway deny | **WARN** until 4b |

---

## Operational threats

| Threat | Likelihood | Impact | Existing mitigation | Required mitigation | Detection | Recovery | Class |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Mac sleep / cosd down | High | Medium | Local clients show degraded | Doorman + user messaging | /health | bin/cosd start | **WARN** |
| Tailscale disconnect | Medium | Medium | N/A | Offline UI on mobile | Client status | Reconnect | **WARN** |
| Daemon restart | Medium | Low | Task registry durable | SSE reconnect (Chief) | health polling | Auto-reconnect | **PASS** |
| Credential rotation failure | Low | Medium | Manual rotate-token | Broker retry + owner alert | audit rotate_failed | Manual fix | **WARN** |
| Token expires (device) | Medium | Low | N/A | Refresh or re-pair flow | 401 | Re-pair | **WARN** |

---

## Residual risks (accepted for implementation planning)

1. **Owner Mac compromise** — attacker with local disk may read master token; containment = full machine recovery, not network revoke alone. (**WARN**)
2. **Physical access to unlocked owner session** — approve malicious pairing; mitigation = UI confirmation + profile display. (**WARN**)
3. **NAS doorman bug** — must never decrypt E2E queue; CERT required in D-015 milestone. (**WARN** until proven)

## CERT / test implications (future)

- No request served without valid **device** credential on remote path.
- cosd not reachable outside localhost without gateway hop.
- Revoked device receives 401 within one gateway refresh cycle.
- Master token never appears in mobile Keychain export tests.

## Review cadence

Cross-model security review required before P1b.4d activation (per NEXT-PHASES P1b note).
