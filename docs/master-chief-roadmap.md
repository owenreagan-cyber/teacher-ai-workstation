# Master Chief — Product Direction and Development Roadmap

```text
Status: canonical strategic roadmap (Chief platform product direction)
Scope: documentation only — no runtime, UI, or integration activation
Implementation approval: not granted by this document
Baseline verified at: 47f5aff (2026-11-08)
Owner: Owen Reagan
```

This is the **one authoritative roadmap** for the Chief platform: what it is, how it is
architected, and the order in which it gets built. It replaces no security decision and activates
no runtime behavior.

Related authority:

| Document | Role |
| --- | --- |
| `docs/DECISIONS.md` | Settled decisions D-001 through D-028 (authoritative) |
| `docs/NEXT-PHASES.md` | Detailed build order and phase-level acceptance notes |
| `CHIEF-OF-STAFF.md` | Developer README: what exists today, code stack, operational detail |
| `docs/master-build-roadmap.md` | Whole-repository Teacher Workstation v1.0 program roadmap (different scope) |
| `docs/security/p1b4-multi-device-architecture.md` | Accepted multi-device security architecture (P1b.4a) |
| `docs/chief-of-staff-roadmap.md` | Historical Phase 1A–1I roadmap; superseded by this file |

If this document and `docs/DECISIONS.md` disagree, the decision wins.

---

## 1. Naming

Naming is fixed. These names are not interchangeable and not subject to renaming by an agent.

| Name | Meaning |
| --- | --- |
| **Master Chief** | Internal codename for the overall intelligence and orchestration platform |
| **Chief** | The assistant and the product |
| **Chief.app** | The desktop application |
| **cos** | Authoritative core runtime: intelligence, model routing, policy, tools, sessions, memory |
| **cosd** | Persistent daemon: APIs, tasks, execution, devices, recovery |
| **Raycast** | Optional convenience client — never a required dependency |

**Master Chief is a codename, not a replacement product name.** The product is Chief. Codename use
is limited to internal planning documents, branch names, and planning conversations. It must not
appear in user-facing UI, packaging identifiers, marketplace listings, or external marketing.

No other product, character, or franchise name is part of this architecture. Earlier working names
or unrelated references carry no architectural meaning and must not be reintroduced.

---

## 2. Product identity

Chief is a local-first, provider-flexible intelligence and orchestration platform for one teacher's
working life. It answers questions, holds sessions and memory, coordinates specialist agents and
external workers, and performs consequential actions only through deterministic authorization and
explicit human approval.

Chief is not a chat wrapper. The value is the core: one place that owns routing, policy, task state,
memory, and audit, with many interchangeable surfaces on top.

---

## 3. Architecture

One authoritative intelligence and orchestration core. Surfaces are clients. No surface invents
state, and no surface is the system of record.

```text
 SURFACES
   Chief.app (primary graphical interface)
   Terminal (supported administrative interface)
   Raycast (optional convenience client)
   Mobile clients (future independent interfaces)

        │  authenticated local API
 ┌──────▼───────────────────────────────────────────────────────────────┐
 │ cos — authoritative core runtime                                     │
 │   intelligence · model routing · policy · tools · sessions · memory   │
 └──────┬───────────────────────────────────────────────────────────────┘
        │  in-process authority
 ┌──────▼───────────────────────────────────────────────────────────────┐
 │ cosd — persistent runtime                                            │
 │   APIs · tasks · execution · devices · recovery                      │
 └──────┬───────────────────────────────────────────────────────────────┘
        │
   Local models (Ollama) · optional cloud models · cloud agent CLIs · tools
```

Ownership rules:

- **cos owns intelligence, model routing, policy, tools, sessions, and memory.** Authority is code
  (D-003). Models propose; the core decides.
- **cosd owns persistent APIs, tasks, execution, devices, and recovery.** Task state survives any
  model context (D-025).
- **Chief.app is the primary graphical interface** and must be able to exercise the full capability
  set without any other client installed.
- **Terminal is a supported administrative interface**, not a second-class fallback.
- **Raycast is optional.** It is a convenience launcher over the same runtime.
- **Mobile clients are future independent interfaces**, not remote mirrors of the desktop window.

---

## 4. Core principles

1. **Local-first.** The system works on Owen's machine without a network. Cloud is an option, never
   a prerequisite.
2. **Provider-flexible.** Models and workers are interchangeable configurations. No capability is
   welded to one vendor.
3. **Deterministic authorization.** Code owns the policy gate and the executor. Unknown, failed, or
   timed-out checks resolve to deny.
4. **Durable execution.** Tasks, missions, and approvals are persisted and resumable; a retry
   resumes from recorded state.
5. **Centralized memory.** One memory authority with typed items and explicit recall, not per-client
   stores.
6. **Shared task state.** Every surface observes the same task records.
7. **Independent device identities.** Each device has its own credential and permission profile; no
   shared master token for new devices (D-018, ADR-021).
8. **Human approval for consequential operations.** Writes, sends, purchases, grade changes, and
   deletions require a sealed approval packet plus execution-time re-check (D-018, D-022).
9. **No surprise cloud spending.** Entitlements, caps, and budgets are enforced in code, not in
   prompts (D-022 control 4, D-026).

---

## 5. Status vocabulary

Roadmap items use exactly one of these labels. They are not synonyms.

| Label | Meaning |
| --- | --- |
| **Designed** | Architecture or decision accepted; no working code |
| **Implemented** | Code exists on `main` and is covered by automated tests in CI |
| **Tested** | Exercised against realistic conditions with recorded evidence |
| **Deployed** | Running in the place people actually use it, with provenance recorded |
| **Production-ready** | Deployed, certified, documented, and supportable without the author present |

**Source implementation is not deployment.** A merged pull request with passing CI proves
"Implemented". It does not prove "Deployed" or "Production-ready", and this roadmap never claims it
does.

---

## 6. Verified baseline

Verified against `main` at `47f5aff`. Every row below is bounded by its evidence.

### Platform foundation

| Item | What it is | Status |
| --- | --- | --- |
| P1b.1a | Loopback `cosd`, authenticated HTTP, lifecycle CLI, `run_ask` integration | **Implemented** |
| P1b.1b | SQLite task registry, task APIs, idempotency, event history | **Implemented** |
| P1b.1c | Execution queue, worker leases, checkpoints, startup recovery, handlers | **Implemented** |
| P1b.1d | `bin/cos` smart client with standalone fallback | **Implemented** |
| P1b.1e | Chief.app uses loopback `cosd` for ask, status, and task center | **Implemented** |
| P1b.2 | Local operations: lifecycle controls, SSE task events, notifications, runtime snapshot, chunked ask stream | **Implemented** |
| P1b.3 | Raycast extension as a `cosd` client | **Implemented** (optional client) |

### Multi-device track

| Item | What it is | Status |
| --- | --- | --- |
| P1b.4a | Multi-device security architecture, ADR-021, threat model | **Designed** (accepted) |
| P1b.4b | Local device registry, permission profiles, Keychain-backed credential references, rotation/revocation, `/v1/devices`, Devices screen | **Implemented** (local only) |
| P1b.4c | Local pairing and enrollment: one-time codes, QR payloads, owner approval, X25519/HKDF/AES-GCM credential delivery, replacement | **Implemented** (local only) |
| P1b.4d | Tailscale, TLS gateway, ACLs, remote enrollment | **Designed only — not implemented** |

`cosd` binds `127.0.0.1` only. No gateway process ships. Remote access, remote pairing, Tailscale,
and remote credential delivery are **not activated**.

### Deployment reality

| Item | Finding | Status |
| --- | --- | --- |
| Chief.app source | `apps/chief-desktop` at version `0.1.0` | **Implemented** |
| Chief.app installed build | No installed build found in standard application locations at audit time; source and installed versions are not reconciled | **Unknown — P0 work** |
| Provenance-stamped package | Not produced | **Designed only — P0 work** |
| Certified `cosd` startup and auth on the working machine | Not recorded as a certification artifact | **Unknown — P0 work** |

These three unknowns are the reason P0 exists. Until they are closed, no part of Chief should be
described as deployed or production-ready.

---

## 7. Development sequence

Program order is deliberate. P1 depends on P0 because a mission/approval system that only runs in a
source checkout is not a system Owen can rely on.

### P0 — Operational deployment and certification

**Objective:** make the existing platform installable, certifiable, and trustworthy in daily use.

- Reconcile source and installed Chief.app versions.
- Resolve reproducible dependencies for the daemon, desktop app, and evaluator.
- Certify `cosd` startup and authentication on the working machine.
- Verify the device registry and pairing dependency chain end to end.
- Prepare a provenance-stamped Chief.app package.
- **Owner approval before any live application replacement.**

**Exit criteria:** a signed package with recorded provenance is installed by Owen, `cosd`
startup/authentication is certified with evidence, and source, package, and installed versions all
agree.

**Non-goals:** new features, remote access, and UI redesign.

### P1 — Mission and approval infrastructure

**Objective:** turn one-off tasks into durable, verifiable missions with sealed approvals.

- Durable mission records (identity, objective, scope, owner, state, evidence).
- Task-to-mission relationships, so every task belongs to something.
- Dependency graph across tasks and missions.
- Sealed approval packets extending D-018: canonical hash, expiry, replay state, target before-state.
- Execution-time authorization: re-check the sealed packet and every target at the moment of action;
  stale approvals fail closed (D-005, D-025).
- Recovery and verification: resume after partial completion; verify the result against the packet.
- Chief.app mission and approval interfaces as the primary surface.

**Exit criteria:** a mission containing a consequential write completes, fails closed on a stale
approval, resumes after interruption, and verifies its own result — with no surface able to edit a
sealed packet.

### P2 — Housekeeper

**Objective:** scoped storage intelligence with no unapproved deletion.

- Scoped file inventory within explicitly approved roots.
- Duplicate detection.
- Storage intelligence: what is large, stale, or redundant.
- Cleanup proposals as reviewable packets.
- Quarantine and approved cleanup with a restore path (D-005: no permanent deletion).

**Exit criteria:** a real cleanup round produces proposals only, executes only after approval, and
every removal is restorable.

### P3 — Secretary

**Objective:** calendar, reminders, and mail triage with approval before sending.

- Calendar awareness and conflict surfacing.
- Reminders and follow-up tracking.
- Email triage, read-only first (D-013).
- Follow-up tracking across threads and commitments.
- Draft communications.
- **Approval before sending** (D-022 control 3).

**Exit criteria:** a draft is produced, approved as a sealed packet, sent, and audited — and no send
is possible without that approval.

### P4 — Development HQ

**Objective:** one place to see and direct Owen's development work.

- Repository inventory across local projects.
- Cursor / Codex / Claude session and usage tracking (D-019, D-026).
- Build and PR monitoring.
- Controlled worker dispatch through the deterministic orchestrator (D-023).
- Isolated worktrees per dispatched job.
- Independent review from a different model family (D-010).

**Exit criteria:** a coding mission is dispatched, runs in an isolated worktree, returns a reviewed
diff, and Owen sees the diff plus both reports in Chief.app.

### P5 — Shared intelligence

**Objective:** make the agent and service layer reusable by any approved client.

- Agent registry: configuration, not processes (D-023).
- Deterministic orchestrator that validates plans against registry and permissions.
- Shared memory across agents with one authority.
- Canonical service interfaces in the core.
- MCP adapters as thin, read-only-first adapters over the same services (D-024).
- Agent Skills as a portable packaging format.
- ACP evaluation for interoperability, with no premature adoption.

**Exit criteria:** an external approved client performs a read-only task through an MCP adapter with
identical logic, identical permissions, and full audit.

### P6 — Model optimization

**Objective:** spend the least for adequate quality, with no surprise cost.

- Provider abstraction across local and remote models.
- Ollama plus optional cloud model adapters.
- Entitlement-aware routing using measured, current access (D-026).
- Budget controls and per-service spending caps (D-022 control 4).
- Evaluation harness for answer quality and routing decisions.
- GEPA and model training **only when justified by recorded evidence** — never speculatively.

**Exit criteria:** routing decisions are explained per request, caps are enforced in code, and an
evaluation shows the cheaper path meets the quality bar.

### Parallel multi-device track

This track runs alongside P0–P6 but never blocks or gates local specialist development.

| Item | Scope | Status |
| --- | --- | --- |
| P1b.4d | Tailscale, TLS gateway, ACLs, remote enrollment activation | **Designed — not implemented** |
| P1c | iPhone / iPad native clients (D-007) | **Designed — not implemented** |
| P1d | Full device management: fleet view, policy assignment, revocation at scale | **Designed — not implemented** |

Remote access stays separate from local specialist development. A slow month on the gateway must
never stall P1–P6, and P1b.4d must never be used to justify shipping a feature that depends on remote
connectivity.

---

## 8. Chief.app independence

This is a **permanent architecture requirement**, not a phase goal.

Removing Raycast — or never installing it — must not affect:

- Chat
- Sessions
- Memory
- Model routing
- Tasks
- Missions
- Approvals
- Agent execution
- Devices
- Notifications
- Recovery

Obligations that follow from this:

1. **Chief.app is the primary full-featured interface.** Every capability in the list above must be
   reachable and complete in Chief.app alone.
2. **Raycast remains an optional convenience integration.** It may accelerate access; it may not own
   a capability.
3. **No capability may be implemented only in Raycast** or only in the terminal.
4. **No shared state may live in a Raycast-only store.** Raycast reads and writes through the same
   authenticated runtime as every other client.
5. **Verification is behavioral.** A future acceptance test must demonstrate that the listed
   capabilities work with Raycast absent, not merely that they compile.

This document records the requirement. It does not implement UI or runtime changes.

---

## 9. Decision alignment

This roadmap is consistent with the accepted decisions and does not modify them. D-018 through D-028
remain exactly as recorded in `docs/DECISIONS.md`.

| Decision | How this roadmap uses it |
| --- | --- |
| D-003 | Code owns authority; every surface is a client |
| D-005 | Every write needs an approval packet; deletions go to quarantine |
| D-010 | Security, privacy, authority, and routing phases get a cross-model reviewer |
| D-013 | Mail is read-only to start |
| D-018 | Approval packets are server-authoritative and re-checked at execution |
| D-019 | Registries separate workers, environments, and services |
| D-022 | Four strict controls remain: Canvas writes, grades, send/purchase/delete, spending caps |
| D-023 | Agents are configurations; the orchestrator is deterministic code |
| D-024 | Canonical services in the core; MCP is a thin, read-only-first adapter |
| D-025 | Task records are durable, resumable, cancellable, and re-checked |
| D-026 | Real entitlements drive routing |
| D-027 | The Canvas Planner owns Canvas weekly planning |
| D-028 | The Canvas rollover engine is the only publisher of the weekly package |

Anti-drift rules for future agents:

- Do not weaken D-018 execution-time re-checking to make a UI simpler.
- Do not expose Canvas writes through MCP.
- Do not move authorization into prompts, the UI, or a proxy.
- Do not add a required dependency on Raycast.
- Do not relabel "Implemented" as "Deployed" without evidence.

---

## 10. Content integrity

Two classes of defect are explicitly excluded from this architecture and its documentation:

- **Unrelated fictional or franchise references.** Names from television, film, or games are not
  product names, architecture concepts, roadmap items, or example personas.
- **Accidental non-English text.** Chinese characters or other substituted text appearing where
  English prose is intended indicate an insertion error, not a localisation feature.

One intentional exception exists and stays: `evals/suites/robustness.jsonl` contains a non-English
input fixture (`rb-lang-002`) beside a Spanish fixture and emoji cases. That is a deliberate
input-robustness test, it predates this roadmap, and it is legitimate test content. It is not
contamination and must not be removed.

Any future finding of this kind in Chief documentation should be treated as a defect: locate the
introducing commit, report it, and correct the text without rewriting unrelated history.

---

## 11. What this document does not do

- It does not activate runtime behavior, integrations, network calls, or generation.
- It does not approve implementation of P0–P6.
- It does not change any accepted decision.
- It does not modify the Teacher Workstation or Canvas roadmaps.
- It does not delete historical planning documents.

Implementation proceeds only through explicit approved missions under
`docs/implementation-approval-gate.md`.
