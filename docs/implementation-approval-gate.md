# Implementation Approval Gate and Track Intake Foundation

```text
Gate status: active
Documentation status: documentation/status only
Implementation approval status: not approved
Track intake status: planning templates only
Runtime activation status: not active
```

## Purpose

This document defines the **repo-wide implementation approval gate** for Teacher AI Workstation. It separates planning/status work from implementation work and requires explicit approval before any track may activate schemas, validators, renderers, registries, APIs, ingestion, RAG, generation, or automation. documentation/status only — no runtime behavior.

## Gate Status

- `Gate status: active`
- `Documentation status: documentation/status only`
- `Implementation approval status: not approved`
- `Track intake status: planning templates only`
- `Runtime activation status: not active`

No implementation is approved by default. Planning foundation completion does not imply implementation approval.

## What Counts as Planning/Status Work

Planning/status work is allowed when bounded and documentation-only:

- planning docs, audit docs, closeout docs, and maintainer handoffs
- cross-links, index updates, and build-queue/active-priorities alignment
- static PASS/WARN/FAIL status checks (file presence and fixed-string grep only)
- fictional/static sample artifacts explicitly marked planning-only
- decision intake **templates** that remain blank
- section completion audits and non-activation boundary notes

Planning/status work must not activate runtime behavior.

## What Counts as Implementation Work

Implementation work includes any change that creates or activates:

- schema files, database tables, or migrations
- live registry records or registry data files
- validators, parsers, importers, crawlers, or renderers
- new commands that read/write curriculum files or external systems
- Drive/NAS/iCloud/Canvas path resolution or connectors
- APIs, OAuth, network calls, or secrets handling
- document scanning, folder scanning, folder crawling, or file indexing
- OCR, embeddings, vector database, or RAG pipelines
- lesson generation, generated lesson drafts, or generated review notes
- automation, schedulers, or background jobs
- dashboard semantics changes that weaken or replace existing checks without approval

If unsure, treat the work as implementation and stop for explicit approval.

## What Requires Explicit Approval

Explicit human approval from Owen is required before:

- crossing this repo-wide gate
- crossing any track-specific gate (for example `docs/curriculum-builder-approval-gate.md`)
- unfreezing Canvas LLM runtime work (`docs/canvas-llm-planning-foundation-freeze.md`, stop marker)
- activating any checklist section in **Implementation Track Intake Checklists** below

Documentation/status PRs do not require crossing the gate unless they accidentally include implementation behavior.

## Required Intake Fields

Any implementation intake must include:

| Field | Required content |
| --- | --- |
| Track name | Curriculum Builder, Canvas LLM, lesson planning, Appearance & Vibe, etc. |
| Decision title | Short name for the proposed implementation PR |
| Requested path | What implementation category is requested |
| Approval level | Documentation-only vs bounded runtime vs full runtime |
| Proposed PR scope | Files/commands expected to change |
| Explicitly allowed work | Bullet list of approved behaviors |
| Explicitly blocked work | Bullet list of remain-forbidden behaviors |
| Risk review | Storage, registry, Teacher Workstation, Chief of Staff, dashboard/status, student-data, network/API impact |
| Validation proof plan | Commands that must pass before merge |
| Rollback/stop plan | How to revert and stop if behavior activates incorrectly |
| Non-activation confirmation | Statement of what will NOT be activated in this PR |
| Final approval | Explicit Owen approval checkbox / sign-off |

Curriculum Builder implementations must also complete `docs/curriculum-builder-decision-intake-template.md`.

## Required Risk Review

Before approval, review:

- **Student data:** confirm no real student names, records, or classroom-sensitive content
- **Network/API:** confirm no unauthorized APIs, OAuth, secrets, or network calls
- **Scanning/indexing:** confirm no folder scanning, crawling, indexing, OCR, or embeddings unless explicitly approved
- **Generation:** confirm no lesson generation or generated review notes unless explicitly approved
- **Semantics:** confirm PASS/WARN/FAIL and dashboard health semantics are preserved unless explicitly approved
- **Scope creep:** confirm the PR does not activate adjacent blocked tracks (RAG while requesting registry only, etc.)

## Required Validation Proof

Minimum validation before merge of any implementation PR:

```bash
bash -n bin/chief-of-staff
bash scripts/phase-1-status.sh
bin/chief-of-staff --dashboard
bash tests/smoke-chief-of-staff-cli.sh
```

Add track-specific status scripts when the implementation touches that track:

```bash
bash scripts/curriculum-builder-foundation-status.sh
bash scripts/teacher-app-designer-canvas-llm-status.sh
bash scripts/cursor-workflow-status.sh
```

Final proof on clean local `main` after merge is required.

## Required Rollback/Stop Plan

Every implementation intake must document:

- files and commands to revert
- data artifacts to remove or disable
- how to restore prior PASS/WARN/FAIL counts
- stop conditions that trigger immediate rollback (unexpected FAIL, runtime activation, network call, student data touch)
- who approves restart after rollback (Owen only)

## Implementation Track Intake Checklists

Planning templates only. Checking a box here does **not** approve implementation.

### Curriculum Builder live registry

- [ ] Completed track intake with explicit allowed/blocked work
- [ ] Repo-wide gate crossed with Owen approval
- [ ] `docs/curriculum-builder-approval-gate.md` requirements satisfied
- [ ] Completed `docs/curriculum-builder-decision-intake-template.md` attached
- [ ] No scanning, ingestion, or cloud resolution unless separately approved
- [ ] No student data
- [ ] Validation and rollback plan attached

### Output contract schema activation

- [ ] Completed track intake naming each output contract category
- [ ] No renderers or lesson generation unless separately approved
- [ ] Schema remains planning-only or explicitly scoped schema file PR approved
- [ ] No generated drafts or packages
- [ ] Validation and rollback plan attached

### Validators/renderers

- [ ] Completed track intake naming validator/renderer scope
- [ ] Read-only PASS/WARN/FAIL semantics preserved
- [ ] No file reads beyond explicitly approved sample paths
- [ ] No network calls or APIs
- [ ] Validation and rollback plan attached

### Drive/NAS/iCloud resolution

- [ ] Completed track intake naming storage systems affected
- [ ] No live path resolution without explicit approval
- [ ] No OAuth, secrets, or network calls unless separately approved PR
- [ ] Metadata/reference-only default preserved
- [ ] Validation and rollback plan attached

### Canvas export/package work

- [ ] Completed track intake referencing frozen Canvas LLM foundation
- [ ] Stop marker and freeze docs reviewed
- [ ] No Canvas API, exporter, or package generator unless explicitly approved
- [ ] No unfreezing Canvas as default next track
- [ ] Validation and rollback plan attached

### Ingestion/RAG/vector/search work

- [ ] Completed track intake naming ingestion and search scope
- [ ] No folder scanning, crawling, indexing, OCR, or embeddings unless explicitly approved
- [ ] No vector database activation unless explicitly approved
- [ ] No student data in corpus or indexes
- [ ] Validation and rollback plan attached

### Lesson generation/review generation

- [ ] Completed track intake naming generation outputs
- [ ] No generated lesson drafts in gitignored paths without explicit policy
- [ ] No generated review notes presented as classroom-ready
- [ ] Human review boundary preserved
- [ ] Validation and rollback plan attached

### Automation/background jobs

- [ ] Completed track intake naming scheduler/automation scope
- [ ] No unattended network calls
- [ ] No launch agents, cron, or background jobs unless explicitly approved
- [ ] Dry-run or manual-trigger default preferred
- [ ] Validation and rollback plan attached

## Relationship to Track-Specific Gates

| Track | Track-specific gate |
| --- | --- |
| Engineering authority | `docs/engineering-constitution.md` |
| Curriculum Builder | `docs/curriculum-builder-approval-gate.md` |
| Curriculum Builder intake | `docs/curriculum-builder-decision-intake-template.md` |
| Canvas LLM | `docs/canvas-llm-planning-foundation-freeze.md`, stop marker |
| Cursor workflow | `.cursor/rules/teacher-ai-workstation-senior-engineer.mdc` |

Track-specific gates add requirements on top of this repo-wide gate. They do not replace it.

## Relationship to Section Completion Audits

| Audit | Role |
| --- | --- |
| `docs/implementation-approval-gate.md` | Repo-wide implementation gate and track intake checklists |
| `docs/curriculum-builder-section-completion-audit.md` | Curriculum Builder planning foundation complete; implementation approval-gated |
| `docs/canvas-llm-section-completion-audit.md` | Canvas LLM frozen/stopped; runtime approval-gated |

Section completion means planning/status foundation is complete. It does **not** approve implementation.

## Chief of Staff Boundary

Chief of Staff may:

- report static status and confirm this gate doc exists
- show PASS/WARN/FAIL from read-only scripts

Chief of Staff must not:

- cross the gate automatically
- activate implementation without explicit approval
- scan, ingest, resolve cloud paths, call APIs, or generate content

## Validation Expectations

```bash
bash scripts/cursor-workflow-status.sh
bin/chief-of-staff --cursor-workflow-status
```

## Non-Activation Confirmation

Documentation/status only. Implementation approval gate is Markdown-only planning/status text. No schema files, validators, renderers, live registry, ingestion, scanning, folder crawling, file indexing, OCR, embeddings, vector database, APIs, OAuth, network calls, automation, lesson generation, generated lesson drafts, generated review notes, student data, or runtime behavior. Gate status: active. Implementation approval status: not approved.
