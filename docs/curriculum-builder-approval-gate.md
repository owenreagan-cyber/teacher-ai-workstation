# Curriculum Builder Approval Gate

This document defines the approval gate required before any future Curriculum Builder implementation PR. implementation blocked until approval. This note does not start implementation.

## Current planning status

The Curriculum Builder / Curriculum Resource Registry planning stack is documentation/status-only. Planning artifacts define boundaries, vocabulary, and future decision paths. No active registry, schema, validator, connector, or generation behavior exists.

## What is complete

- Local-first foundation plan
- Source storage strategy
- Metadata-only registry plan and section notes
- Planning stack summary
- Next-phase decision note
- Decision intake template
- Read-only curriculum builder foundation status checks
- Chief of Staff reporting through existing status commands only

## What is intentionally not active

- active schema files or schema activation
- database tables or migrations
- registry data
- validators, parsers, scanners, or crawlers
- import/export or backup scripts
- entry forms or new commands
- Drive connector activation
- NAS connector activation
- iCloud connector activation
- Canvas connector activation
- file reads, hashing, scanning, indexing, OCR, or embeddings
- APIs, OAuth, network calls, automation, or live integrations
- background jobs or scheduler
- lesson generation, generated lesson briefs/drafts, or real review notes
- storage migration or raw curriculum file duplication
- student data handling

## Required approval before implementation

Any future implementation PR must cross this approval gate only after explicit human approval. Documentation/status PRs may continue under the current pattern without crossing the gate.

## Approved decision intake requirement

Implementation is blocked until a future PR includes a completed and explicitly approved decision intake using `docs/curriculum-builder-decision-intake-template.md`.

The completed decision intake requirement must include:

- decision title
- requested path
- approval level
- proposed next PR scope
- explicitly allowed work and explicitly blocked work
- impact review for storage, registry, Teacher Workstation, Chief of Staff, and dashboard/status
- rollback plan and validation commands
- final approval checkbox completed

## Allowed documentation/status-only PRs

- planning summaries and audit notes
- non-activation boundary notes
- read-only repo-local status marker checks
- cross-references between existing planning docs
- decision intake template refinements that remain blank templates only

## Blocked implementation PRs

Without a completed approved decision intake, these PR types remain blocked:

- schema activation or registry data files
- database or migration work
- validator or command implementation
- dashboard section additions that change health semantics
- connector, API, OAuth, or network behavior
- file reads, scanning, indexing, OCR, embeddings, or vector database work
- automation, background jobs, or schedulers
- lesson generation or student-facing output
- storage migration or raw curriculum file duplication

## future implementation entry criteria

A future implementation PR may be proposed only when all of the following are true:

1. A completed decision intake exists and is explicitly approved.
2. The requested path matches an allowed next path from `docs/curriculum-builder-next-phase-decision.md`.
3. The PR answers the implementation approval gate questions in `docs/curriculum-resource-registry-plan.md`.
4. Safety boundaries for teacher-only, student-facing, answer-key, assessment, restricted, blocked, retired, and do_not_use postures are preserved.
5. Existing PASS/WARN/FAIL semantics and dashboard behavior are preserved unless explicitly approved otherwise.
6. Rollback and validation strategy are documented in the PR.

## required validation before crossing the gate

Before merge, the future PR must pass at minimum:

```bash
bash scripts/lesson-planning-template-readiness-status.sh
bash scripts/curriculum-builder-foundation-status.sh
bin/chief-of-staff --curriculum-builder-foundation-status
bash scripts/phase-1-status.sh
bin/chief-of-staff --dashboard
bash tests/smoke-chief-of-staff-cli.sh
git diff --check
```

## Required final local main proof

After merge, local `main` must show:

- clean git status, up to date with `origin/main`
- lesson-planning readiness with no FAIL lines
- curriculum builder foundation status with no FAIL lines
- dashboard health with no FAIL lines
- branch deleted locally and remotely
- final validation commands re-run on local `main`

## rollback expectations

Any PR that crosses the gate must document how to revert files, commands, data artifacts, and status checks. Rollback must restore prior PASS/WARN/FAIL semantics and dashboard health count unless explicitly approved otherwise.

## Relationship to Teacher Workstation

Teacher Workstation relationship: Teacher Workstation may use Curriculum Builder planning later only after an approved implementation PR. No Teacher Workstation runtime behavior changes occur at this gate. No lesson-planning registry reference or generation is activated.

## Relationship to Chief of Staff

Chief of Staff relationship: Chief of Staff continues reporting planning/status readiness through existing read-only checks. Chief of Staff does not own raw curriculum files, scan folders, call APIs, validate real registry records, back up files, or generate content in this phase.

curriculum registry relationship: Future curriculum registry work remains metadata/reference-only until explicitly approved. Registry records must not copy raw files by default and must not contain student data.

## Safety boundaries preserved

Unless explicitly approved in a completed decision intake, preserve:

- no document scanning
- no folder scanning
- no file indexing
- no scanning/indexing/OCR/embeddings
- no OCR
- no embeddings
- no vector database
- no real lesson generation
- no lesson generation
- no generated lesson briefs/drafts
- no real review notes
- no student data
- no network calls
- no APIs/OAuth/network calls
- no APIs
- no OAuth
- no automation/live integrations
- no automation
- no live integrations
- no background jobs
- no scheduler
- no Drive connector activation
- no NAS connector activation
- no iCloud connector activation
- no Canvas connector activation
- no storage migration/raw file duplication
- no storage migration
- no raw curriculum file duplication
- no registry data
- no schema activation
- no parser
- no crawler
- no command removals or renames
- no check removals
- no dashboard behavior changes

## Non-Activation confirmation

This approval gate note does not add active schema, database tables, migrations, registry data files, validators, commands, connectors, APIs, automation, scanning, indexing, OCR, embeddings, lesson generation, student data, or live integrations.
