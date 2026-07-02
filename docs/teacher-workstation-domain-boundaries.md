# Teacher Workstation Domain Boundaries

Last updated: 2026-07-02

```text
Status: documentation/status only
Program: Cursor Operating Modes and Proposal Governance Foundation
Classification: domain boundary reference — no runtime activation
```

## Purpose

Define project-specific boundaries for each major Teacher Workstation domain. Use with `docs/cursor-operating-modes-and-approval-gates.md` and `docs/implementation-approval-gate.md`.

## Boundary Categories

| Category | Meaning |
| --- | --- |
| Safe foundation work | Docs, status scripts, read-only checks, fictional placeholders, cross-links |
| Proposal-only work | Ideas recorded in `docs/proposals/index.md`; no implementation |
| Implementation-gated work | Requires `approved_for_implementation` and track intake |
| Runtime/live-integration-gated work | Requires `approved_for_runtime` or `approved_for_live_integration` |
| Blocked unless explicitly approved | Default deny; mission must name scope explicitly |

---

## Parent Communication Agents

| Work type | Category |
| --- | --- |
| Template catalogs, response-pattern docs, approval-gated planning | Safe foundation work |
| New parent-communication features or workflows | Proposal-only work |
| Draft-generation helpers, roster-linked logic | Implementation-gated work |
| Live parent workflows, message sending | Runtime/live-integration-gated work |

**Blocked unless explicitly approved:**

- Automatic sending of messages
- Gmail access
- Roster lookup, attendance lookup, grade lookup
- Behavior-data lookup, accommodation lookup, health-data processing
- Student-specific message generation
- Live parent workflows

---

## Curriculum / Lesson / Worksheet / Presentation Generation

| Work type | Category |
| --- | --- |
| Registry v0, contract schemas, binding v0, validators (read-only) | Safe foundation work |
| New generation features, renderer activation | Proposal-only work |
| Bounded validators, registry extensions under intake | Implementation-gated work |
| Real lesson/worksheet/presentation/quiz generation | Runtime-gated work |

**Blocked unless explicitly approved:**

- Real lesson generation
- Generated worksheets, presentations, quizzes, or tests
- Extraction from copyrighted curriculum
- File scanning, OCR, embeddings, RAG
- Canvas export/upload and automatic deployment

---

## Canvas / Drive / Gmail / Calendar / External Integrations

| Work type | Category |
| --- | --- |
| Integration planning docs, staged models, frozen Canvas LLM foundation | Safe foundation work |
| New integration proposals | Proposal-only work |
| Placeholder schemas, manual export checklists (docs only) | Implementation-gated work (docs/status) |
| API clients, OAuth, live sync, automatic exports | Runtime/live-integration-gated work |

**Blocked unless explicitly approved:**

- OAuth, API clients, credential handling, token storage
- Network requests, live sync, live reads/writes
- Automatic exports/imports, automatic message sending
- Automatic Canvas updates, Drive crawling

See also: `docs/canvas-llm-stop-marker-curriculum-builder-return.md` — Canvas LLM runtime remains frozen.

---

## UI / UX / App Experience Improvement

| Work type | Category |
| --- | --- |
| UX planning docs, navigation patterns, dashboard readability | Safe foundation work |
| New UI features or interaction patterns | Proposal-only work |
| Bounded UI implementation in approved app scope | Implementation-gated work |
| Live app behavior, student-facing surfaces | Runtime-gated work |

**Blocked unless explicitly approved:** deploying student-facing tools, live app execution, or unreviewed UX that implies sending/sharing data.

---

## Classroom App Lab / Prototype Rescue

| Work type | Category |
| --- | --- |
| Read-only foundation (`--classroom-app-lab-status`) | Safe foundation work |
| Rescue workflow proposals | Proposal-only work |
| Bounded repo-local scaffolding under intake | Implementation-gated work |
| Zip extraction, code parsing, app execution, auto-rescue | Runtime-gated work |

**Blocked unless explicitly approved:** zip extraction, codebase parsing, app execution, LLM/API analysis of uploaded prototypes.

---

## Mac Workstation Experience

| Work type | Category |
| --- | --- |
| Read-only planning (`--mac-workstation-status`) | Safe foundation work |
| Mode/wallpaper/menu improvements | Proposal-only work |
| Bounded Mac-adjacent docs under intake | Implementation-gated work |
| Wallpaper apply, system prefs, LaunchAgents | Runtime/live-integration-gated work |

**Blocked unless explicitly approved:** Mac system setting changes, `defaults write`, wallpaper apply, automation.

---

## Widgets and Shortcuts

| Work type | Category |
| --- | --- |
| Read-only catalog (`--widget-shortcut-status`) | Safe foundation work |
| Widget/shortcut ideas | Proposal-only work |
| Catalog metadata extensions | Implementation-gated work |
| Install, sync, execute shortcuts/widgets | Runtime-gated work |

**Blocked unless explicitly approved:** widget installation, shortcut installation, shortcut execution, AppleScript, Mac automation.

See: `docs/widget-shortcut-builder-non-activation-boundaries.md`

---

## VIBE Mode

| Work type | Category |
| --- | --- |
| Appearance & Vibe foundation docs, wallpaper/photo planning status | Safe foundation work |
| VIBE enhancements | Proposal-only work |
| Bounded planning polish | Implementation-gated work |
| Live curator, wallpaper rotation, notifications | Runtime-gated work |

**Blocked unless explicitly approved:** live wallpaper curator, schedulers, network fetches, Mac mutation.

---

## 3D Design Studio

| Work type | Category |
| --- | --- |
| Read-only planning (`--3d-builder-status`) | Safe foundation work |
| CAD/workshop agent ideas | Proposal-only work |
| Bounded planning extensions | Implementation-gated work |
| CAD generation, STL export, slicing, printing | Runtime-gated work |

**Blocked unless explicitly approved:** CAD generation, STL/3MF export, slicer integration, printer integration.

See: `docs/3d-builder-workshop-agent-non-activation-boundaries.md`

---

## Lovable / App Builder Workflows

| Work type | Category |
| --- | --- |
| Read-only planning (`--lovable-status`) | Safe foundation work |
| Classroom app builder routing ideas | Proposal-only work |
| Bounded docs under intake | Implementation-gated work |
| Lovable API, app generation, deployment | Runtime/live-integration-gated work |

**Blocked unless explicitly approved:** Lovable API connection, OAuth, network calls, live app generation or deployment.

---

## Local LLM / Ollama Workflows

| Work type | Category |
| --- | --- |
| Read-only status (`--local-llm-workstation-status`), routing matrix visibility | Safe foundation work |
| Local inference proposals | Proposal-only work |
| Capability-broker planning (D2) | Implementation-gated work |
| Ollama install, model downloads, inference | Runtime-gated work |

**Blocked unless explicitly approved:** Ollama execution, model downloads, local inference, network probes, package managers.

See: `docs/local-llm-non-activation-boundaries.md`

---

## Cross-Domain Rules

1. **Chief of Staff** orchestrates status and proof — it does not activate blocked domains by default.
2. **Health Monitor** and **System Updater** report repo-local foundation health — no repair, install, or apply without approval.
3. **AI Tool Routing** provides lane visibility — no automated routing to cloud or local models without approval.
4. Mixed-category files follow the more restrictive domain rule.

## Non-Activation

This document is boundary reference text only. It does not activate any domain runtime behavior.
