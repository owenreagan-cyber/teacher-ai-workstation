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
- Capability map: `docs/teacher-workstation-capability-map.md`
- Long-term future programs (planning index): `docs/long-term-future-programs-roadmap.md`
- AI tool routing matrix: `docs/ai-tool-routing-matrix.md`
- 3D Builder Workshop Agent: `docs/3d-builder-workshop-agent-roadmap.md`
- Phase 3 closure: `docs/teacher-workstation-foundation-v0.md`
- Active handoff: `assistant/memory/active-priorities.md`
- Build queue: `docs/build-queue.md`
- Parked tracks map: `docs/phase-1-chief-of-staff-status-audit.md`

---

## 1. Current State Summary

| Area | State | Summary |
| --- | --- | --- |
| Engineering governance | **Active** | Constitution, senior-engineer workflow, implementation approval gate |
| Chief of Staff | **Strong foundation** | CLI, dashboard, memory, intake, proof runner — daily ops and unified next-action incomplete |
| Phase 3 foundations | **Complete (v0)** | Lesson Planning, Curriculum Library, Renderer, Local Retrieval, Integration Planning |
| Curriculum Builder | **v1 foundation complete** | Registry, 5 contracts, binding, validation — no renderers, real records, or generation |
| Canvas LLM | **Frozen/stopped** | Planning stack complete; stop marker active; no runtime |
| Local LLM | **Active (D1 read-only)** | Program D1 status foundation; no installs/downloads/inference |
| Mac workstation experience | **Scaffold/plan** | Wallpaper foundation stack; teacher modes planned; no live curator/widget |
| Health Monitor / System Updater | **Active** | Read-only foundations complete (Programs H and I) |
| 3D Builder Workshop Agent | **Planned** | `3d-agent/` readiness parked; no CAD/slicing/printing |
| Automation/integrations | **Blocked** | Drive, Canvas API, OAuth, Gmail, Lovable, cloud APIs — all deferred/planning only |

**Baseline proof:** local `main` clean; dashboard healthy (see `bin/chief-of-staff --dashboard`); Phase 3 foundation orchestration active; Canvas LLM stop marker active.

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

### Phase 3 — Teacher Workstation Foundation (complete)

Closure: `docs/teacher-workstation-foundation-v0.md`

| Workstream | Doc |
| --- | --- |
| Lesson Planning Foundation | `docs/lesson-planning-v1-foundation.md` |
| Curriculum Library Foundation | `docs/curriculum-library-v1-foundation.md` |
| Renderer Foundation v1 | `docs/renderer-v1-foundation.md` |
| Local Retrieval Foundation v0 | `docs/local-retrieval-foundation-v0.md` |
| Integration Planning Foundation v0 | `docs/integration-planning-foundation-v0.md` |

### Long-term planning companions (new)

- Capability map: `docs/teacher-workstation-capability-map.md`
- AI tool routing matrix: `docs/ai-tool-routing-matrix.md`
- 3D Builder Workshop Agent: `docs/3d-builder-workshop-agent-roadmap.md`

---

## 3. Major Remaining Programs

| Program | v1 goal (summary) | Current gap |
| --- | --- | --- |
| **Chief of Staff v1 Agent Core** | Central control plane with next-action, briefing, closeout, mode awareness | Command index incomplete; no unified daily briefing |
| **Teacher Workstation Capability Map** | One canonical map of all systems and status labels | **Documented** — maintain with programs |
| **Teacher Workstation Health Monitor** | Observe/report workstation health (manual read-only first) | **Complete** — Program H read-only foundation |
| **Teacher Workstation System Updater** | Read-only update checks → guided plans → approved maintenance | **Complete** — Program I read-only foundation |
| **AI Tool Routing Matrix** | Documented roles for cloud/local/builder tools | **Active** — read-only operational surface; routing inactive |
| **Curriculum Builder Complete** | Registry + contracts + renderers + teacher-reviewed outputs | v1 foundation done; renderers/generation gated |
| **Local LLM / Ollama Workstation** | Local model policy, inventory, health checks | **Active** — Program D1 read-only foundation |
| **Mac Workstation Experience** | Teacher modes, wallpaper, visible transformation | **Active** — Program E1 read-only foundation |
| **Widget and Shortcut Builder** | Catalogs for approved surfaces | Roadmap only |
| **Lovable Classroom App Builder** | Future approval-gated app-builder routing | Planning only — Program G1 |
| **3D Builder Workshop Agent** | Separate sub-agent for classroom objects | `3d-agent/` readiness parked |
| **Canvas Manual Restart** | Bounded manual export when explicitly reopened | Frozen — stop marker |
| **Integration and Automation Layer** | Permissioned connectors when approved | All blocked — last stage |

---

## 4. Recommended Build Order

Priority respects dependencies in `docs/engineering-constitution.md` architectural layers and Phase 3 completion:

```text
 1. Finish Current Phase 3 Foundations (complete — maintain proof)
    Renderer, Local Retrieval, Integration Planning, Program Closure

 2. Chief of Staff v1 Agent Core
    command catalog, next-action, daily briefing, closeout, proof runner,
    status routing, mode awareness

 3. Teacher Workstation Capability Map (maintain with programs)

 4. Teacher Workstation Health Monitor
    manual/read-only first — observe and report only

 5. Teacher Workstation System Updater
    read-only checks → guided plans → approved maintenance only

 6. AI Tool Routing Matrix (maintain; routing remains inactive)

 7. Local LLM / Ollama Workstation
    policy, inventory, health checks — no installs until approved

 8. Curriculum Builder Complete
    real records, renderers, retrieval hooks — approval-gated subtracks

 9. Mac Workstation Experience
    teacher modes, wallpaper, appearance — no Mac changes until approved

10. Widget and Shortcut Builder
    catalogs; manual/local-first first

11. Lovable Classroom App Builder Integration
    future approval-gated; Chief of Staff routes approved ideas only

12. 3D Builder Workshop Agent
    separate sub-agent; classroom objects — no CAD/slicing/printing until approved

13. Canvas Manual Restart
    only after explicit unfreeze; staged C0–C6 sequence

14. Integrations and Automation Layer (final stage)
    Drive/Canvas/OAuth/network/background jobs — explicit mission each
```

**Rationale:** Phase 3 foundations provide coherent status surfaces. Chief of Staff v1 and Health Monitor improve daily execution before write-capable curriculum work. Mac/widgets/Lovable/3D remain planning or approval-gated. Canvas stays frozen until Owen supersedes stop marker. Integrations are intentionally last.

See `docs/teacher-workstation-capability-map.md` for per-capability status labels.

**Standardized planning index:** `docs/long-term-future-programs-roadmap.md` — Future / Approval-Gated / Planning Only entries for Health Monitor, System Updater, AI Tool Routing, Local LLM, Mac Experience, Widgets/Shortcuts, Lovable, and 3D Builder Workshop Agent.

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

### Program B — Chief of Staff v1 Agent Core

**Program goal:** Chief of Staff is the **central control plane** — agent coordinator, status/proof runner, route planner, approval gatekeeper, next-action recommender, and daily/weekly operating assistant.

It should eventually answer:

- What is ready?
- What is blocked?
- What changed?
- What needs Owen?
- What can Cursor do next?
- What can Gemini design next?
- What can Lovable build later?
- What is safe to show students?
- What is safe to export?
- What should I build/review/teach today?

**Future capabilities (roadmap only):**

- command catalog
- next-action recommendation
- daily briefing and closeout
- proof runner consolidation
- status routing across foundation tracks
- mode awareness (Mac Workstation Experience)
- tool routing (see `docs/ai-tool-routing-matrix.md`)
- approval queue surfacing (`docs/implementation-approval-gate.md` intake status)
- blocker queue (frozen tracks, escalation conditions, stop markers)
- health summary (aggregated PASS/WARN/FAIL from Health Monitor)

**Future command ideas (roadmap only unless implemented in approved mission):**

- `bin/chief-of-staff --commands`
- `bin/chief-of-staff --next-action`
- `bin/chief-of-staff --daily-briefing`
- `bin/chief-of-staff --closeout`
- `bin/chief-of-staff --prove-main`
- `bin/chief-of-staff --mode-status`

#### B1 — Command Surface Index v1

```text
Status: COMPLETE (foundation v1_b1)
Closure: docs/chief-of-staff-v1-foundation.md
```

Mission delivered: canonical command index, `--commands`, agent core docs, operating model, proof workflow, v1 foundation status.

#### B2 — Daily Operations Framework

```text
Status: COMPLETE (Program B2)
Closure: docs/chief-of-staff-daily-operations.md
```

Mission delivered: daily operations framework, `--daily-status`, build queue and priority pointers.

#### B3 — Closeout Workflow

```text
Status: COMPLETE (Program B3)
Closure: docs/chief-of-staff-closeout-workflow.md
```

Mission delivered: closeout checklist, `--closeout` read-only template.

#### B4 — Approval and Blocker Queues

```text
Status: COMPLETE (Program B4)
Closure: docs/chief-of-staff-approval-blocker-queues.md
```

Mission delivered: `--approval-queue`, `--blocker-queue` read-only surfacing.

#### B5 — Mode Status / Operating Context

```text
Status: COMPLETE (Program B5)
Closure: docs/chief-of-staff-mode-status.md
```

Mission delivered: `--mode-status` conceptual operating modes (no Mac changes).

#### B6 — Program B Closure

```text
Status: COMPLETE
Closure: docs/chief-of-staff-v1-program-b-closure.md
```

#### B3 (roadmap) — Next-Action Recommendation v1

```text
Status: COMPLETE
Closure: scripts/chief-of-staff-next-action.sh
```

#### B4 (roadmap) — Proof Runner Consolidation

```text
Status: COMPLETE
Closure: scripts/run-workstation-proof.sh
```

#### B5 (roadmap) — Model Routing Proof Surface (documentation only)

```text
Status: PLANNED
```

**Chief of Staff v1 Program B complete when:** B1–B6 done; daily operations, closeout, queues, and mode status documented and tested; dashboard clean; next-action is deterministic and single-sourced. Closure: `docs/chief-of-staff-v1-program-b-closure.md`.

---

### Program C — Canvas Manual Restart (Frozen)

**Status: FROZEN — do not start by default.** Canvas LLM remains stopped until Owen explicitly supersedes the stop marker.

Evidence: `docs/canvas-llm-stop-marker-curriculum-builder-return.md` — stop marker active, default next PR blocked.

**Future restart sequence (approval-gated, in order):**

| Stage | Scope | Status |
| --- | --- | --- |
| C0 — Readiness audit | Frozen foundation proof, contract maturity check, stop-marker review | planning only |
| C1 — Manual package manifest | Read-only validator for manual export package JSON shapes | first mission when unfreezed |
| C2 — Static preview package | Fictional sample packages; local preview only | blocked |
| C3 — Manual copy/paste Canvas-ready content | Human-in-loop export; no API | blocked |
| C4 — Export bundle files | Weekly bundle dry-run validator | blocked |
| C5 — Canvas API planning | OAuth/API architecture docs only | blocked |
| C6 — Canvas API integration | Live Canvas connection | blocked — separate mission |

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

### Program D — Local LLM / Ollama Workstation

**Program goal:** Local model policy, inventory, health checks, and local/cloud split documentation — not automated hybrid routing.

**Planning references:** `assistant/model-routing.md`, `docs/ai-tool-routing-matrix.md`, `setup/08-local-ai.sh`

**Model-family roles (planning only — verify locally before assignment):**

| Family | Planned role |
| --- | --- |
| Gemma / Gemma 3 / Gemma 3n | Lightweight helper; summarization; classification; offline assistant |
| DeepSeek | Technical/code reasoning; validator/debugging assistance — not curriculum authority |
| Qwen | Local coding/general assistant candidate |
| Other | Evaluate by task, safety, speed, memory, quality |

Unconfirmed model variant names remain tentative until locally verified.

#### D1 — Local LLM Status Foundation

```text
Mission: Local LLM workstation read-only status foundation (Program D1)

Scope:
- docs/local-llm-workstation-status-foundation.md
- docs/local-llm-non-activation-boundaries.md
- docs/local-llm-ollama-readiness-plan.md
- scripts/local-llm-workstation-status.sh
- chief-of-staff --local-llm-workstation-status
- checks: repo-local docs, manifest, CLI registration, negative non-activation assertions

Out of scope:
- Ollama install/execution/ping
- model downloads
- model inference
- localhost/port probes
- API key setup
- cloud routing activation

Autonomous: yes (read-only repo-local status only)
```

#### D2 — Secrets/Capability Broker (approval-gated)

Phase 0F scope. Requires explicit approval before any secret storage or API key injection.

**Local LLM v1 complete when:** D1 passing; routing policy documented; Owen can verify local stack from one command; broker approved separately if needed.

---

### Program E — Mac Workstation Experience

**Program goal:** Visible workstation transformation — teacher modes, wallpaper packs, appearance, desktop polish — without unapproved Mac system changes.

**Future teacher modes (planning):**

- Planning Mode
- Teaching Mode
- Curriculum Builder Mode
- Canvas Prep Mode
- Grading / Review Mode
- Focus / Admin Mode
- After-School Closeout Mode

**Future mode surfaces:** wallpaper, appearance, desktop organization, widgets, shortcuts, Chief of Staff dashboard view, active folders, recommended commands.

#### E1 — Mac Experience Read-Only Planning Foundation

```text
Mission: Mac Workstation Experience read-only planning foundation (Program E1)

Scope:
- docs/mac-workstation-experience-foundation.md
- docs/mac-workstation-non-activation-boundaries.md
- docs/mac-workstation-readiness-plan.md
- scripts/mac-workstation-experience-status.sh
- chief-of-staff --mac-workstation-status
- checks: repo-local docs, mode-status cross-link, negative non-activation assertions

Out of scope:
- Mac system setting changes
- wallpaper apply
- widget/shortcut install
- osascript/automation
- live curator/fetcher

Autonomous: yes (read-only repo-local status only)
```

#### E2 — Wallpaper Curator Live v1 (approval-gated)

Requires explicit approval for: image fetching, scheduler, macOS wallpaper apply, notifications.

#### E3 — Vibe Panel v1 (approval-gated)

Per `docs/vibe-panel-roadmap.md` — app build requires separate mission approval.

**Mac Workstation v1 complete when:** approved vibe/wallpaper path operational with human review gates; shortcuts documented; no unattended system mutation.

---

### Program F — Widget and Shortcut Builder

Program F1 read-only catalog foundation complete (`docs/widget-shortcut-builder-catalog-foundation.md`). `--widget-shortcut-status` reports catalog planning boundaries only. No widget install, shortcut install, shortcut execution, or Mac automation.

Deferred live health and install paths until explicit approval per mission. Manual/local-first widgets and shortcuts first — no automation or install without Owen approval.

**Widget Catalog v1 (planning):**

- Chief of Staff Status Widget
- Next Action Widget
- Dashboard Health Widget
- Curriculum Builder Widget
- Lesson Planning Widget
- Canvas Frozen/Ready Widget
- Local LLM Status Widget
- Mode Widget
- Approval Queue Widget
- Today's Teacher Launchpad

**Shortcut Catalog v1 (planning):**

- Open Workstation
- Run Dashboard
- Run Proof Main
- Start Planning Mode
- Start Teaching Mode
- Open Cursor Mission
- Open Gemini Curriculum Architect
- Open Lovable App Builder (manual profile only until G1 approved)
- Capture App Idea
- Capture Resource Note
- Run Daily Briefing
- Run Closeout

---

### Program G — Integration and Automation Layer

**Explicitly deferred — final stage only.** See `docs/phase-1-chief-of-staff-status-audit.md` § What Should Not Be Automated Yet.

**Staged integration model (no stage active without explicit mission approval):**

| Stage | Description | Current |
| --- | --- | --- |
| G0 — Documentation only | Roadmaps, boundaries, inactive manifests | **active** (planning) |
| G1 — Manual links | Browser profiles, paste-only workflows | planning |
| G2 — Local dry-run | Validators and fictional fixtures only | partial (integration planning foundation) |
| G3 — Read-only integration | Local probes without writes | blocked |
| G4 — Write integration | Approved connectors with human gates | blocked |
| G5 — Automation | Background jobs, scheduled tasks | blocked |

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
| Cloud AI APIs (OpenAI/Anthropic/Google) | Blocked — see `docs/ai-tool-routing-matrix.md` |

#### G1 — Lovable Classroom App Builder Integration (Future / Approval-Gated)

```text
Classification: Lovable Classroom App Builder Integration — Future / Approval-Gated
Current status: planning only — not connected
Authority: assistant/model-routing.md, docs/integration-planning-foundation-v0.md
```

**Purpose:** Chief of Staff may eventually route **approved** classroom-app ideas into Lovable for building teacher tools, classroom mini-apps, review games, dashboards, workflow helpers, and other classroom-support apps.

**Architecture rule:** Chief of Staff must **not** become Lovable. Chief of Staff decides, validates, routes, tracks, and provides status. Lovable remains an external app-builder tool used only after an approved classroom-app request passes the safety/implementation gate.

**Tool ecosystem placement:** Lovable sits in the future tool/integration roadmap alongside Gemini, Claude, Cursor, Codex, and other builder/model tools. See `assistant/model-routing.md` and `docs/ai-tool-routing-matrix.md`.

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

### Program H — Teacher Workstation Health Monitor

**Program goal:** A manual/read-only health monitor that checks whether the workstation is healthy.

**Architecture rule:** Health Monitor **observes and reports**. It does not update, install, repair, automate, or modify the system unless a later approved mission explicitly allows it.

```text
Status: COMPLETE (read-only foundation v1_h)
Closure: docs/teacher-workstation-health-monitor-foundation.md
```

Mission delivered: architecture doc, health domains, `--system-health` / `--workstation-health`, `scripts/teacher-workstation-health-status.sh`, dashboard integration, tests.

**Eventually checks (future/live — not in v1_h):**

- Local LLM service and installed model health
- Widget, shortcut, wallpaper/mode live health
- Lovable/cloud tool live integration status
- Disk space / environment readiness

**Commands:**

- `bin/chief-of-staff --system-health` — implemented
- `bin/chief-of-staff --workstation-health` — implemented (alias)
- `bin/chief-of-staff --local-llm-health` — planned
- `bin/chief-of-staff --widget-health` — planned
- `bin/chief-of-staff --shortcut-health` — planned

**Health Monitor v1 complete when:** read-only health report aggregates existing status scripts with PASS/WARN/FAIL footer; no repair or install behavior. **Met.**

---

### Program I — Teacher Workstation System Updater

**Program goal:** Check for and eventually manage **approved** updates to the workstation environment.

**Architecture rule:** System Updater **recommends and applies only approved updates**. Health Monitor and System Updater remain separate: Health Monitor observes/reports; Updater recommends/applies approved changes.

```text
Status: COMPLETE (read-only planning foundation v1_i)
Closure: docs/teacher-workstation-system-updater-foundation.md
```

Mission delivered: architecture doc, update domains, `--system-update-check`, `--system-update-plan`, status/plan scripts, tests, dashboard integration.

| Stage | Scope | Status |
| --- | --- | --- |
| **v0 — read-only planning** | Docs, checklists, repo-local readiness | **complete** |
| **v1 — guided planning** | Recommend updates, manual plans, approval required | future |
| **v2 — approved maintenance** | Apply approved updates only | blocked |

**Commands:**

- `bin/chief-of-staff --system-update-check` — implemented
- `bin/chief-of-staff --system-update-plan` — implemented
- `bin/chief-of-staff --apply-approved-updates` — blocked

**Blocked until approval:** automatic code updates, model downloads, dependency installs, Mac setting changes, widget/shortcut changes, network calls, background jobs, package manager execution.

---

### Program J — 3D Builder Workshop Agent

**Program goal:** Separate future agent/sub-agent for classroom object creation — toys, fidgets, decals, tools, action figures, tokens, badges, manipulatives, and classroom objects.

**Not** Curriculum Builder, Canvas, lesson planning, or curriculum export work. Chief of Staff coordinates and gates; it does not own the asset library or generate 3D files.

**Current status:** Planning only. Readiness stack at `3d-agent/` and `docs/3d-printing-roadmap.md` remains parked. Legacy parked-track string: **3D Design Factory Agent remains parked**.

**Canonical detail:** `docs/3d-builder-workshop-agent-roadmap.md`

**Blocked until approval:** web search, downloads, scraping, CAD/file generation, STL/3MF export, slicer/printer integration, print jobs, model training, APIs, OAuth, network, student data, public publishing.

**Future commands (roadmap only):** `--3d-builder-status`, `--3d-builder-intake-status`, `--3d-builder-library-status`, `--3d-builder-safety-status`, `--3d-builder-roadmap-status`

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
- Connect Lovable, cloud AI APIs, or 3D CAD/slicing/printing pipelines
- Activate Health Monitor repair or System Updater apply without approval mission
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
| Lovable / 3D Builder / cloud API connection | Program G1 / J / routing matrix approval |
| Health Monitor repair or Updater apply | Separate mission per stage |
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
| Chief of Staff | Stable CLI, dashboard, memory, intake, daily ops, next-action | **Partial** — foundation strong; agent core incomplete |
| Capability map | Canonical system map with status labels | **Documented** |
| Health Monitor | Read-only workstation health report | **Active** — Program H foundation |
| System Updater | Read-only update planning | **Active** — Program I foundation |
| AI tool routing | Documented matrix; inactive routing | **Active** — read-only operational surface |
| Local LLM / Ollama | Read-only planning/status foundation | **Active** — Program D1 read-only |
| Curriculum Registry | Approved manual registry with metadata references | **Partial** — v1 fictional foundation |
| Output Contracts | Active contracts wired to registry and review | **Foundation complete** — 5/5 canonical v0 |
| Renderers | ≥1 renderer per primary contract type | **Not started** — interface foundation only |
| Canvas Package Builder | Bounded export path | **Frozen** — planning only |
| Local Retrieval | Approved local lookup | **Foundation complete** — no engines |
| Lesson Generation | Human-reviewed drafts under safety boundaries | **Not started** |
| Mac Workstation Experience | Approved modes and surfaces | **Active** — Program E1 read-only planning |
| Widgets / Shortcuts | Catalogs and manual install path | **Active** — Program F1 read-only catalog |
| 3D Builder Workshop Agent | Gated classroom object pipeline | **Planned** |
| Validation suite | PASS/WARN/FAIL for all active tracks | **Strong** |
| Dashboard | Single local health surface on `main` | **Active** — see `bin/chief-of-staff --dashboard` |

**v1.0 is not a date.** It is an engineering completeness bar.

---

## 10. Immediate Next Recommended Mission

**Lovable Classroom App Builder — Read-Only Planning Surface (Program G1)**

Classroom App Lab Prototype Rescue read-only foundation is complete (`docs/classroom-app-lab-prototype-rescue-foundation.md`). `--classroom-app-lab-status` provides planning visibility only. Recommended next: Lovable integration planning surface without API, OAuth, or live app generation.

Alternate tracks remain approval-gated per `docs/implementation-approval-gate.md`.

**This roadmap does not auto-start implementation.** Owen or an explicit mission prompt authorizes execution.

---

## 11. Program Mission Sequencing (Quick Reference)

```text
COMPLETE:
  Phase 3 Teacher Workstation Foundation (v0)
  Capability map + AI tool routing matrix (documentation)
  H0 Health Monitor read-only foundation
  I0 System Updater read-only checks
  R0 AI Tool Routing operational surface (read-only)
  D1 Local LLM read-only status foundation
  E1 Mac Workstation Experience read-only planning
  F1 Widget/Shortcut catalog read-only foundation
  CAL1 Classroom App Lab prototype rescue read-only foundation

NOW (autonomous pattern when authorized):
  G1 Lovable Classroom App Builder read-only planning surface

THEN (mixed approval):
  A4–A7 Curriculum Builder Complete subtracks
  E* Mac Workstation Experience
  F* Widget and Shortcut Builder catalogs

LATER (approval-gated):
  G1 Lovable Classroom App Builder
  J* 3D Builder Workshop Agent
  C* Canvas LLM restart (explicit unfreeze)
  G* Drive/Gmail/Canvas API/OAuth integrations
  I2 System Updater approved maintenance
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

Documentation/status only. This master build roadmap is Markdown planning text. It does not activate lesson generation, real curriculum content, real review notes, student data, file scanning, folder crawling, indexing, OCR, embeddings, vector database, RAG, Canvas API, Google Drive API, OAuth, network calls, automation, background jobs, live integrations, Lovable connection, cloud AI API routing, Mac system setting changes, wallpaper changes, widget installation, shortcut installation, LLM installation, model downloads, API key setup, 3D file generation, STL/3MF export, slicer integration, printer integration, registry writes, contract writes, renderers, or runtime behavior.

**Implementation does not proceed automatically from this audit.**

---

## Validation

```bash
bash scripts/cursor-workflow-status.sh
bash scripts/phase-1-status.sh
bin/chief-of-staff --dashboard
```
