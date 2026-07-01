# Curriculum Builder Maintainer Handoff

This document is maintainer-facing documentation only. It helps a future developer, Cursor session, or ChatGPT session understand the current Curriculum Builder state without activating implementation.

## current state summary

Curriculum Builder planning is complete through PR #120. The stack is documentation/status-only. Implementation is paused behind an explicit approval gate.

## latest completed PR reference

Latest completed PR reference:

- PR #120 — Curriculum builder approval gate and planning closeout
- Merge commit: `535f7be62e788a8c359a6aca891ac743d4821d8c`
- Local main short commit: `535f7be`

Prior stack PRs: #107–#120 built local-first foundation, registry boundaries, planning summaries, next-phase decision guidance, decision intake template, approval gate, and planning closeout.

## planning stack status

Planning stack status: complete enough for now. Artifacts define boundaries and vocabulary only. No active registry, schema, validator, connector, or generation behavior exists.

Key docs:

- `docs/curriculum-builder-local-first-foundation-plan.md`
- `docs/curriculum-source-storage-strategy.md`
- `docs/curriculum-resource-registry-plan.md`
- `docs/curriculum-builder-planning-stack-summary.md`
- `docs/curriculum-builder-next-phase-decision.md`
- `docs/curriculum-builder-decision-intake-template.md`
- `docs/curriculum-builder-approval-gate.md`
- `docs/curriculum-builder-planning-closeout.md`
- `docs/curriculum-builder-maintainer-handoff.md`
- `docs/curriculum-builder-future-pr-checklist.md`

## What Curriculum Builder is intended to become

A local-first, metadata/reference-only curriculum registry that helps Teacher Workstation organize curriculum resource references while raw files remain in Google Drive, NAS, iCloud, or local folders.

## What Curriculum Builder is not yet allowed to do

Curriculum Builder is not yet allowed to activate schema, registry data, validators, commands, connectors, file reads, scanning, APIs, automation, or lesson generation without crossing the approval gate with a completed decision intake.

## local-first storage model

local-first storage model summary:

- Google Drive: active working curriculum files
- NAS: archive/vault curriculum files
- iCloud: optional convenience sync copies
- local folders: manually managed references only if explicitly approved
- no storage migration
- no raw curriculum file duplication

## metadata/reference-only registry direction

metadata/reference-only registry direction: Teacher Workstation stores metadata, references, and planning records only. Registry records must not copy raw files by default and must not contain student data.

## Teacher Workstation relationship

Teacher Workstation relationship: may reference approved planning docs later. No runtime registry reference or lesson generation is activated in this phase.

## Chief of Staff relationship

Chief of Staff relationship: reports planning/status readiness through existing read-only proof surfaces only. Status commands report PASS/WARN/FAIL and do not activate implementation. Does not own raw curriculum files, scan folders, call APIs, validate real registry records, back up files, or generate content.

## approval gate requirement

approval gate requirement: any implementation PR must satisfy `docs/curriculum-builder-approval-gate.md` before merge.

## decision intake requirement

decision intake requirement: implementation is blocked unless a future PR includes a completed and explicitly approved decision intake using `docs/curriculum-builder-decision-intake-template.md`.

## current status commands

current status commands:

```bash
bash scripts/curriculum-builder-foundation-status.sh
bin/chief-of-staff --curriculum-builder-foundation-status
```

## required validation commands

required validation commands:

```bash
bash scripts/lesson-planning-template-readiness-status.sh
bash scripts/curriculum-builder-foundation-status.sh
bin/chief-of-staff --curriculum-builder-foundation-status
bash scripts/phase-1-status.sh
bin/chief-of-staff --dashboard
bash tests/smoke-chief-of-staff-cli.sh
git diff --check
```

## final local main proof requirements

final local main proof requirements after merge:

- clean git status on `main`, up to date with `origin/main`
- lesson-planning readiness: no FAIL lines
- curriculum builder foundation: no FAIL lines
- dashboard health: no FAIL lines
- branch deleted locally and remotely
- validation commands re-run on local `main`

## safe next PR categories

safe next PR categories:

- documentation/status hardening
- planning summaries and audit notes
- read-only status marker checks
- maintainer handoff or checklist refinements
- pause and return to another repo priority

## blocked PR categories

blocked PR categories without approved decision intake:

- schema activation or registry data
- database or migration work
- validator or new command implementation
- connector, API, OAuth, or network behavior
- file reads, scanning, indexing, OCR, embeddings, or vector database work
- automation, background jobs, or scheduler
- lesson generation or student-facing output
- storage migration or raw curriculum file duplication
- command removals or renames
- check removals
- dashboard behavior changes

## Safety boundaries preserved

Unless explicitly approved through the approval gate and completed decision intake, these remain blocked:

- document scanning
- folder scanning
- file indexing
- no scanning/indexing/OCR/embeddings
- OCR
- embeddings
- vector database
- real lesson generation
- no lesson generation
- generated lesson briefs/drafts
- real review notes
- no student data
- no network calls
- no APIs/OAuth/network calls
- APIs
- OAuth
- no automation/live integrations
- automation
- live integrations
- background jobs
- scheduler
- Drive connector activation
- NAS connector activation
- iCloud connector activation
- Canvas connector activation
- storage migration
- raw curriculum file duplication
- registry data
- schema activation
- parser
- crawler
- command removals or renames
- check removals
- dashboard behavior changes

## Non-Activation confirmation

This maintainer handoff does not add active schema, database tables, migrations, registry data files, validators, commands, connectors, APIs, automation, scanning, indexing, OCR, embeddings, lesson generation, student data, or live integrations.

## Hand-off note for future ChatGPT/Cursor sessions

Hand-off note for future ChatGPT/Cursor sessions:

1. Read `docs/curriculum-builder-planning-closeout.md` and `docs/curriculum-builder-approval-gate.md` first.
2. Use `docs/curriculum-builder-future-pr-checklist.md` for every new Curriculum Builder PR.
3. Default to documentation/status-only work.
4. Do not implement schema, data, validators, commands, connectors, or generation without a completed approved decision intake.
5. Preserve existing commands, checks, PASS/WARN/FAIL semantics, dashboard health count, full PR lifecycle, branch deletion verification, and final local main dashboard proof.
