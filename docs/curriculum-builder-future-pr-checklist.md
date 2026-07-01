# Curriculum Builder Future PR Checklist

Reusable checklist for every future Curriculum Builder PR. Complete before opening the PR. This checklist is documentation only and does not activate implementation.

Start from `docs/curriculum-builder-next-stage-readiness-audit.md` for next-stage scope class, blocked work, and validation expectations.

For manual/static registry field schema planning, see `docs/curriculum-builder-manual-registry-schema-plan.md`.

For future fictional sample registry proof rules, see `docs/curriculum-builder-manual-registry-sample-proof-plan.md`.

For the static fictional sample artifact, see `docs/curriculum-builder-manual-registry-sample-proof.md`.

For static sample validation planning, see `docs/curriculum-builder-static-sample-validation-plan.md`. For implemented static checks, see `docs/curriculum-builder-static-sample-validation-checks.md`. For sample format policy, see `docs/curriculum-builder-sample-format-decision.md`. For future CSV placeholder planning, see `docs/curriculum-builder-csv-placeholder-sample-plan.md`.

## PR title and type

- [ ] PR title states docs/status vs implementation clearly
- [ ] PR type matches an allowed next path from `docs/curriculum-builder-next-phase-decision.md`

## approval status

- [ ] Documentation/status PR uses current docs/status pattern, or
- [ ] Implementation PR has explicit approval through `docs/curriculum-builder-approval-gate.md`

## decision intake link/status

- [ ] decision intake link/status documented
- [ ] If implementation-related, completed intake from `docs/curriculum-builder-decision-intake-template.md` is attached and approved

## scope classification

- [ ] scope classification: documentation/status only | planning only | blocked implementation
- [ ] Scope does not drift into runtime behavior accidentally

## files expected to change

- [ ] files expected to change listed explicitly
- [ ] Only planning docs and read-only status scripts unless explicitly approved otherwise

## files that must not change

- [ ] files that must not change listed explicitly
- [ ] No unexpected command, dashboard, or lesson-generation files modified

## commands that must remain unchanged

- [ ] commands that must remain unchanged unless explicitly approved
- [ ] No new Chief of Staff command unless explicitly approved
- [ ] No command removals or renames

## checks that must remain unchanged

- [ ] checks that must remain unchanged unless adding auditable read-only markers
- [ ] No check removals

## PASS/WARN/FAIL preservation

- [ ] PASS/WARN/FAIL preservation confirmed
- [ ] No weakening of existing PASS checks
- [ ] No new WARN or FAIL lines introduced unintentionally

## dashboard health preservation

- [ ] dashboard health preservation confirmed
- [ ] Dashboard health count unchanged unless existing repo pattern requires it
- [ ] No dashboard behavior changes unless explicitly approved

## storage impact

- [ ] storage impact reviewed
- [ ] no storage migration
- [ ] no raw curriculum file duplication
- [ ] no Drive connector activation
- [ ] no NAS connector activation
- [ ] no iCloud connector activation

## registry impact

- [ ] registry impact reviewed
- [ ] no registry data
- [ ] no schema activation
- [ ] no fake registry data files unless explicitly approved as docs-only examples

## Teacher Workstation impact

- [ ] Teacher Workstation impact reviewed
- [ ] No lesson-planning registry reference activation
- [ ] no lesson generation

## Chief of Staff impact

- [ ] Chief of Staff impact reviewed
- [ ] Existing `--curriculum-builder-foundation-status` path preserved unless explicitly approved

## Safety boundary confirmation

Confirm these remain blocked unless explicitly approved through the approval gate and completed decision intake:

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
- automation
- live integrations
- background jobs
- scheduler
- Canvas connector activation
- parser
- crawler
- command removals or renames
- check removals
- dashboard behavior changes

## validation commands

validation commands to run before merge:

```bash
bash scripts/lesson-planning-template-readiness-status.sh
bash -n scripts/lesson-planning-template-readiness-status.sh
bash -n tests/smoke-chief-of-staff-cli.sh
bash -n scripts/curriculum-builder-foundation-status.sh
bash -n scripts/phase-1-status.sh
bash scripts/curriculum-builder-foundation-status.sh
bin/chief-of-staff --curriculum-builder-foundation-status
bash scripts/phase-1-status.sh
bin/chief-of-staff --dashboard
bash tests/smoke-chief-of-staff-cli.sh
git diff --check
git status
```

## PR body requirements

- [ ] PR body requirements met: summary, files changed, safety boundaries, validation results
- [ ] Explicit statement that PR is documentation/status only unless approved otherwise
- [ ] Confirmation that no scanning, indexing, OCR, embeddings, APIs, automation, storage migration, registry data, schema activation, or lesson-generation behavior was added unless explicitly approved

## merge requirements

- [ ] merge requirements: all checks pass, review complete, full PR lifecycle preserved
- [ ] existing commands preserved
- [ ] existing checks preserved

## branch deletion verification

- [ ] branch deletion verification planned: delete remote and local branch after merge
- [ ] `git fetch --prune` after deletion

## final local main proof

- [ ] final local main proof planned after merge
- [ ] Re-run validation commands on local `main`
- [ ] Confirm dashboard health with no FAIL lines

## rollback notes

- [ ] rollback notes documented
- [ ] Revert path is simple and auditable

## Non-Activation confirmation

This checklist does not add active schema, database tables, migrations, registry data files, validators, commands, connectors, APIs, automation, scanning, indexing, OCR, embeddings, lesson generation, student data, or live integrations.

## Full lifecycle preservation

Every future PR must preserve:

- existing commands
- existing checks
- PASS/WARN/FAIL semantics
- full PR lifecycle
- branch deletion verification
- final local main dashboard proof
