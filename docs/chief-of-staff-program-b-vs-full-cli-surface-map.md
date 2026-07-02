# Chief of Staff — Program B vs Full CLI Surface Map

Last updated: 2026-07-02

```text
Status: documentation/status only
Purpose: explain Program B scope vs expanded CLI surface
Command changes: none — no removal or rename
PASS/WARN/FAIL semantics: unchanged
```

## Purpose

Clarify what **Program B (Chief of Staff v1 Agent Core B1–B6)** originally delivered versus the **full Chief of Staff CLI surface** today, including program status commands added after Program B closure.

This is a planning/discovery doc only. It does not authorize new commands or runtime behavior.

## Original Program B Scope (B1–B6)

Closure: `docs/chief-of-staff-v1-program-b-closure.md`

| Sub-program | Focus | Key commands |
| --- | --- | --- |
| B1 | Command surface, operating model | `--commands`, `--chief-of-staff-v1-status`, `--next-action` |
| B2 | Daily operations | `--daily-status` |
| B3 | Closeout | `--closeout` |
| B4 | Approval/blocker queues | `--approval-queue`, `--blocker-queue` |
| B5 | Mode concepts | `--mode-status` |
| B6 | Program coherence | closure doc |

Program B is **orchestration and read-only repo-local operations** — not curriculum intake, not integrations, not Mac mutations.

## What Expanded After Program B

The CLI surface grew with **program foundation status commands** and **aggregate lane proofs**:

| Category | Examples | Program |
| --- | --- | --- |
| Health / Updater | `--system-health`, `--system-update-check`, `--workstation-ops-lane-status` | H, I |
| Governance | `--cursor-operating-modes-status`, `--autonomous-build-engine-status`, `--governance-lane-status` | Governance |
| Curriculum Builder | `--curriculum-registry-*`, `--curriculum-production-registry-planning-status`, `--curriculum-production-registry-governance-status`, `--curriculum-production-registry-owen-checklist-status`, `--curriculum-source-readiness-status` | A / CB-IMPL |
| Future program lanes | `--local-llm-workstation-status`, `--lovable-status`, `--3d-builder-status`, … | D1, G1, J1, … |
| Canvas (frozen) | `--teacher-app-designer-canvas-llm-status` | C |

Full index: `docs/chief-of-staff-command-index-v1.md`

Manifest: `assistant/chief-of-staff/v1/command-surface-manifest.json`

## Aggregate Commands (Post–Program B)

Read-only wrappers that run component status scripts without hiding failures:

| Command | Aggregates |
| --- | --- |
| `--curriculum-registry-lane-status` | CB-IMPL-1–4 + planning + A4–A7 cross-validation |
| `--governance-lane-status` | Operating modes + ABE + proposal folders |
| `--workstation-ops-lane-status` | Health Monitor H + System Updater I |
| `--dashboard` | Broad orchestration across tracks |

## Gaps and Future Safe Improvements

| Gap | Classification | Notes |
| --- | --- | --- |
| No single `--chief-of-staff-lane-status` for all programs | proposal candidate | Large aggregate; auditability risk |
| Program B commands vs 40+ status flags | documentation | This map |
| `--capability-map-status` / `--roadmap-status` | planned in manifest | Not yet implemented |
| Owen § J production registry checklist tracker | proposed | Owen decision |
| Daily briefing AI (`--daily-briefing`) | blocked | Generation — approval-gated |

## What Program B Did Not Promise

- Curriculum registry production writes
- Real metadata or content intake
- Health repair or system apply
- APIs, OAuth, network, Ollama execution
- Widget/shortcut install, Mac system changes

## Non-Activation

This map does not remove, rename, or weaken any command or status check.

## Proof

```bash
bin/chief-of-staff --chief-of-staff-v1-status
bin/chief-of-staff --commands
bin/chief-of-staff --governance-lane-status
```
