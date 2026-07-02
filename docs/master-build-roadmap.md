# Master Build Roadmap

Last updated: 2026-07-02

```text
Status: documentation/status only
Roadmap status: active
Implementation approval status: not approved by default
Automatic implementation: no — this document does not authorize runtime work
Authority: canonical program roadmap for Teacher AI Workstation v1.0
```

## Purpose

This document is the **canonical program roadmap** for completing Teacher AI Workstation. It synthesizes current repository state, defines major build programs, sequences mission-level work, and clarifies what Cursor may do autonomously versus what requires Owen approval.

**This audit does not activate any implementation.** Future work proceeds only through explicit approved missions under `docs/engineering-constitution.md` and `docs/implementation-approval-gate.md`.

Cross-references:

- Engineering authority: `docs/engineering-constitution.md`
- Approval gate: `docs/implementation-approval-gate.md`
- Active handoff: `assistant/memory/active-priorities.md`
- Build queue: `docs/build-queue.md`
- Parked tracks map: `docs/phase-1-chief-of-staff-status-audit.md`

---

## 1. Current State Summary

| Area | State | Summary |
| --- | --- | --- |
| Engineering governance | **Active** | Constitution, senior-engineer workflow, implementation approval gate |
| Chief of Staff | **Strong foundation** | ~124 CLI flags, dashboard 91/91, memory, intake, workflows — gaps in daily ops and unified next-action |
| Curriculum Builder | **Phase 2 v0 partial** | Registry, Output Contract, Binding, 2 canonical contracts — no renderers, ingestion, or generation |
| Canvas LLM | **Frozen/stopped** | Planning stack complete; stop marker active; no runtime |
| Local LLM | **Setup only** | Ollama installer/verify; `assistant/model-routing.md` is policy doc only |
| Mac workstation experience | **Scaffold/plan** | Phase 0E Vibe Engine complete; wallpaper foundation stack; no live curator/widget |
| Automation/integrations | **Blocked** | Drive, Canvas API, OAuth, Gmail, secrets broker, background jobs, Lovable — all deferred/planning only |

**Baseline proof (post Phase 2 Missions 1–4):** local `main` clean; dashboard PASS 91 / WARN 0 / FAIL 0; Curriculum Builder foundation status PASS ~1103; Canvas LLM status PASS ~629.

---

## 2. Completed Foundations

### Governance and workflow

- Engineering Constitution (`docs/engineering-constitution.md`)
- Implementation Approval Gate (`docs/implementation-approval-gate.md`)
- Senior Engineer Cursor rules (`.cursor/rules/teacher-ai-workstation-senior-engineer.mdc`)
- Cursor workflow OS, prompt template, PR checklist
- Section completion audits (Curriculum Builder, Canvas LLM)

### Chief of Staff (Phase 1)

- Interactive CLI (`bin/chief-of-staff`)
- Status dashboard (`bin/chief-of-staff --dashboard`)
- Project memory, writing style memory, intake review queue
- Lesson planning scaffold (brief, draft, pack, review, notes helpers)
- Developer Mode templates
- Workflow polish stack (command map, help examples, quick-start, section summaries)

### Curriculum Builder — planning (complete)

- Full planning stack (PRs #107–#162): schema plans, sample proofs, approval gate, closeout audits
- Output contract planning foundation, static source registry plan

### Curriculum Builder — Phase 2 v0 (implemented, read-only)

| Mission | Deliverable | Doc |
| --- | --- | --- |
| Mission 1 | Registry v0 | `docs/curriculum-registry-v0.md` |
| Mission 2 | Output Contract Schema v0 | `docs/curriculum-output-contract-v0.md` |
| Mission 3 | Registry–Contract Binding v0 | `docs/curriculum-binding-v0.md` |
| Mission 4 | Teacher Script Contract v0 | `docs/curriculum-teacher-script-contract-v0.md` |

### Canvas LLM — planning (complete, frozen)

- Planning foundation capstone, closure audit, index, freeze, handoff snapshot, stop marker
- Manual export package/review/checklist/bundle placeholder plans

### Mac / Appearance — foundation (planning)

- Wallpaper/photo curator foundation stack (validators, schemas, dry-run helpers)
- Vibe Panel roadmap (explicit: do not build app yet)

### Local LLM — installer baseline

- `setup/08-local-ai.sh`, `assistant/model-routing.md`, dashboard LLM CLI readiness probe

---

## 3. Major Remaining Programs

| Program | v1 goal (summary) | Current gap |
| --- | --- | --- |
| **Curriculum Builder Complete** | Approved registry + contracts + binding + renderers + teacher-reviewed outputs | v0 only; 3 contract placeholders; no real records; no renderers |
| **Chief of Staff v1** | Stable daily operating system with next-action clarity | No daily-ops mode; build-queue parsing only; model routing doc-only |
| **Canvas LLM Restart and Completion** | Bounded manual export path when explicitly reopened | Entire runtime track frozen; stop marker blocks default PRs |
| **Local LLM Workstation Setup** | Reliable local model ops with documented routing policy | No capability broker; no automated routing; Phase 0F secrets deferred |
| **Mac Workstation Experience** | Coherent desktop/vibe command center | Plans exceed implementation; wallpaper curator not live |
| **Widget and Shortcut Builder** | Approved shortcuts/widgets for teacher workflows | Roadmap only; no WidgetKit/Shortcuts install |
| **Integration and Automation Layer** | Permissioned connectors when approved | Gmail/Drive/Canvas API/OAuth all blocked |

---

## 4. Recommended Build Order

Priority respects dependencies in `docs/engineering-constitution.md` architectural layers:

```text
1. Curriculum Builder Complete (contracts → renderers → retrieval hooks)
2. Chief of Staff v1 (operating system while building)
3. Local LLM Workstation Setup (supports generation/review when approved)
4. Mac Workstation Experience (teacher-facing polish)
5. Widget and Shortcut Builder (surfaces approved commands)
6. Canvas LLM Restart and Completion (only after explicit unfreeze + Curriculum Builder maturity)
7. Integration and Automation Layer (last; permission-gated)
```

**Rationale:** Registry and contracts must stabilize before renderers and Canvas packaging. Chief of Staff v1 improves daily execution during long builds. Canvas remains frozen until Owen explicitly supersedes the stop marker. Integrations are intentionally last.

---

## 5. Mission-Level Roadmap

### Program A — Curriculum Builder Complete

**Program goal:** Teacher-reviewed, local-first curriculum metadata and artifact pipeline from registry through contracts to renderers — without unapproved scanning, ingestion, or student data.

#### A1 — Worksheet Contract Schema v0 (next recommended)

```text
Mission: Promote worksheet_contract to third canonical output contract

Scope:
- worksheet-contract-schema.json
- contracts/sample-worksheet-001.json
- placeholder-manifest canonical_contracts update
- output contract validator extension
- binding integration
- tests and docs/curriculum-worksheet-contract-v0.md

Out of scope:
- worksheet generation
- PDF/HTML output
- real curriculum content
- registry writes
- scanning/ingestion

Autonomous: yes (same pattern as Missions 2–4)
Approval: mission authorization under Phase 2 track (bounded v0)

Definition of done:
- fictional sample passes validator
- invalid fixture fails
- binding lookup includes worksheet contract
- dashboard clean
- PR merged with proof
```

#### A2 — Review Game Contract Schema v0

Same pattern as A1 for `review_game_contract`.

#### A3 — Canvas Export Package Contract Schema v0 (metadata only)

Promote `canvas_export_package_contract` placeholder to canonical **metadata** contract. No Canvas API, no package building.

#### A4 — Registry v0.2 Manual Entry Dry-Run

```text
Mission: Registry manual entry CLI (validate-before-write dry-run only)

Scope:
- read-only default; --dry-run validates proposed record JSON
- optional --write only with explicit flag + Owen approval mission
- fictional samples remain default

Out of scope:
- Drive/NAS scanning
- folder crawling
- live resolution

Autonomous: dry-run portion yes; --write requires separate approval mission
```

#### A5 — Real Registry Records (approval-gated)

Replace fictional `sample-*` records with Owen-approved real metadata. Requires completed decision intake and explicit no-student-data confirmation.

#### A6 — Renderer Foundation (approval-gated)

First teacher-reviewed renderer for one contract type (likely DI slide deck or teacher script). Separate intake per `docs/implementation-approval-gate.md` validators/renderers checklist.

#### A7 — Local Retrieval Hooks (approval-gated)

Approved lookup/index over registry + contracts without vector DB or RAG.

**Curriculum Builder v1 complete when:** approved real registry (or governed fictional production path), all five contract types canonical, binding operational, at least one renderer per primary contract, validation suite green, documentation complete — per `docs/engineering-constitution.md` §10.

---

### Program B — Chief of Staff v1

**Program goal:** Owen can open one surface each day and know status, next action, and safe commands — without hunting docs.

#### B1 — Command Surface Index v1

```text
Mission: Complete Chief of Staff v1 command surface

Scope:
- canonical command index doc (grouped by program)
- help text alignment audit
- dashboard section labels match index
- smoke tests for critical commands

Out of scope:
- new runtime features
- automation

Autonomous: yes

Definition of done:
- docs/chief-of-staff-command-index-v1.md (or equivalent)
- cursor-workflow + foundation status checks
- dashboard clean
```

#### B2 — Daily Status Summary

```text
Mission: Single daily status summary command

Scope:
- bin/chief-of-staff --daily-status (read-only)
- aggregates: dashboard summary, active priorities excerpt, build-queue next item
- PASS/WARN/FAIL footer

Out of scope:
- email/notifications
- background scheduler

Autonomous: yes
```

#### B3 — Next-Action Recommendation v1

```text
Mission: Unified next-action recommendation

Scope:
- parse master-build-roadmap + build-queue + active-priorities
- deterministic recommendation string (not LLM-generated)
- dashboard "Next Recommended Action" section uses same source

Out of scope:
- autonomous mission start without approval
- LLM inference for ranking

Autonomous: yes
```

#### B4 — Proof Runner Consolidation

```text
Mission: Single proof runner for pre-merge validation

Scope:
- scripts/run-workstation-proof.sh calling track validators + smoke tests
- documented in cursor workflow guide

Out of scope:
- CI changes unless separately approved

Autonomous: yes
```

#### B5 — Model Routing Proof Surface (documentation only)

```text
Mission: Model routing status proof (no automated routing)

Scope:
- bin/chief-of-staff --model-routing-status
- reports: assistant/model-routing.md boundaries, llm CLI probe, Ollama reachability (local only)
- docs update

Out of scope:
- API keys
- cloud routing implementation
- model downloads

Autonomous: yes for status; routing implementation requires approval
```

**Chief of Staff v1 complete when:** B1–B4 done; dashboard clean; daily workflow documented; next-action is deterministic and single-sourced.

---

### Program C — Canvas LLM Restart and Completion

**Status: FROZEN — do not start by default.**

Evidence: `docs/canvas-llm-stop-marker-curriculum-builder-return.md` — stop marker active, default next PR blocked.

**Safe restart prerequisites (all required):**

1. Owen explicitly approves superseding stop marker
2. Named PR with explicit scope and reason to reopen
3. Completed decision intake per implementation gate
4. Curriculum Builder contracts sufficiently mature for Canvas package references
5. Dry-run default, rollback plan, no-student-data confirmation
6. Separate approval if Canvas API, Drive API, OAuth, or network proposed

**First restart mission (when approved):**

```text
Mission: Canvas LLM Manual Export Dry-Run v0

Scope:
- read-only validator for manual export package JSON shapes
- fictional sample packages only
- chief-of-staff status command

Out of scope:
- Canvas API
- browser automation
- live export
- OAuth

Autonomous: only after explicit unfreeze approval from Owen
```

**Canvas LLM v1 complete when:** bounded manual export path operational with teacher review checklist runner (human-in-loop), weekly bundle dry-run validator, completion status tracking — all local-first, API only if separately approved.

---

### Program D — Local LLM Workstation Setup

**Program goal:** Documented, verifiable local model operations aligned with `assistant/model-routing.md` — not automated hybrid routing.

#### D1 — Local LLM Status Foundation

```text
Mission: Local LLM workstation status proof

Scope:
- docs/local-llm-workstation-v1.md
- scripts/local-llm-workstation-status.sh
- chief-of-staff --local-llm-workstation-status
- checks: ollama binary, service reachability (local), llm CLI, model-routing doc

Out of scope:
- model downloads
- API key setup
- cloud routing

Autonomous: yes (read-only probes only)
```

#### D2 — Secrets/Capability Broker (approval-gated)

Phase 0F scope. Requires explicit approval before any secret storage or API key injection.

**Local LLM v1 complete when:** D1 passing; routing policy documented; Owen can verify local stack from one command; broker approved separately if needed.

---

### Program E — Mac Workstation Experience

**Program goal:** Coherent teacher desktop experience — vibe, wallpaper, shortcuts — without unapproved system changes.

#### E1 — Mac Experience Audit Doc

Document what has actually changed on Mac vs repo-only plans (`setup/` scripts run state).

#### E2 — Wallpaper Curator Live v1 (approval-gated)

Requires explicit approval for: image fetching, scheduler, macOS wallpaper apply, notifications.

#### E3 — Vibe Panel v1 (approval-gated)

Per `docs/vibe-panel-roadmap.md` — app build requires separate mission approval.

**Mac Workstation v1 complete when:** approved vibe/wallpaper path operational with human review gates; shortcuts documented; no unattended system mutation.

---

### Program F — Widget and Shortcut Builder

Deferred until Chief of Staff v1 command index exists. Builds Raycast/Shortcuts surfaces for approved commands only — no install without Owen approval per mission.

---

### Program G — Integration and Automation Layer

**Explicitly deferred.** See `docs/phase-1-chief-of-staff-status-audit.md` § What Should Not Be Automated Yet.

| Integration | Status |
| --- | --- |
| Google Drive API | Blocked — Level 3 permission later |
| Gmail | Blocked — Level 4 permission later |
| Canvas API | Blocked — Canvas stop marker |
| Lovable Classroom App Builder | Blocked — future / approval-gated; see Program G1 and `assistant/model-routing.md` |
| OAuth / secrets | Blocked — capability broker Phase 0F |
| Background jobs / cron | Blocked unless explicit mission |
| Folder scanning / indexing | Blocked — separate intake |
| RAG / vector DB | Blocked |

#### G1 — Lovable Classroom App Builder Integration (Future / Approval-Gated)

```text
Classification: Lovable Classroom App Builder Integration — Future / Approval-Gated
Current status: planning only — not connected
Authority: assistant/model-routing.md, docs/integration-planning-foundation-v0.md
```

**Purpose:** Chief of Staff may eventually route **approved** classroom-app ideas into Lovable for building teacher tools, classroom mini-apps, review games, dashboards, workflow helpers, and other classroom-support apps.

**Architecture rule:** Chief of Staff must **not** become Lovable. Chief of Staff decides, validates, routes, tracks, and provides status. Lovable remains an external app-builder tool used only after an approved classroom-app request passes the safety/implementation gate.

**Tool ecosystem placement:** Lovable sits in the future tool/integration roadmap alongside Gemini, Claude, Cursor, Codex, and other builder/model tools. See `assistant/model-routing.md`.

**Allowed now:**

- roadmap references
- tool-role mapping
- future integration boundaries
- Chief of Staff routing concept documentation
- approval-gated status language

**Blocked until explicit future approval:**

- Lovable API use
- OAuth and credentials
- network calls
- live app generation
- classroom app deployment
- automation
- student data
- generated student-facing apps
- any live integration

**Future relationship to Renderer Foundation:** Approved renderer/output-contract patterns may later inform classroom-app builds in Lovable. See `docs/renderer-v1-foundation.md` §8 Future Downstream Tool Surfaces.

**Non-activation:** This roadmap entry does not connect Lovable, authorize APIs, or activate app generation.

---

## 6. What Cursor May Do Autonomously

Within an **explicitly authorized mission** (like Phase 2 Missions 1–4):

- Pull, branch, implement bounded scope, test, PR, merge, cleanup, proof
- Add docs, status scripts, tests, fictional samples
- Extend PASS/WARN/FAIL validators (read-only)
- Update cross-links, build queue, active priorities (preserving invariant strings)
- Sequence sub-PRs inside the approved program

**Without additional approval, Cursor must not:**

- Unfreeze Canvas LLM
- Add network calls, APIs, OAuth, secrets
- Generate lessons, reviews, or real curriculum content
- Scan folders, ingest files, build RAG/embeddings
- Change Mac system settings, install widgets/shortcuts
- Download models or configure API keys
- Change PASS/WARN/FAIL semantics or remove existing commands
- Start implementation solely because this roadmap exists

---

## 7. What Requires Owen Approval

| Decision | Gate |
| --- | --- |
| Any new implementation track | `docs/implementation-approval-gate.md` intake |
| Real registry records (non-fictional) | Curriculum Builder gate + no-student-data confirmation |
| Renderers, generation, retrieval | Track-specific checklists |
| Canvas LLM reopen | Stop marker supersession + named PR |
| Drive/Gmail/Canvas API/OAuth | Permission levels + separate PR |
| Mac wallpaper/widget/shortcut install | Explicit mission per change |
| Secrets/capability broker | Phase 0F approval |
| Automation/background jobs | Implementation gate automation checklist |
| Semantic changes to dashboard/commands | Constitution escalation |

---

## 8. Stop and Escalation Conditions

Cursor stops and asks Owen when conditions in `docs/engineering-constitution.md` §8 apply, including:

- hard repo boundary violation
- runtime/API/generation needed but not approved
- student data or real curriculum content required
- existing invariants would change
- equally valid architectural forks

---

## 9. Version 1.0 Definition of Complete

Per `docs/engineering-constitution.md` §10, v1.0 means these systems exist as **approved, teacher-reviewed, locally operable capabilities** with validation proof:

| System | v1 requirement | Current |
| --- | --- | --- |
| Chief of Staff | Stable CLI, dashboard, memory, intake, status orchestration | **Partial** — foundation strong; daily ops incomplete |
| Curriculum Registry | Approved manual registry with metadata references | **Partial** — v0 fictional only |
| Output Contracts | Active contracts wired to registry and review | **Partial** — 2/5 canonical |
| Renderers | ≥1 renderer per primary contract type | **Not started** |
| Canvas Package Builder | Bounded export path | **Frozen** — planning only |
| Local Retrieval | Approved local lookup | **Not started** |
| Lesson Generation | Human-reviewed drafts under safety boundaries | **Not started** |
| Validation suite | PASS/WARN/FAIL for all active tracks | **Strong** for implemented tracks |
| Dashboard | Single local health surface on `main` | **Active** — 91/91 |

**v1.0 is not a date.** It is an engineering completeness bar.

---

## 10. Immediate Next Recommended Mission

**Phase 2 Mission 5 — Worksheet Contract Schema v0**

Promote `worksheet_contract` from placeholder to third canonical contract using the established Mission 2–4 pattern. Cursor may execute autonomously under Phase 2 bounded implementation authority.

**This roadmap does not auto-start Mission 5.** Owen or an explicit mission prompt authorizes execution.

---

## 11. Program Mission Sequencing (Quick Reference)

```text
NOW (authorized pattern):
  A1 Worksheet Contract v0
  A2 Review Game Contract v0
  A3 Canvas Export Package Contract v0 (metadata)

THEN (mixed approval):
  A4 Registry manual entry dry-run (autonomous)
  B1–B4 Chief of Staff v1 (autonomous)
  D1 Local LLM status (autonomous)

LATER (approval-gated):
  A5 Real registry records
  A6 Renderer foundation
  A7 Local retrieval
  C* Canvas restart (explicit unfreeze)
  E* Mac live experience
  G* Integrations
```

---

## 12. Cursor Operating Model Going Forward

**Prefer large program missions over narrow ad hoc PR prompts.**

Each program mission should specify:

- scope, out-of-scope, definition of done
- autonomous authority or approval requirement
- validation commands
- expected PR count (Cursor sequences internally)

Owen approves **programs and boundaries**; Cursor owns **PR sequencing, implementation, validation, merge, and proof** within those boundaries.

---

## 13. Non-Activation Confirmation

Documentation/status only. This master build roadmap is Markdown planning text. It does not activate lesson generation, real curriculum content, real review notes, student data, file scanning, folder crawling, indexing, OCR, embeddings, vector database, RAG, Canvas API, Google Drive API, OAuth, network calls, automation, background jobs, live integrations, Mac system setting changes, wallpaper changes, widget installation, shortcut installation, LLM installation, model downloads, API key setup, registry writes, contract writes, renderers, or runtime behavior.

**Implementation does not proceed automatically from this audit.**

---

## Validation

```bash
bash scripts/cursor-workflow-status.sh
bash scripts/phase-1-status.sh
bin/chief-of-staff --dashboard
```
