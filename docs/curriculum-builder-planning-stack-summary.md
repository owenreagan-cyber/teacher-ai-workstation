# Curriculum Builder Planning Stack Summary

## Purpose

This document summarizes the Curriculum Builder / Curriculum Resource Registry planning stack. It is an audit guide and status index only.

It does not create active schema, data, registry records, validators, commands, APIs, automation, scanning, indexing, or lesson-generation behavior. The planning stack remains local-first and metadata/reference-only.

## Current Baseline

- **Google Drive**, **NAS**, **iCloud**, and **local folders** remain source storage.
- Teacher Workstation stores **metadata/status/reference records only**.
- Chief of Staff reports planning/status readiness through read-only proof surfaces only (PASS/WARN/FAIL status commands).
- Raw curriculum files are not copied into app-owned storage.
- No scanning, indexing, OCR, embeddings, APIs, OAuth, automation, or generation are active.

## Planning Stack Index

| Area | Document / Section | Purpose | Current Activation Status | Explicit Non-Activation Boundary |
| --- | --- | --- | --- | --- |
| Local-first foundation | `docs/curriculum-builder-local-first-foundation-plan.md` | Defines local-first Curriculum Builder foundation and source-reference model | documentation/status only | no active schema, no registry data files, no generation |
| Source storage strategy | `docs/curriculum-source-storage-strategy.md` | Defines Drive/NAS/iCloud/local folder ownership and reference boundaries | documentation/status only | no raw file copying, no mirroring, no APIs |
| Metadata-only registry plan | `docs/curriculum-resource-registry-plan.md` | Defines metadata-only registry concept and planning sections | documentation/status only | no database tables, no validators, no file reads |
| Static registry field inventory | `docs/curriculum-resource-registry-plan.md#static-registry-field-inventory-note` — Static Registry Field Inventory Note | Documents static field inventory for future registry records | planning only | no schema file, no seed data |
| Safety/status values | `docs/curriculum-resource-registry-plan.md#static-registry-safety-and-status-values-note` — Static Registry Safety and Status Values Note | Documents safety and status value vocabulary | planning only | no review workflows, no approval workflows |
| Manual-first entry workflow | `docs/curriculum-resource-registry-plan.md#manual-first-registry-entry-workflow-note` — Manual-First Registry Entry Workflow Note | Documents manual-first entry stages and conservative defaults | planning only | no entry forms, no scanning |
| Metadata-only backup/export planning | `docs/curriculum-resource-registry-plan.md#metadata-only-backup-and-export-planning-note` — Metadata-Only Backup and Export Planning Note | Documents metadata-only backup/export planning boundaries | planning only | no backup scripts, no export scripts |
| Local validator planning | `docs/curriculum-resource-registry-plan.md#local-registry-validator-planning-note` — Local Registry Validator Planning Note | Documents future local validator scope and PASS/WARN/FAIL semantics | planning only | no active validators |
| Placeholder metadata shape | `docs/curriculum-resource-registry-plan.md#placeholder-metadata-shape-note` — Placeholder Metadata Shape Note | Documents fake placeholder metadata record shape | fake placeholder examples only | no fake registry data files, no real registry records |
| Implementation approval gate | `docs/curriculum-resource-registry-plan.md#registry-implementation-approval-gate-note` — Registry Implementation Approval Gate Note | Defines explicit future approval gate before implementation | explicit future approval required | no new commands, no dashboard sections |
| Next-stage readiness audit | `docs/curriculum-builder-next-stage-readiness-audit.md` | Canonical transition note for bounded next-stage planning | documentation/status only | no schema, data, scanning, APIs, or generation |
| Manual registry schema plan | `docs/curriculum-builder-manual-registry-schema-plan.md` | Planned manual/static registry field schema and placeholder rows | planning only | no live registry file, no database, no parser |
| Manual registry sample proof plan | `docs/curriculum-builder-manual-registry-sample-proof-plan.md` | Plans future fictional sample artifact rules | planning only | no sample file consumed by app |
| Manual registry sample proof | `docs/curriculum-builder-manual-registry-sample-proof.md` | Static fictional seven-row sample | documentation proof only | no live registry, no app loader |
| Static sample validation checks | `docs/curriculum-builder-static-sample-validation-checks.md` | Repo-local text-only checks on sample proof | documentation/status only | no runtime validator |
| Sample format decision | `docs/curriculum-builder-sample-format-decision.md` | Markdown-only format decision | documentation only | no CSV/JSON/YAML artifact |
| CSV placeholder sample plan | `docs/curriculum-builder-csv-placeholder-sample-plan.md` | Future CSV safety rules | planning only | no CSV file yet |
| CSV placeholder sample artifact | `docs/examples/curriculum-builder-manual-registry-sample.csv` | Secondary static CSV mirror | documentation only | Markdown canonical |
| CSV static validation maintenance | `docs/curriculum-builder-csv-static-validation-maintenance.md` | Markdown/CSV alignment checklist | documentation only | no parser |
| Static sample validation plan | `docs/curriculum-builder-static-sample-validation-plan.md` | Future static validation rule set | planning only | no validator implementation |
| Output contract foundation | `docs/curriculum-builder-output-contract-foundation.md` | Future output contract planning placeholders | planning only | no schema, validators, renderers, or generation |

## Storage and Ownership Summary

- **Google Drive** owns active working curriculum files.
- **NAS** owns archive/vault curriculum files.
- **iCloud** may hold optional convenience sync copies.
- **local folders** may hold manually managed local references or repo-safe planning fixtures only if explicitly approved.
- Teacher Workstation owns metadata/status/reference records only.
- Chief of Staff owns status reporting only.
- Chief of Staff **does not own raw curriculum files**.

## Registry Boundary Summary

- Registry planning is metadata-only.
- Future registry records may reference source storage but must not copy raw files by default.
- Future registry records must preserve teacher-only, answer-key, assessment-related, restricted, blocked, retired, do_not_use, and student-facing boundaries.
- Registry records must not contain student data.
- Any future real registry records require explicit approval.

## Current Allowed Work

- documentation-only planning
- read-only repo-local status marker checks
- planning summaries
- audit notes
- explicit future approval criteria

## Current Blocked Work Without Explicit Approval

- active schema files
- database tables
- migrations
- registry data files
- fake registry data files
- real registry records
- validators
- new commands
- dashboard sections
- entry forms
- import/export scripts
- backup scripts
- archive bundles
- file caches
- raw file copying
- Drive mirroring
- NAS mirroring
- iCloud mirroring
- file reads
- hashing
- scanning
- indexing
- OCR
- embeddings
- vector search
- APIs
- OAuth
- network calls
- automation
- background jobs
- schedulers
- review workflows
- approval workflows
- real review notes
- generated lesson briefs
- generated lesson drafts
- lesson generation
- student data
- live integrations

## Future PR Decision Path

1. Documentation/status PRs may continue if they remain read-only and repo-local.
2. Any schema/data/validator/command/runtime PR must first answer the implementation approval gate questions.
3. Any real curriculum resource record requires explicit approval.
4. Any network/API/OAuth/connector behavior requires explicit approval.
5. Any lesson-planning runtime reference requires explicit approval.
6. Any generation behavior requires explicit approval.
7. Any rollback and validation strategy must be documented in the future PR.

## Relationship to Teacher Workstation

Teacher Workstation may later use the registry after a separately approved implementation PR. Current Teacher Workstation behavior remains unchanged.

No lesson planning, lesson generation, lesson brief generation, or lesson draft generation is activated.

## Relationship to Chief of Staff

Chief of Staff may report planning/status readiness through existing read-only proof surfaces (PASS/WARN/FAIL status commands only). Chief of Staff must not own curriculum files.

Chief of Staff must not scan folders, index files, call APIs, validate real registry records, back up raw files, or generate content in this phase.

## Explicit Non-Activation

This summary does not add:

- no active schema
- no database tables
- migrations
- no registry data files
- no fake registry data files
- no real registry records
- backup scripts
- export scripts
- archive bundles
- file caches
- raw file copying
- Drive mirroring
- NAS mirroring
- iCloud mirroring
- no active validators
- entry forms
- no new commands
- no dashboard sections
- review workflows
- approval workflows
- real review notes
- automated safety classifiers
- importers
- scanners
- crawlers
- parsers
- indexers
- no file reads
- no hashing
- no scanning
- no indexing
- no OCR
- no embeddings
- no vector search
- no APIs
- no OAuth
- no network calls
- no automation
- no background jobs
- no schedulers
- no generated lesson briefs
- no generated lesson drafts
- no lesson generation
- no student data
- no live integrations
