# Chief of Staff Command Index v1

Last updated: 2026-07-02

```text
Status: documentation/status only
Index status: active_v1
Read-only: yes — commands report PASS/WARN/FAIL; they do not activate runtime work
Manifest: assistant/chief-of-staff/v1/command-surface-manifest.json
CLI index: bin/chief-of-staff --commands
```

## Purpose

Canonical grouped index of Chief of Staff v1 commands. Separates **implemented**, **planned**, and **blocked** surfaces.

Cross-references:

- Agent Core: `docs/chief-of-staff-agent-core.md`
- Operating model: `docs/chief-of-staff-operating-model.md`
- Proof workflow: `docs/chief-of-staff-proof-workflow.md`
- B1 closure: `docs/chief-of-staff-v1-foundation.md`
- Program B closure: `docs/chief-of-staff-v1-program-b-closure.md`
- Daily operations: `docs/chief-of-staff-daily-operations.md`
- Dashboard: `docs/chief-of-staff-dashboard.md`

## Implemented Commands

These flags exist in `bin/chief-of-staff` and work as read-only local status surfaces unless noted.

### Core Status

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --dashboard` | Full local health dashboard |
| `bin/chief-of-staff --status` | Basic CLI status |
| `bin/chief-of-staff --cursor-workflow-status` | Cursor workflow and governance checks |
| `bin/chief-of-staff --cursor-operating-modes-status` | Cursor operating modes, approval gates, and proposal governance |
| `bin/chief-of-staff --autonomous-build-engine-status` | Autonomous Build Engine governance, continuation loop, exhaustion rules |
| `bin/chief-of-staff --governance-lane-status` | Aggregate governance lane status (operating modes + ABE + proposal folders) |
| `bin/chief-of-staff --return-to-core-status` | Parked tracks / return-to-core map |
| `bin/chief-of-staff --commands` | Deterministic command surface index |
| `bin/chief-of-staff --chief-of-staff-v1-status` | Chief of Staff v1 Agent Core foundation status |
| `bin/chief-of-staff --chief-of-staff-command-index-v1-status` | Command index v1 status proof |
| `bin/chief-of-staff --teacher-workstation-foundation-status` | Phase 3 foundation orchestration |

### Proof

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --proof-run` | Pre-merge proof runner |
| `bin/chief-of-staff --validate-all` | Core validation orchestration |

### Planning (Program B)

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --next-action` | Deterministic next recommended program/focus |
| `bin/chief-of-staff --daily-status` | Unified daily operating summary |
| `bin/chief-of-staff --closeout` | End-of-work closeout checklist |

### Safety / Queues

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --memory-status` | Project memory status |
| `bin/chief-of-staff --validate-memory` | Project memory validation |
| `bin/chief-of-staff --approval-queue` | Approval queue categories |
| `bin/chief-of-staff --blocker-queue` | Blocker queue surfacing |
| `bin/chief-of-staff --mode-status` | Operating context mode concepts |

### System Updater (Program I)

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --system-update-check` | System Updater read-only foundation check |
| `bin/chief-of-staff --system-update-plan` | Manual update planning checklist |

### Workstation Operations (Aggregate)

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --workstation-ops-lane-status` | Aggregate workstation ops lane status (Health H + Updater I) |

### Health Monitor (Program H)

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --system-health` | Teacher Workstation Health Monitor report |
| `bin/chief-of-staff --workstation-health` | Alias for `--system-health` |

### Program Status — Curriculum & Foundations

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --curriculum-builder-foundation-status` | Curriculum Builder v1 |
| `bin/chief-of-staff --curriculum-contracts-status` | Metadata contract schemas A4–A7 (read-only) |
| `bin/chief-of-staff --curriculum-registry-dry-run-status` | Registry v0.2 manual entry dry-run (CB-IMPL-1; no writes) |
| `bin/chief-of-staff --curriculum-registry-records-status` | Registry v0.2 local fake records (CB-IMPL-2; fixture only) |
| `bin/chief-of-staff --curriculum-registry-renderer-status` | Registry v0.2 fake-record renderer preview (CB-IMPL-3) |
| `bin/chief-of-staff --curriculum-registry-retrieval-status` | Registry v0.2 fake-record retrieval hooks (CB-IMPL-4) |
| `bin/chief-of-staff --curriculum-registry-lane-status` | Registry lane aggregate status (CB-IMPL-1–4 + planning + hardening) |
| `bin/chief-of-staff --curriculum-registry-a4-a7-fixture-schema-status` | A4–A7 canonical schema cross-validation for v0.2 fake fixtures |
| `bin/chief-of-staff --curriculum-production-registry-planning-status` | Production registry workflow planning status (CB-PROD-PLAN; planning-only; no writes) |
| `bin/chief-of-staff --curriculum-production-registry-owen-checklist-status` | Owen § J production registry approval checklist tracker (planning-only; Owen decisions required) |
| `bin/chief-of-staff --curriculum-source-readiness-status` | Curriculum Source Readiness fake metadata inventory foundation (no real ingestion) |
| `bin/chief-of-staff --curriculum-library-foundation-status` | Curriculum Library v1 |
| `bin/chief-of-staff --lesson-planning-foundation-status` | Lesson Planning v1 |
| `bin/chief-of-staff --renderer-foundation-status` | Renderer Foundation v1 |
| `bin/chief-of-staff --local-retrieval-foundation-status` | Local Retrieval v0 |
| `bin/chief-of-staff --integration-planning-foundation-status` | Integration Planning v0 |
| `bin/chief-of-staff --teacher-app-designer-canvas-llm-status` | Canvas LLM frozen foundation |

### AI Tool Routing (Operational Surface)

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --model-routing-status` | AI tool routing matrix operational status (read-only) |

### Local LLM / Ollama Workstation (Program D1)

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --local-llm-workstation-status` | Local LLM/Ollama read-only status foundation |

### Mac Workstation Experience (Program E1)

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --mac-workstation-status` | Mac workstation experience read-only planning foundation |

### Widget and Shortcut Builder (Program F1)

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --widget-shortcut-status` | Widget and shortcut catalog read-only foundation |

### Classroom App Lab (Prototype Rescue Foundation)

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --classroom-app-lab-status` | Classroom App Lab prototype rescue read-only foundation |

### Lovable Classroom App Builder (Program G1)

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --lovable-status` | Lovable integration read-only planning surface |

### 3D Builder Workshop Agent (Program J1)

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --3d-builder-status` | 3D Builder Workshop Agent read-only planning surface |

## Planned Commands

Documented for future programs. **Not implemented** unless added to CLI.

| Command | Program | Purpose |
| --- | --- | --- |
| `bin/chief-of-staff --daily-briefing` | B2+ | Daily briefing surface (AI approval-gated) |
| `bin/chief-of-staff --prove-main` | Proof | Local main cleanliness proof |
| `bin/chief-of-staff --local-llm-health` | D3 | Live Ollama health (blocked) |
| `bin/chief-of-staff --widget-health` | F2 | Live widget catalog health (blocked) |
| `bin/chief-of-staff --shortcut-health` | F3 | Live shortcut catalog health (blocked) |

## Blocked Commands

Intentionally not available until explicit approval supersedes stop markers or gates.

| Command | Reason |
| --- | --- |
| Canvas restart / live export | Canvas LLM stop marker active |
| Lovable API / app generation | Program G1 — planning only |
| Drive/Gmail/Canvas API surfaces | Program G — integrations blocked |
| Ollama install / model download | Program D — approval-gated |
| `--apply-approved-updates` | System Updater apply blocked without approval mission |

## Proof Scripts

| Script | Purpose |
| --- | --- |
| `bash scripts/run-workstation-proof.sh` | Full local proof runner |
| `bash scripts/chief-of-staff-validate-all.sh` | Core validation orchestration |
| `bash tests/smoke-chief-of-staff-cli.sh` | CLI smoke tests |
| `bash tests/chief-of-staff-v1-operating-test.sh` | Operating command tests |
| `bash tests/chief-of-staff-daily-operations-test.sh` | Program B daily operations tests |
| `bash tests/teacher-workstation-health-monitor-test.sh` | Health Monitor tests |

## Boundaries

Chief of Staff v1 commands:

- orchestrate read-only status and validation
- recommend next approved work deterministically
- do not generate lessons, curriculum, or review notes
- do not call external APIs, OAuth, or network services
- do not scan folders, index documents, or run LLM inference for planning

## no lesson generation

Chief of Staff coordinates work; it does not generate lesson content.
