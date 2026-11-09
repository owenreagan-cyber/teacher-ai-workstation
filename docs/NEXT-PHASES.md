# Chief of Staff — Next Phases

Status: ACCEPTED · revised 2026-10-02
Settled rules are recorded in `docs/DECISIONS.md`. This file is the build order.

**Canonical product direction and program sequence: `docs/master-chief-roadmap.md`.** This file
keeps the phase-level detail for work already sequenced there. "Master Chief" is the internal
codename for the platform; the product is **Chief**.

Operating evidence for P0.1 (installed application identity, source provenance, `cosd` and device
certification, candidate package hash): `docs/operations/master-chief-operational-certification.md`.

## Product shape

There is **one `cos` core with two faces.**

| | **Messenger** (Mac compact window + iPhone app) | **Co-developer** (Mac Workbench, the expanded window) |
|---|---|---|
| Does | weather, meetings, reminders, quick web search, mail summary (later) | idea → structured prompt → best tool per part → runs, reviews, diffs, test results |
| Speed | under 3 s | minutes to hours, in the background |

## Done

| Item | Result |
|---|---|
| M1 core | `cos` CLI, tools, policy gate, audit, kill switch, fast path |
| M1.5A desktop shell | Chief.app (Electron), signed and installed |
| E1 Part 1 | harness with 9 suites; CERT-001 to CERT-008; 165/165 fake |
| F1 / F2 | session fixes; `think: false` (model-path p50 15.6 s → about 2 s); cloud-model guard; `num_ctx`; `keep_alive`; `cos warm`; dev-mode fix |

## Standing rules

- **The harness grows with every phase.** New behavior gets new cases. A new safety rule gets a
  new CERT ID, assigned when it is implemented.
- **Certify from a clean commit.** Nightly runs must be green before any merge.
- **Builder and reviewer differ.** Phases that touch security, networking, or authority get a
  reviewer from a different model family (D-010).
- **Find, then fix.** Harness failures are listed first, then fixed in a separate batch.

## Build order

### P0 — Operational deployment and certification (open)

**Certified 2026-11-09:** the installed `/Applications/Chief.app` is v0.1.0, arm64, Electron 44.5.1,
signed (Team 98F559Y354, hardened runtime, not notarized), and built from commit `24c9df4` — proven
by a byte-identical rebuild of all 28 asar payload files. `cosd` lifecycle, authentication, task
persistence, device registry and pairing are certified against a temporary state root.

**Still open:**
- The installed build predates `cosd`: no tasks, queue, devices, pairing, or notifications. It runs
  the `bin/cos` CLI fallback.
- `cosd` has never run in production (no state directory exists).
- `cryptography` is missing from the operating Python 3.12; pairing approval fails closed today.
- A signed candidate from `98b9dfc` (`app.asar` sha256 `529c221c…92506`) is built and **not
  installed**. Installation needs owner approval.

Details and rollback: `docs/operations/master-chief-operational-certification.md`.

### P1a — Messenger complete (Mac). Next.
- **Web search:** an explicit command ("search …" / "look up …"), one allowlisted API, the API
  key kept in the macOS Keychain, and results treated as untrusted data (D-011).
- **Home card:** a greeting, the next event, reminders due, and weather. Deterministic, no model.
- **Personality spec:** `cos/personality.md`, edited by Owen. Chief never offers actions it
  can't do.
- **Start at login.**
- **Harness:** cases for search (fake provider), injected search results, and personality, plus
  a new CERT for search query provenance.

### P1a.5 — Rich Messenger (prompt: `docs/prompts/PROMPT-P1A5.md`)
- **Structured answers:** `cos` returns structured blocks: time card, weather card, hourly chart, daily forecast, collapsed sources, one action button, and follow-up suggestions. The model never writes block data.
- **Weather:**
  - day and night visuals, from the weather service's `is_day`, sunrise, and sunset
  - a 7-day forecast and the next 12 hours
  - named places: home is Wilson, work is Clayton
- **Links:** opened only through `openLink(turnId, linkId)`, which accepts https links from Chief's own results only. The renderer stays offline.
- **Suggestions:** chosen by deterministic code, and they never start a web search (D-011).
- **Search summaries:** links are stripped from the summary text, fixing the duplicated links seen in the first real search.
- **Same contract on iPhone:** the iPhone app (P1c) renders this same block schema.

### P1b — `cosd` daemon

**P1b.1a (complete):** loopback daemon, authenticated HTTP, lifecycle CLI, `run_ask` integration.

**P1b.1b (complete):** SQLite task registry, task APIs, idempotency, event history.

**P1b.1c (complete):** Execution queue, worker leases, checkpoints, startup recovery, registered handlers, `bin/cosd queue`. No autonomous scheduler or multi-agent orchestration yet.

**P1b.1d (complete):** `bin/cos` smart client (`COS_USE_DAEMON`, `cosd/client.py`) for `ask`/`status` with standalone fallback.

**P1b.1e (complete):** Chief.app (`apps/chief-desktop`) uses loopback cosd for ask, status, and task center; execFile fallback for other cos commands. See `docs/architecture/chief-app-cosd-integration.md`.

**P1b.4a (architecture — complete):** Multi-device security design only. ADR-021: loopback `cosd` + tailnet **gateway**, device registry, per-device credentials (not master token). See `docs/security/p1b4-multi-device-architecture.md`, `docs/security/p1b4-threat-model.md`, `docs/architecture/device-registry.md`, `docs/architecture/remote-access-gateway.md`. **No remote access activated.**

**P1b.4b (complete — local foundation only):** Persistent device registry in the existing cosd SQLite file, independent stable device ids, permission profiles with central authorization, Keychain-backed device credential references, rotation/expiration/revocation, device audit events, authenticated local `/v1/devices` APIs, primary Mac bootstrap, and a Chief.app local owner Devices screen. Implementation: `docs/architecture/device-registry-implementation.md`. The master token, Chief.app, Raycast, and `bin/cos` paths are unchanged. **Remote enrollment, pairing, Tailscale, TLS, and remote credentials remain disabled.**

**P1b.4c (complete — local pairing only):** Owner-created pairing invitations with 60-bit one-time codes and QR payloads, device-generated X25519 identities, code redemption with replay/rate limiting, explicit owner approval, permission selection, independent credential issuance, authenticated X25519/HKDF/AES-GCM delivery envelopes, re-pairing/replacement, enrollment audit, and Chief.app Pending Enrollments/Add Device UI. Implementation: `docs/architecture/device-pairing-implementation.md`. **All enrollment endpoints remain loopback-only; remote delivery and network access wait for P1b.4d.**

**Later P1b (implementation, gated):**
- **P1b.4d** — Tailscale, TLS gateway, ACLs, remote enrollment activation (cross-model security review).
- HTTPS on gateway (not on raw cosd listener).
- Read-only / capture-only profiles for remote clients by default.
- **New CERTs:**
  - no remote request without valid **device** credential
  - cosd not reachable outside localhost except via gateway

### P1b+ — NAS doorman (D-015)
- A Docker container on the UGREEN NAS. It runs Tailscale, is always on, and serves only paired devices.
- **Wake on demand:** wakes the MacBook over the home network, waits until `cosd` is reachable, then forwards the request.
- **Queue:** if the Mac can't be woken, it holds the request encrypted end-to-end between phone and Mac. It delivers the request when the Mac returns and notifies the phone.
- **Limits:** no models, no plaintext content, and no credentials for school data on the NAS.
- **New CERTs:**
  - the doorman never stores or logs plaintext request content
  - it forwards only to the paired Mac
- Cross-model security review is required.

### P1c — Chief for iPhone (SwiftUI)
- **On the phone itself (works without the Mac):**
  - time and weather (Apple weather service)
  - today's calendar and reminders, read on the phone through EventKit
  - short replies from Apple's on-device model
- **Through the Mac:** search and longer answers, sent via `cosd` directly or through the NAS doorman.
- **Features:**
  - chat
  - home card
  - brief
  - history
  - Stop
  - Face ID
  - offline state
- **Then:** a widget (home card) and a Siri App Intent ("ask Chief").
- **Data rule:** stores nothing on the device and locks when idle (D-014 once accepted).
- **Build:** Cursor builds, installed with Xcode over USB-C. A different model family reviews.

### P2 — Co-developer v1: Prompt Studio
- An **Expand** button opens the Workbench.
- Type an idea. Local Qwen writes a full build prompt (scope, rules, validation, report) and
  splits it into parts.
- Chief suggests an installed tool for each part.
- Each part gets a copy button and an open-app button. Handoff only; nothing is sent
  automatically.

### P3 — Agent registry and usage log
- **Inventory:** tools detected on the Mac plus subscriptions Owen confirms (D-012).
- **Per tool:** strengths and a backup.
- **Usage:** a log of every job sent, detection of limit messages and reset times, and backup
  suggestions while a tool is capped.

### P4 — Automatic runs
- Requires approval packets and `cosd`.
- **Flow:**
  1. Owen approves a job.
  2. Claude Code or Codex runs in a fresh worktree under the D1 safety profile.
  3. The harness runs.
  4. A reviewer from another model family reviews the result.
  5. Owen sees the diff and both reports in the Workbench.

### Alongside P1–P2
- **E1 Part 2:**
  - an answer-quality judge
  - personality checks, using the personality spec from P1a
  - paraphrase expansion of the test cases
  - honesty cases, including offers to do actions Chief can't do

### Week of 10/12 (school resumes)
- Projector test. Auto-hide when a display is mirrored or a new display is added.
- All-day classroom use.

### Later
- **Mail:** read-only through Apple Mail (D-013).
- **Downloads cleanup:** with quarantine.
- **Canvas track:** C0–C3.
- **Drive and iCloud.**
- **Merge gate and Stage 0 consolidation onto `main`.** First step done: MERGE-1 (2026-10-18)
  merged the Chief stack with `main` on `integrate/cos-into-main`; the PR into `main` is Owen's.

## Targets every run

| Metric | Target |
|---|---|
| CERT invariants | all PASS |
| Fake-run pass rate | 100% |
| Fast-path p95, wall time | < 200 ms |
| Model path, real (`tool_choice`) | p50 ≤ 5 s, p95 ≤ 15 s |
| Memory free with the model loaded | ≥ 15% (watch) |
