# Curriculum Builder Canonical Planning Index

This document is the canonical entry point for Curriculum Builder / Curriculum Resource Registry planning. It is documentation/status only and does not start implementation.

## current state summary

Curriculum Builder planning is complete through PR #124. Post-closeout alignment through PR #132 hardened Chief of Staff status-command wording. The stack is documentation/status-only. Implementation is paused behind an explicit approval gate. Latest completed PR reference: PR #124 — Phase 1 curriculum builder status closeout note (`817480a`). Next-stage transition note: `docs/curriculum-builder-next-stage-readiness-audit.md`. Manual registry schema plan: `docs/curriculum-builder-manual-registry-schema-plan.md`. Manual registry sample proof plan: `docs/curriculum-builder-manual-registry-sample-proof-plan.md`.

## planning stack purpose

planning stack purpose: define local-first curriculum organization boundaries, metadata/reference vocabulary, approval gates, and maintainer workflows without activating registry, schema, validator, connector, or generation behavior.

## local-first architecture summary

local-first architecture summary: raw curriculum files remain in Google Drive, NAS, iCloud, or local folders. Teacher Workstation stores metadata, references, and planning records only. Chief of Staff reports planning/status readiness through read-only checks.

## storage model summary

storage model summary:

- Google Drive: active working curriculum files
- NAS: archive/vault curriculum files
- iCloud: optional convenience sync copies
- local folders: manually managed references only if explicitly approved
- no storage migration
- no raw curriculum file duplication

## metadata/reference-only registry summary

metadata/reference-only registry summary: future registry records reference source storage but must not copy raw files by default. Registry records must not contain student data. Any real registry records require explicit approval.

## Teacher Workstation relationship

Teacher Workstation relationship: may reference approved planning docs later. No runtime registry reference or lesson generation is activated in this phase.

## Chief of Staff relationship

Chief of Staff relationship: reports planning/status readiness through read-only proof surfaces only — `bin/chief-of-staff --curriculum-builder-foundation-status` and `bin/chief-of-staff --dashboard`. These commands report PASS/WARN/FAIL only. They do not own raw curriculum files, scan folders, call APIs, activate implementation, or generate content.

## approval gate summary

approval gate summary: `docs/curriculum-builder-approval-gate.md` blocks implementation until a future PR crosses the gate with explicit approval.

## decision intake summary

decision intake summary: `docs/curriculum-builder-decision-intake-template.md` is the required blank intake form. Implementation PRs must include a completed and explicitly approved intake.

## maintainer handoff summary

maintainer handoff summary: `docs/curriculum-builder-maintainer-handoff.md` explains current state, blocked work, safe categories, and session hand-off guidance for future maintainers and AI sessions.

## future PR checklist summary

future PR checklist summary: `docs/curriculum-builder-future-pr-checklist.md` is the reusable checklist for every future Curriculum Builder PR.

## artifact map

| Artifact | Path | Purpose |
| --- | --- | --- |
| Local-first foundation plan | `docs/curriculum-builder-local-first-foundation-plan.md` | Defines local-first Curriculum Builder foundation and source-reference model |
| Source storage strategy | `docs/curriculum-source-storage-strategy.md` | Defines Drive/NAS/iCloud/local folder ownership and reference boundaries |
| Resource registry plan | `docs/curriculum-resource-registry-plan.md` | Metadata-only registry concept, field inventory, safety values, workflows, validator planning, placeholder shape, approval gate sections |
| Integration/relationship docs | `docs/curriculum-resource-registry-plan.md` (relationship sections) | Teacher Workstation and Chief of Staff relationship planning within registry sections |
| Status/foundation summaries | `docs/curriculum-builder-planning-stack-summary.md` | Audit index of planning stack areas, storage boundaries, allowed/blocked work |
| Next-phase decision note | `docs/curriculum-builder-next-phase-decision.md` | Next-phase decision paths and pause recommendation |
| Decision intake template | `docs/curriculum-builder-decision-intake-template.md` | Blank reusable intake form for future approval |
| Approval gate | `docs/curriculum-builder-approval-gate.md` | Explicit gate before implementation |
| Planning closeout | `docs/curriculum-builder-planning-closeout.md` | Closeout summary of completed planning stack |
| Maintainer handoff | `docs/curriculum-builder-maintainer-handoff.md` | Maintainer and AI session handoff |
| Future PR checklist | `docs/curriculum-builder-future-pr-checklist.md` | Reusable future PR checklist |
| Canonical planning index | `docs/curriculum-builder-canonical-planning-index.md` | This document: where to start and how to route next work |
| Next-stage readiness audit | `docs/curriculum-builder-next-stage-readiness-audit.md` | Canonical transition note for bounded next-stage planning work |
| Manual registry schema plan | `docs/curriculum-builder-manual-registry-schema-plan.md` | Planned manual/static registry field schema and fictional placeholder rows |
| Manual registry sample proof plan | `docs/curriculum-builder-manual-registry-sample-proof-plan.md` | Plans future fictional sample registry artifact rules and validation |
| Foundation status script | `scripts/curriculum-builder-foundation-status.sh` | Read-only PASS/WARN/FAIL status checks |

## Start Here

- **For maintainers:** start with this canonical planning index, then `docs/curriculum-builder-maintainer-handoff.md` and `docs/curriculum-builder-next-stage-readiness-audit.md`.
- **For future ChatGPT/Cursor sessions:** start with `docs/curriculum-builder-next-stage-readiness-audit.md`, then `docs/curriculum-builder-maintainer-handoff.md` and `docs/curriculum-builder-future-pr-checklist.md`.
- **For implementation requests:** start with `docs/curriculum-builder-approval-gate.md` and `docs/curriculum-builder-decision-intake-template.md`.
- **For status verification:** run `bin/chief-of-staff --curriculum-builder-foundation-status` and `bin/chief-of-staff --dashboard`.

## Safe Next PR Routing

| Category | Route |
| --- | --- |
| Documentation/status-only cleanup | Continue docs/status PRs using current pattern, future PR checklist, and next-stage readiness audit |
| Decision intake drafting | Use decision intake template only; do not create registry data |
| Approval gate review | Review or refine approval gate docs only |
| Manual registry planning only | Extend registry planning per schema plan and sample proof plan without schema/data activation |
| Implementation, blocked until approved | Requires completed approved decision intake and approval gate crossing |
| Connector/API/scanning/indexing/generation work, blocked until approved | Blocked until explicit approval through gate and intake |

## Do Not Start Here

Future sessions must not begin with:

- schema creation
- registry data creation
- file scanning
- folder scanning
- file indexing
- OCR
- embeddings
- parsers
- crawlers
- APIs
- OAuth
- automation
- live integrations
- lesson generation
- generated lesson briefs/drafts
- real review notes
- student data handling
- storage migration
- raw curriculum file duplication

## blocked work summary

blocked work summary: schema activation, registry data, validators, new commands, connectors, file reads, scanning, indexing, OCR, embeddings, APIs, OAuth, automation, lesson generation, student data, storage migration, and raw curriculum file duplication remain blocked unless explicitly approved through the approval gate and completed decision intake.

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

## Safety boundaries preserved

Unless explicitly approved through the approval gate and completed decision intake:

- no document scanning
- no folder scanning
- no file indexing
- no scanning/indexing/OCR/embeddings
- no OCR
- no embeddings
- no vector database
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
- no storage migration
- no raw curriculum file duplication
- no registry data
- no schema activation

## Non-Activation confirmation

This canonical planning index does not add active schema, database tables, migrations, registry data files, validators, commands, connectors, APIs, automation, scanning, indexing, OCR, embeddings, lesson generation, student data, or live integrations.
