# Curriculum Builder Next-Stage Readiness Audit

Last verified: 2026-06-30

This document is the canonical transition note for the next strategic stage of local-first **Curriculum Builder / Curriculum Library / Curriculum Resource Registry** work. It is documentation/status only. It does not activate implementation, scanning, indexing, APIs, automation, or lesson generation.

## Naming glossary

Use these terms consistently across docs and prompts:

| Term | Meaning |
| --- | --- |
| **Curriculum Builder** | Product/track name for local-first curriculum organization work in Teacher Workstation |
| **Curriculum Library** | User-facing label for the future organized curriculum reference surface; planning synonym for Curriculum Builder |
| **Curriculum Resource Registry** | Metadata/reference registry concept documented in `docs/curriculum-resource-registry-plan.md` |
| **curriculum registry** | Shorthand for the future metadata/reference registry; not an active database or file store today |

Chief of Staff and Teacher Workstation **reference** registry boundaries and readiness. They do **not** own raw curriculum files.

## 1. Current status baseline

Repo baseline after PR #132 (Chief of Staff status command consistency audit):

| Check | Expected posture |
| --- | --- |
| Lesson-planning readiness | PASS 110 / WARN 0 / FAIL 0 |
| Curriculum Builder foundation | PASS 597+ / WARN 0 / FAIL 0 (may increase when this audit adds read-only doc checks) |
| Wallpaper handoff safety | PASS 48 / WARN 0 / FAIL 0 |
| Return-to-core | PASS 19 / WARN 0 / FAIL 0 |
| Phase 1 | PASS 284 / WARN 0 / FAIL 0 |
| Prompt-pack stale-reference audit | PASS 62 / WARN 0 / FAIL 0 |
| Dashboard | PASS 87 / WARN 0 / FAIL 0 |

Planning stack status: **complete and parked**. Implementation remains blocked behind `docs/curriculum-builder-approval-gate.md` and a completed `docs/curriculum-builder-decision-intake-template.md`.

Canonical entry point: `docs/curriculum-builder-canonical-planning-index.md`.

## 2. What is already ready

The following planning foundations are in place and verified by read-only status checks:

- Local-first foundation plan with source-reference model
- Manual registry schema plan (`docs/curriculum-builder-manual-registry-schema-plan.md`)
- Manual registry sample proof plan (`docs/curriculum-builder-manual-registry-sample-proof-plan.md`)
- Manual registry sample proof (`docs/curriculum-builder-manual-registry-sample-proof.md`)
- Static sample validation plan (`docs/curriculum-builder-static-sample-validation-plan.md`)
- Source storage strategy (Google Drive, NAS, iCloud, local folders)
- Metadata-only Curriculum Resource Registry plan (field inventory, safety values, manual-first workflow, validator planning, placeholder shape, approval gate sections)
- Planning stack summary and next-phase decision note
- Decision intake template and approval gate
- Planning closeout and maintainer handoff
- Future PR checklist
- Canonical planning index surfaced in dashboard docs
- Chief of Staff read-only proof surfaces: `bin/chief-of-staff --curriculum-builder-foundation-status`, `bin/chief-of-staff --dashboard`
- Repo-wide parked-track map in `docs/phase-1-chief-of-staff-status-audit.md`

The workstation is ready for **bounded, auditable, documentation/status-first** next-stage planning PRs. It is **not** ready for autonomous ingestion, connector activation, or lesson generation without explicit approval.

## 3. What is still planning-only

All of the following remain **planning vocabulary and documentation only**:

- Registry field inventories and safety/status value lists
- Manual-first entry workflow stages
- Metadata-only backup/export planning
- Local validator **planning** (PASS/WARN/FAIL semantics for a future validator, not a live validator)
- Placeholder metadata shape examples (prose/fake examples only; no registry data files)
- Teacher Workstation future reference patterns (how lesson planning might reference approved metadata later)
- Chief of Staff future status/reporting boundaries
- Connector/API/OAuth **planning** sections (Drive, NAS, iCloud, Canvas remain future-only)
- Schema decision notes (prose only; no live schema file)

Future registry work must start **manual and static** (human-authored planning records, fictional samples in docs) before any automation, file reads, or connectors.

## 4. What is explicitly not active

Unless a future PR crosses the approval gate with a completed approved decision intake, the following are **not active**:

- no document scanning
- no folder scanning
- file indexing
- OCR
- embeddings
- vector database
- AI parsing
- real lesson generation
- generated lesson briefs or drafts
- real review notes
- student data handling
- Google Drive API
- Canvas API
- iCloud integration
- NAS crawler
- network calls
- OAuth
- background jobs
- scheduler
- automation
- live integrations
- hosted storage requirement for raw files
- Supabase requirement for raw files
- new runtime services
- new package dependencies
- registry data files (JSON/CSV/YAML)
- active schema files
- active validators
- no raw curriculum file duplication into the repo or app-owned storage

## 5. Safe next PR categories

| Category | May add | Must not activate |
| --- | --- | --- |
| Documentation/status hardening | Audit notes, cross-links, readiness criteria, naming clarity | Schema, data, commands, validators, runtime |
| Next-stage planning notes | Bounded planning sections for manual registry stages | File reads, scanning, connectors |
| Read-only status marker checks | Static doc-presence PASS checks in foundation status script | Behavior, folder scans, network |
| Decision intake drafting | Blank or example intake prose in docs only | Implementation |
| Approval gate review | Gate doc refinements | Implementation |
| Manual registry planning only | Prose field/workflow refinements per manual registry schema plan | Registry data files, validators |
| Pause / return to other tracks | Handoff clarity only | Any Curriculum Builder runtime |

Substantial next-stage PRs are allowed when they remain **local-first, metadata/reference-only, manual/static-first, and auditable**.

## 6. What must remain blocked

Blocked without explicit approval through gate + completed decision intake:

- schema activation
- registry data creation
- validator implementation
- new Chief of Staff commands (unless explicitly approved)
- command removals or renames
- dashboard behavior or health-count drift without documented reason
- check removals
- connector/API/OAuth/network behavior
- file reads outside repo planning docs
- hashing of user curriculum files
- crawlers, parsers, indexers, importers
- lesson generation or student-facing output
- storage migration
- Chief of Staff does not own raw curriculum files; it reports readiness through read-only proof surfaces only

## 7. Cursor self-check expectations for future substantial prompts

Future substantial Curriculum Builder prompts should include these stages:

1. **Baseline self-check** — run validation suite on clean `main` before editing; stop on FAIL.
2. **Audit** — read canonical index, this readiness note, maintainer handoff, and approval gate; confirm scope class.
3. **Self-review** — `git diff` for activation wording, storage-model contradictions, and Chief of Staff ownership errors.
4. **Debug/fix loop** — smallest safe fix on validation failure; re-run failed check.
5. **Final verification** — full validation suite + dashboard on feature branch and again on local `main` after merge.
6. **Handoff** — PR body lists count changes, script changes, and non-activation confirmation.

Do not scan curriculum folders. Do not inspect personal or external curriculum documents. Repo-doc audit only.

## 8. Required validation commands

```bash
bash -n bin/chief-of-staff
bash scripts/lesson-planning-template-readiness-status.sh
bash scripts/curriculum-builder-foundation-status.sh
bash scripts/wallpaper-photo-rotation-handoff-safety-status.sh
bin/chief-of-staff --return-to-core-status
bash scripts/phase-1-status.sh
bin/chief-of-staff --prompt-pack-stale-reference-audit-status
bin/chief-of-staff --dashboard
bash tests/smoke-chief-of-staff-cli.sh
git status
```

After merge on local `main`:

```bash
git switch main
git pull --ff-only
bin/chief-of-staff --dashboard
```

## 9. PR handoff template for future Curriculum Builder work

Copy into future PR descriptions:

```markdown
## Curriculum Builder scope class
- [ ] documentation/status only
- [ ] planning only (manual/static)
- [ ] blocked implementation (requires gate + intake)

## Readiness pointers
- Start: docs/curriculum-builder-canonical-planning-index.md
- Next-stage audit: docs/curriculum-builder-next-stage-readiness-audit.md
- Manual registry schema plan: docs/curriculum-builder-manual-registry-schema-plan.md
- Manual registry sample proof plan: docs/curriculum-builder-manual-registry-sample-proof-plan.md
- Checklist: docs/curriculum-builder-future-pr-checklist.md

## Non-activation confirmation
- [ ] No scanning, indexing, OCR, embeddings, APIs, OAuth, automation, or lesson generation activated
- [ ] No registry data files or active schema created
- [ ] No raw curriculum file duplication
- [ ] Chief of Staff remains read-only proof/status/reference only
- [ ] Google Drive, NAS, iCloud, local folders remain source storage

## Validation
- [ ] curriculum-builder-foundation-status: no FAIL
- [ ] dashboard: no FAIL
- [ ] smoke tests passed

## Count changes
- Document any PASS/WARN/FAIL count changes and why
```

## Storage and ownership reminder

- **Google Drive**, **NAS**, **iCloud**, and **local folders** remain source storage for raw curriculum files.
- Teacher Workstation stores **metadata, source references, optional content hashes (planning only), review status, planning status, and relationships** — not paid duplicate copies of every raw file.
- Chief of Staff reports readiness through **read-only proof surfaces** (`bin/chief-of-staff --curriculum-builder-foundation-status`, `bin/chief-of-staff --dashboard`). It does not own curriculum files, orchestrate implementation, or modify repository state.

## Related documents

- `docs/curriculum-builder-canonical-planning-index.md`
- `docs/curriculum-builder-maintainer-handoff.md`
- `docs/curriculum-builder-next-phase-decision.md`
- `docs/curriculum-builder-approval-gate.md`
- `docs/curriculum-builder-future-pr-checklist.md`
- `docs/curriculum-builder-local-first-foundation-plan.md`
- `docs/curriculum-builder-manual-registry-schema-plan.md`
- `docs/curriculum-builder-manual-registry-sample-proof-plan.md`
- `docs/curriculum-resource-registry-plan.md`

## Non-Activation confirmation

This readiness audit does not add active schema, database tables, migrations, registry data files, validators, commands, connectors, APIs, automation, scanning, indexing, OCR, embeddings, lesson generation, student data, or live integrations.
