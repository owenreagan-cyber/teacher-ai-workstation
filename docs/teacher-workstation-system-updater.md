# Teacher Workstation System Updater

Last updated: 2026-07-02

```text
Status: documentation/status only
Program: Teacher Workstation System Updater — Program I
Classification: read-only update planning — not automatic updater
Network calls: no
Package managers: no
Automation: no
```

## Purpose

The **System Updater** checks, summarizes, and plans safe workstation updates. It is **not** an automatic updater.

In Program I v0, the System Updater produces read-only planning surfaces and checklists only.

## Scope — What Can Be Planned Now

| Area | Planning surface | Status |
| --- | --- | --- |
| Repo update readiness | local main cleanliness concept | planning only |
| Dashboard/validation readiness | status script inventory | planning only |
| Chief of Staff command surface | manifest coherence | planning only |
| Health Monitor relationship | separation boundary | doc checks |
| Tool inventory | planning categories only | future |
| Local LLM/model inventory | planning categories only | blocked |
| Wallpaper/widget/shortcut assets | planning categories only | future |
| Dependency checklist | manual template only | planning only |

## Architecture Rule

System Updater **recommends and plans only** unless a future approved mission explicitly allows applying changes.

In this foundation, it does **not**:

- install, update, repair, or mutate
- automate or schedule background jobs
- run APIs, OAuth, or network calls
- perform network checks or call package managers
- modify git state or create branches
- change Mac settings, widgets, or shortcuts
- download LLMs or run local inference
- inspect Drive/NAS/iCloud, student data, or curriculum files
- push to Canvas or call Lovable

## Boundary with Health Monitor

| System | Role |
| --- | --- |
| **Health Monitor (H)** | Observes and reports current PASS/WARN/FAIL health |
| **System Updater (I)** | Checks and plans possible updates (read-only in v0) |

Health Monitor must not become System Updater. System Updater must not become Health Monitor.

## System Updater Stages

### v0 — Read-Only Update Planning Foundation (this mission)

Allowed:

- architecture documentation
- update checklist categories
- repo-local readiness from docs/scripts
- manual update plan template
- `--system-update-check` and `--system-update-plan`

Blocked:

- applying updates, package installs, model downloads
- Mac/widget/shortcut changes, network checks, background jobs

### v1 — Guided Update Planning (future approval-gated)

May eventually recommend steps and produce manual plans requiring Owen approval.

Still blocked: automatic application, package manager execution, external service checks.

### v2 — Approved Maintenance Execution (future approval-gated)

May apply explicitly approved updates only. Not part of this mission.

## Update Planning Domains

1. **Repo Update Planning** — branch/main cleanliness concepts; no git mutation
2. **Dashboard/Validation Update Planning** — which proof commands to run before/after updates
3. **Chief of Staff Command Surface Update Planning** — manifest and CLI coherence
4. **Status Script Inventory Planning** — foundation status scripts catalog
5. **Documentation Coherence Update Planning** — roadmap/capability/build-queue alignment
6. **Dependency/Tool Inventory Planning** — checklist only; no package manager
7. **Local LLM/Ollama Inventory Planning** — blocked until Program D approval
8. **Mac Experience Asset Planning** — wallpaper/widget planning only
9. **Widget/Shortcut Asset Planning** — catalog presence planning only
10. **Future Integration Update Planning** — Drive/Canvas/OAuth last-stage
11. **Non-Activation Boundary Planning** — gates, stop markers, constitution

## CLI Surfaces

```bash
bin/chief-of-staff --system-update-check
bin/chief-of-staff --system-update-plan
bash scripts/teacher-workstation-system-updater-status.sh
```

## Non-Activation

Documentation and read-only planning only. No apply, install, network, or automation.
