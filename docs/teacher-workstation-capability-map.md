# Teacher Workstation Capability Map

Last updated: 2026-07-02

```text
Status: documentation/status only
Authority: companion to docs/master-build-roadmap.md
Implementation approval status: not approved by default
```

## Purpose

This document is the **canonical capability map** for Teacher AI Workstation. It lists all major systems and future capabilities in one place with consistent status labels.

Cross-references:

- Master program sequence: `docs/master-build-roadmap.md` §4
- AI tool roles: `docs/ai-tool-routing-matrix.md`, `assistant/model-routing.md`
- Long-term future programs: `docs/long-term-future-programs-roadmap.md`

## Status Labels

| Label | Meaning |
| --- | --- |
| **planned** | Documented future capability; no foundation artifacts |
| **foundation complete** | Docs, interfaces, validators, or status proof exist; no runtime |
| **implemented read-only** | Operational read-only checks or local-first proof surfaces |
| **write-capable** | Approved writes under explicit human/approval gates |
| **active integration** | Live external connection approved and bounded |
| **automated** | Background or unattended behavior approved and bounded |
| **production** | Teacher-reviewed daily-use capability with proof on `main` |

## Central Control Plane

| Capability | Status | Notes |
| --- | --- | --- |
| Chief of Staff CLI | implemented read-only | `bin/chief-of-staff`; status/orchestration |
| Chief of Staff dashboard | implemented read-only | PASS/WARN/FAIL health surface |
| Project memory / intake | implemented read-only | Local memory; human-reviewed |
| Proof runner | implemented read-only | `scripts/run-workstation-proof.sh` |
| Command surface index (`--commands`) | **foundation complete** | Program B |
| Chief of Staff v1 Agent Core | **foundation complete** | Program B — see `docs/chief-of-staff-v1-program-b-closure.md` |
| Next-action recommendation | implemented read-only | `--next-action` |
| Daily status / closeout | **implemented read-only** | `--daily-status`, `--closeout` (Program B2/B3) |
| Approval / blocker queues | **implemented read-only** | `--approval-queue`, `--blocker-queue` (Program B4) |
| Mode awareness (conceptual) | **implemented read-only** | `--mode-status` (Program B5); no Mac changes |
| Cursor operating modes governance | **implemented read-only** | `--cursor-operating-modes-status`; approval gates + proposal ledger |
| Autonomous Build Engine governance | **implemented read-only** | `--autonomous-build-engine-status`; continuation loop + exhaustion rules |
| Governance lane aggregate status | **implemented read-only** | `--governance-lane-status`; operating modes + ABE + proposal folders |
| Daily briefing (AI) | planned | Approval-gated |
| Tool routing surface | implemented read-only | `--model-routing-status`; matrix at `docs/ai-tool-routing-matrix.md` |
| Health summary | planned | Aggregated report via Program H |

**Architecture rule:** Chief of Staff is the central agent/control plane. It coordinates, validates, routes, tracks, and reports. It does not become external builders (Lovable, renderers, 3D tools, Canvas runtime).

## Curriculum and Content Foundations

| Capability | Status | Notes |
| --- | --- | --- |
| Engineering Constitution / Approval Gate | foundation complete | Active governance |
| Curriculum Builder v1 | foundation complete | Registry, 5 output contracts, binding, validation |
| Curriculum Builder metadata contracts A4–A7 | implemented read-only | `--curriculum-contracts-status`; inactive planning schemas |
| Curriculum Builder Registry v0.2 dry-run (CB-IMPL-1) | implemented read-only | `--curriculum-registry-dry-run-status`; fake candidates only; no writes |
| Curriculum Builder Registry v0.2 local records (CB-IMPL-2) | implemented read-only | `--curriculum-registry-records-status`; fake fixture registry only |
| Curriculum Builder Registry v0.2 renderer preview (CB-IMPL-3) | implemented read-only | `--curriculum-registry-renderer-status`; metadata preview only |
| Curriculum Builder Registry v0.2 retrieval hooks (CB-IMPL-4) | implemented read-only | `--curriculum-registry-retrieval-status`; fake lookup only |
| Curriculum Builder production registry planning (CB-PROD-PLAN) | implemented read-only | `--curriculum-production-registry-planning-status`; planning brief only; no writes |
| Owen § J production registry checklist tracker | implemented read-only | `--curriculum-production-registry-owen-checklist-status`; Owen decisions required; review packet |
| Owen § J decision worksheet + post-decision map | implemented read-only | `docs/curriculum-builder-production-registry-owen-decision-worksheet.md`; routing table; no implied approval |
| Metadata pilot planning boundary (no intake) | implemented read-only | `docs/curriculum-builder-metadata-pilot-planning-boundary.md`; fake examples only |
| Manual metadata boundary | implemented read-only | `docs/curriculum-builder-manual-metadata-boundary.md`; field taxonomy; no real records |
| Governance-first production registry (CB-PROD-GOV) | implemented read-only | `--curriculum-production-registry-governance-status`; blocked-write proof; candidate skeleton |
| Curriculum Builder Registry authority map + lane hardening | implemented read-only | `--curriculum-registry-lane-status` (includes source readiness + Owen checklist); `--curriculum-registry-a4-a7-fixture-schema-status`; see authority map |
| Curriculum Source Readiness (fake metadata inventory) | implemented read-only | `--curriculum-source-readiness-status`; fake fixtures only; no real ingestion |
| Production registry writes / real records | planned | Approval-gated — Owen checklist required; `--curriculum-registry-write` blocked |
| Lesson Planning Foundation | foundation complete | Phase 3 Workstream A |
| Curriculum Library Foundation | foundation complete | Phase 3 Workstream B |
| Renderer Foundation v1 | foundation complete | Interface/status only; no renderers |
| Local Retrieval Foundation v0 | foundation complete | Planning/interfaces; no engines |
| Integration Planning Foundation v0 | foundation complete | Drive/Canvas/OAuth planning; inactive |
| Real registry records | planned | Approval-gated |
| Teacher-reviewed renderers | planned | Per-contract intake |
| Lesson generation | planned | Human-reviewed only when approved |
| Local retrieval engines | planned | Non-RAG first |

## AI and Model Surfaces

| Capability | Status | Notes |
| --- | --- | --- |
| AI Tool Routing Matrix | foundation complete | `docs/ai-tool-routing-foundation.md` |
| Model routing policy | foundation complete | `assistant/model-routing.md` |
| Local LLM / Ollama workstation | implemented read-only | `--local-llm-workstation-status`; Program D1 foundation |
| Cloud API routing (OpenAI/Anthropic/Google) | planned | Blocked until explicit approval |
| Automated model selection | planned | Chief of Staff routing concept only |

## Workstation Operations

| Capability | Status | Notes |
| --- | --- | --- |
| Teacher Workstation Health Monitor | **implemented read-only** | Program H — `--system-health` |
| Teacher Workstation System Updater | **implemented read-only** | Program I — `--system-update-check` |
| Workstation ops lane aggregate status | **implemented read-only** | `--workstation-ops-lane-status`; Health H + Updater I |
| Widget catalog | implemented read-only | `--widget-shortcut-status`; Program F1 foundation |
| Shortcut catalog | implemented read-only | `--widget-shortcut-status`; Program F1 foundation |
| Classroom App Lab / Prototype Rescue | implemented read-only | `--classroom-app-lab-status`; CAL1 foundation |
| Mac teacher modes | implemented read-only | `--mac-workstation-status`; Program E1 foundation |
| Wallpaper / appearance | foundation complete | Planning stack; live curator not started |

## External Builders and Integrations

| Capability | Status | Notes |
| --- | --- | --- |
| Lovable classroom app builder | implemented read-only | `--lovable-status`; Program G1 foundation |
| Canvas LLM manual export | foundation complete | Frozen/stopped; Program C |
| Google Drive / Gmail / Canvas API | planned | Last-stage integrations; Program G |
| OAuth / secrets broker | planned | Phase 0F; blocked |
| Integration staging (G0–G5) | foundation complete | Documentation/dry-run only; see Program G |

## Integrations and Automation (Staged)

| Stage | Status | Notes |
| --- | --- | --- |
| G0 Documentation only | foundation complete | Roadmaps, inactive manifests |
| G1 Manual links | planned | Browser profiles; paste-only |
| G2 Local dry-run | foundation complete | Integration planning foundation v0 |
| G3 Read-only integration | planned | Blocked |
| G4 Write integration | planned | Blocked |
| G5 Automation | planned | Blocked |

## 3D Builder Workshop Agent

| Capability | Status | Notes |
| --- | --- | --- |
| 3D Builder Workshop Agent | implemented read-only | `--3d-builder-status`; Program J1 foundation |
| 3d-agent readiness stack | foundation complete | `3d-agent/` policies/workflows; parked |
| Builder Brain / asset library | planned | Rules and scorecards first; no training |
| CAD generation / slicing / printing | planned | Blocked until explicit missions |

Legacy name **3D Design Factory Agent** remains in parked-track status strings; the master plan program name is **3D Builder Workshop Agent**. See `docs/3d-builder-workshop-agent-roadmap.md`.

## Non-Activation

This capability map is Markdown planning text only. It does not activate integrations, Mac changes, LLM installs, APIs, widgets, shortcuts, 3D generation, slicing, printing, automation, or student-data workflows.
