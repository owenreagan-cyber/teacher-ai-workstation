# Long-Term Future Programs — Planning Roadmap

Last updated: 2026-07-02

```text
Status: documentation/status only
Classification: Future / Approval-Gated / Planning Only
Implementation: not connected — no runtime behavior authorized
Authority: companion to docs/master-build-roadmap.md
```

## Purpose

This document is the **standardized planning index** for approved long-term Teacher AI Workstation programs. Each entry uses consistent status language. Chief of Staff orchestrates, validates, routes, and tracks — it does not become any specialized builder below.

Cross-references:

- Master program sequence: `docs/master-build-roadmap.md` §4
- Capability map: `docs/teacher-workstation-capability-map.md`
- AI tool routing: `docs/ai-tool-routing-matrix.md`
- 3D Builder detail: `docs/3d-builder-workshop-agent-roadmap.md`

---

## Architecture Notes — Subsystem Boundaries

Chief of Staff:

- orchestrates
- validates
- routes
- tracks status

Chief of Staff does **not** become:

| Subsystem | Relationship |
| --- | --- |
| Lovable | External classroom app-builder; Program G1 |
| Curriculum Builder | Separate curriculum metadata/contracts pipeline |
| Local LLM / Ollama | External inference runtime when approved |
| 3D Builder Workshop Agent | Separate sub-agent; Program J |
| Renderers | External output generators per contract type |
| Canvas LLM runtime | Frozen export path; Program C |

Each remains an independent future subsystem gated by `docs/implementation-approval-gate.md`.

---

## Teacher Workstation Health Monitor

**Classification:** Implemented Read-Only Foundation (Program H)

### Purpose

Workstation diagnostics and health reporting. Observes and reports — does not repair, install, or automate.

### Current status

Read-only foundation active. `bin/chief-of-staff --system-health` aggregates repo-local status scripts.

Closure: `docs/teacher-workstation-health-monitor-foundation.md`

### Future phases

| Phase | Scope |
| --- | --- |
| H0 | Read-only report aggregating existing status scripts — **complete** |
| H1 | Live service checks (LLM, widgets, disk) — **planned/blocked** |
| H2+ | Repair/install behavior — **blocked** without separate mission |

### Blocked capabilities

- automation
- monitoring services
- background jobs
- system modifications
- unattended repair

**Detail:** `docs/teacher-workstation-health-monitor.md`, `docs/master-build-roadmap.md` Program H

---

## Teacher Workstation System Updater

**Classification:** Implemented Read-Only Foundation (Program I)

### Purpose

Approval-gated local update planning assistant. Recommends and plans updates; does not apply unless a future approved mission allows it.

### Current status

Read-only planning foundation active. `bin/chief-of-staff --system-update-check` and `--system-update-plan` provide deterministic local-only surfaces.

Closure: `docs/teacher-workstation-system-updater-foundation.md`

### Future phases

| Phase | Scope |
| --- | --- |
| I0 | Read-only update planning foundation — **complete** |
| I1 | Guided update plans requiring approval — **future** |
| I2 | Apply approved updates only — **blocked** |

### Blocked capabilities

- automatic updates
- package installation
- package manager execution
- system modifications
- model downloads
- Mac setting changes
- network calls
- background jobs

**Detail:** `docs/teacher-workstation-system-updater.md`, `docs/master-build-roadmap.md` Program I

---

## AI Tool Routing Matrix

**Classification:** Future / Approval-Gated / Planning Only

### Purpose

Document how Chief of Staff may eventually route requests to specialized tools. Chief of Staff remains orchestration only.

### Tools covered (planning)

| Tool | Role |
| --- | --- |
| Cursor | Repo implementation, testing, PR lifecycle |
| Gemini | Curriculum/pedagogical architecture |
| Lovable | Future classroom app builder |
| Ollama / local LLM | Future private offline execution |
| 3D Builder Workshop Agent | Future classroom object pipeline |
| Future image generation | Future visual asset workflows — not connected |
| ChatGPT / Claude / Codex | Cloud reasoning and coding when manually invoked |

### Current status

Planning only. No routing implementation.

### Blocked capabilities

- automated routing
- API connections
- OAuth and credentials
- network calls from Chief of Staff

**Detail:** `docs/ai-tool-routing-matrix.md`

---

## Local LLM / Ollama Workstation

**Classification:** Future / Approval-Gated / Planning Only

### Purpose

Future local AI execution for privacy-first, offline-capable workflows.

### Future examples

- optional local models
- privacy-first workflows
- offline execution
- model selection guidance
- local/cloud routing policy
- model health checks

### Current status

Planning only. Installer baseline exists (`setup/08-local-ai.sh`); no runtime support active.

### Blocked capabilities

- model downloads
- installs beyond approved missions
- inference implementation
- automated cloud/local routing
- student data processing without explicit policy

**Detail:** `docs/master-build-roadmap.md` Program D

---

## Mac Workstation Experience

**Classification:** Future / Approval-Gated / Planning Only

### Purpose

Future desktop experience improvements for teacher workflow optimization.

### Future examples

- workspace organization concepts
- launch workflow ideas
- menu concepts
- productivity concepts
- teacher modes (Planning, Teaching, Curriculum Builder, Canvas Prep, Grading, Focus, Closeout)
- wallpaper and appearance planning

### Current status

Planning only. Wallpaper foundation stack documented; live curator not started.

### Blocked capabilities

- system modifications
- automation
- configuration changes
- unattended Mac setting changes

**Detail:** `docs/master-build-roadmap.md` Program E

---

## Widget and Shortcut Builder

**Classification:** Future / Approval-Gated / Planning Only

### Purpose

Future teacher productivity widgets and shortcuts surfaced from approved Chief of Staff commands.

### Possible future outputs

- dashboard widgets
- shortcut concepts
- workflow launchers
- mode switchers

### Current status

Planning only. Catalog documented; no installation.

### Blocked capabilities

- installation
- automation
- OS changes
- background scheduling

**Detail:** `docs/master-build-roadmap.md` Program F

---

## Lovable Classroom App Builder Integration

**Classification:** Lovable Classroom App Builder Integration — Future / Approval-Gated

### Purpose

Chief of Staff may eventually route **approved** classroom-app ideas into Lovable for teacher tools, mini-apps, review games, dashboards, and workflow helpers.

### Architecture rule

Chief of Staff must **not** become Lovable. Lovable builds classroom-support apps; CoS decides, validates, routes, tracks, and reports.

### Current status

Planning only. Not connected.

### Blocked capabilities

- Lovable API use
- OAuth and credentials
- network calls
- live app generation
- classroom app deployment
- automation
- student data
- generated student-facing apps
- student-facing deployment
- any live integration

**Detail:** `docs/master-build-roadmap.md` Program G1

---

## 3D Builder Workshop Agent

**Classification:** 3D Builder Workshop Agent — Future / Approval-Gated

### Purpose

Future classroom object creation assistant — separate sub-agent, not Curriculum Builder or Canvas work.

### Example categories

- classroom manipulatives
- bulletin board items
- teacher desk tools
- classroom economy items
- rewards, tokens, badges
- fidgets, desk pets
- organizers, labels, mascots
- display objects

### Chief of Staff workflow (future)

```text
idea intake → safety review → object classification → design prompt
→ builder routing → print readiness checklist → teacher approval
```

### Possible future builders

Tinkercad, Blender, Fusion 360, Bambu Studio, OrcaSlicer, MakerWorld/Printables references (manual), Lovable catalog UI, Cursor local tooling.

### Future Builder Brain (planning only)

- metadata
- preference memory
- scorecards
- print history
- local registry
- reusable object catalog

No custom model training at first.

### Safety boundaries

- no weapons or weapon-like objects
- no sharp objects
- no copyrighted character copies unless manually approved
- no student-identifying objects without approval
- no automatic slicing or printer/hardware integration

### Current status

Planning only. `3d-agent/` readiness parked.

### Blocked capabilities

- web search, downloads, scraping
- CAD/file generation, STL/3MF export
- slicer/printer integration, print jobs
- APIs, OAuth, network calls
- student data, public publishing

**Detail:** `docs/3d-builder-workshop-agent-roadmap.md`

---

## Non-Activation

Documentation/status only. This planning index does not activate integrations, automation, LLM installs, Mac changes, widgets, shortcuts, 3D generation, Lovable connection, APIs, OAuth, network calls, or student-data workflows.
