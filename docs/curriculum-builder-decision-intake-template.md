# Curriculum Builder Decision Intake Template

This document is a reusable template only. It is not a filled decision record. Copy and complete it in a future PR only when an explicit Curriculum Builder next-phase path is being proposed for approval.

## decision title

`[TEMPLATE — fill in proposed decision title]`

## requested path

`[TEMPLATE — select one allowed next path from docs/curriculum-builder-next-phase-decision.md]`

Examples:

- Continue documentation/status hardening
- schema planning only
- fake placeholder fixture planning only
- local validator planning only
- metadata export/import planning only
- Teacher Workstation reference planning only
- Stop Curriculum Builder work for now

## approval level

`[TEMPLATE — current docs/status pattern | explicit approval required | safe default]`

## Related Prior Docs

`[TEMPLATE — list related planning docs, for example:]`

- `docs/curriculum-builder-local-first-foundation-plan.md`
- `docs/curriculum-source-storage-strategy.md`
- `docs/curriculum-resource-registry-plan.md`
- `docs/curriculum-builder-planning-stack-summary.md`
- `docs/curriculum-builder-next-phase-decision.md`
- `docs/curriculum-builder-decision-intake-template.md`

## Problem Being Solved

`[TEMPLATE — describe the planning gap or audit need. Do not describe runtime activation.]`

## proposed next PR scope

`[TEMPLATE — list exact files, docs, and read-only status checks the next PR may add.]`

## explicitly allowed work

`[TEMPLATE — list only work allowed under the selected path.]`

Default allowed examples for docs/status PRs:

- documentation-only planning
- read-only repo-local status marker checks
- planning summaries
- audit notes
- explicit future approval criteria

## explicitly blocked work

`[TEMPLATE — list work that must remain blocked unless separately approved.]`

- active schema files
- database tables
- migrations
- registry JSON/CSV/YAML files
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

## storage impact

`[TEMPLATE — describe whether Google Drive, NAS, iCloud, or local folders ownership changes. Default: none.]`

Boundary reminders:

- Google Drive owns active working curriculum files
- NAS owns archive/vault curriculum files
- iCloud may hold optional convenience sync copies
- local folders may hold manually managed local references only if explicitly approved
- no storage migration
- no raw curriculum file duplication

## registry impact

`[TEMPLATE — describe whether registry planning vocabulary, metadata shape, or future record behavior changes. Default: none.]`

Boundary reminders:

- registry planning remains metadata-only unless explicitly approved
- no registry data files
- no fake registry data files
- no real registry records

## Teacher Workstation impact

`[TEMPLATE — describe whether Teacher Workstation runtime behavior changes. Default: none.]`

Boundary reminders:

- no lesson-planning registry reference activation
- no lesson generation
- no generated lesson briefs
- no generated lesson drafts

## Chief of Staff impact

`[TEMPLATE — describe whether Chief of Staff status reporting changes. Default: existing read-only status only.]`

Boundary reminders:

- Chief of Staff does not own raw curriculum files
- Chief of Staff does not scan, index, validate real registry records, call APIs, back up files, or generate content

## dashboard/status impact

`[TEMPLATE — describe whether dashboard health count, PASS/WARN/FAIL semantics, or existing commands change. Default: none.]`

Boundary reminders:

- no new commands
- no command removals or renames
- no check removals
- preserve existing PASS/WARN/FAIL semantics

## Safety Boundary Review

Confirm the proposed PR preserves these boundaries unless explicitly approved otherwise:

- documentation/status only unless explicitly approved
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
- no automation
- no live integrations
- no background jobs
- no scheduler
- no Drive/NAS/iCloud/Canvas connector activation
- no storage migration
- no raw curriculum file duplication
- no changes to existing command behavior
- no command removals or renames
- no check removals

## rollback plan

`[TEMPLATE — describe how to revert the PR cleanly, including branch deletion and validation proof on local main.]`

## validation commands

`[TEMPLATE — list exact commands that must pass before merge, for example:]`

```bash
bash scripts/lesson-planning-template-readiness-status.sh
bash scripts/curriculum-builder-foundation-status.sh
bin/chief-of-staff --curriculum-builder-foundation-status
bash scripts/phase-1-status.sh
bin/chief-of-staff --dashboard
bash tests/smoke-chief-of-staff-cli.sh
git diff --check
```

## final approval checkbox

`[TEMPLATE — unchecked approval record for human review only]`

- [ ] Requested path is explicitly selected
- [ ] Proposed scope stays within allowed work
- [ ] Blocked work remains blocked
- [ ] Safety boundaries preserved
- [ ] Rollback plan documented
- [ ] Validation commands listed
- [ ] Full PR lifecycle included

## Non-Activation confirmation

This template does not add:

- active schema
- database tables
- migrations
- registry data files
- fake registry data files
- real registry records
- backup scripts
- export scripts
- archive bundles
- file caches
- raw file copying
- Drive mirroring
- NAS mirroring
- iCloud mirroring
- active validators
- entry forms
- new commands
- dashboard sections
- review workflows
- approval workflows
- real review notes
- automated safety classifiers
- importers
- scanners
- crawlers
- parsers
- indexers
- file reads
- hashing
- OCR
- embeddings
- vector search
- APIs
- OAuth
- network calls
- automation
- background jobs
- schedulers
- generated lesson briefs
- generated lesson drafts
- lesson generation
- student data
- live integrations

This template is documentation only. It does not activate implementation behavior.
