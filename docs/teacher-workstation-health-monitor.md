# Teacher Workstation Health Monitor

Last updated: 2026-07-02

```text
Status: documentation/status only
Program: Teacher Workstation Health Monitor — Program H
Classification: observe and report only — not System Updater
Network calls: no
Automation: no
```

## Purpose

The **Health Monitor** observes and reports whether the Teacher AI Workstation appears healthy using deterministic, repo-local status surfaces.

Health Monitor **observes and reports**. It does not update, install, repair, automate, or modify the system.

## Scope — What Can Be Checked Now

| Area | Source | Status |
| --- | --- | --- |
| Repository health | `bin/chief-of-staff`, git repo-local state | active |
| Dashboard health | `bin/chief-of-staff --dashboard` | referenced |
| Validation suite | `scripts/cursor-workflow-status.sh`, foundation status scripts | aggregated |
| Chief of Staff | `scripts/chief-of-staff-v1-foundation-status.sh` | aggregated |
| Program B coherence | Chief of Staff v1 docs and commands | aggregated |
| Roadmap/capability coherence | docs cross-links | doc checks |
| Phase 3 foundations | `scripts/teacher-workstation-foundation-status.sh` | aggregated |
| Curriculum Builder foundation | existing foundation status script | aggregated |
| Canvas frozen status | stop marker docs + canvas status script | doc + status |
| Integration/Lovable/LLM/Mac/widgets/3D | planning-only docs | boundary checks only |

## Architecture Rule

Health Monitor observes and reports.

It does **not**:

- update, install, or repair
- mutate repository or system state
- automate or schedule background jobs
- run APIs, OAuth, or network calls
- scan user folders or external drives
- inspect curriculum files or student data
- modify Mac settings, widgets, or shortcuts
- download LLMs or run local inference
- generate 3D files, slice, or print
- push to Canvas or call Lovable

## Boundary with System Updater

| System | Role |
| --- | --- |
| **Health Monitor (H)** | Observes and reports PASS/WARN/FAIL health |
| **System Updater (I)** | Future: recommends/applies **approved** updates only |

Health Monitor must not become System Updater. No `--system-update-check` or apply behavior in this program.

## Health Domains

### 1. Repo Health

- Chief of Staff CLI present
- Core scripts and docs present
- Optional WARN if working tree dirty (informational)

### 2. Dashboard Health

- Referenced via dashboard command; full dashboard run is separate proof

### 3. Chief of Staff Health

- v1 Agent Core foundation status
- Command surface manifest coherence

### 4. Roadmap and Capability Health

- Health Monitor linked from master roadmap and capability map
- Build queue and active priorities aligned

### 5. Foundation Program Health

- Lesson Planning, Curriculum Library, Renderer, Local Retrieval, Integration Planning foundations
- Curriculum Builder foundation status when script available

### 6. Future Program Boundary Health

- Canvas stop marker active (docs)
- Lovable, Local LLM, Mac modes, widgets, 3D remain planning-only

### 7. Validation Suite Health

- Cursor workflow status
- Chief of Staff commands surface

### 8. Non-Activation Health

- Docs preserve no network/API/OAuth/automation boundaries
- No student data or real curriculum content handling

### 9. Local-First Architecture Health

- Status scripts use PASS/WARN/FAIL semantics
- Read-only orchestration only

## CLI Surfaces

```bash
bin/chief-of-staff --system-health
bin/chief-of-staff --workstation-health   # alias
bash scripts/teacher-workstation-health-status.sh
```

## Proof

```bash
bash scripts/teacher-workstation-health-status.sh
bash tests/teacher-workstation-health-monitor-test.sh
bin/chief-of-staff --dashboard
```

## Non-Activation

Documentation and read-only status only. No repair, update, install, APIs, network, automation, or student data.
