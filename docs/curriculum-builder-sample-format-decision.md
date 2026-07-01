# Curriculum Builder Sample Format Decision

Last verified: 2026-06-30

## 1. Purpose

This document records the **sample format decision** for the Curriculum Builder manual registry proof stack after PR #138 completed repo-local static text checks on the Markdown sample proof.

The decision makes the next safe sample-format path explicit before any secondary format artifact, parser, importer, loader, or runtime validator is introduced.

Planning path:

```text
canonical planning index
→ next-stage readiness audit
→ manual registry schema plan
→ manual registry sample proof plan
→ manual registry sample proof
→ static sample validation plan
→ static sample validation checks
→ sample format decision (this document)
→ CSV placeholder sample plan
→ future CSV placeholder sample artifact
```

## 2. Non-Activation Statement

This sample format decision does **not**:

- create a CSV, JSON, YAML, or database sample artifact
- create a parser, importer, loader, or runtime validator
- create a live registry consumed by app code
- create a database, SQLite file, Postgres schema, or Supabase schema
- create a schema implementation
- scan curriculum files or index folders
- resolve placeholder URIs
- call APIs or use OAuth
- activate Google Drive, Canvas, NAS, or iCloud integrations
- generate lesson briefs, lesson drafts, or review notes
- use AI parsing, OCR, embeddings, or summaries
- use student data
- add network calls, background jobs, automation, or new package dependencies

Chief of Staff remains a read-only proof/status/reference surface. This PR decides documentation format policy only.

## 3. Current Sample Format

The canonical sample proof is **Markdown documentation only**:

```text
docs/curriculum-builder-manual-registry-sample-proof.md
```

This file contains seven fictional placeholder rows in a Markdown table. PR #138 added repo-local static text checks in `scripts/curriculum-builder-foundation-status.sh` and documents them in `docs/curriculum-builder-static-sample-validation-checks.md`.

No CSV, JSON, YAML, or database sample file exists in the repo for Curriculum Builder manual registry proof at this stage.

## 4. Decision Summary

**Decision: keep the canonical sample proof Markdown-only for now.**

**Future secondary format candidate:** CSV placeholder sample, but only after a separate approved PR documents CSV-specific safety rules and proves it remains static, fictional, and not consumed by app code.

No secondary format artifact is created in this PR.

## 5. Options Considered

| Format | Benefit | Risk | Current decision | Required future guardrails |
| --- | --- | --- | --- | --- |
| **Markdown** | Easiest to review in PRs; safest for docs/status-first planning; existing static checks already validate the artifact | Table edits are manual; less machine-readable appearance | **Selected — canonical format for now** | Maintain non-activation language; keep fictional rows; extend static grep checks only |
| **CSV** | Familiar tabular export shape; may help future validator planning on paper | Looks machine-ingested; invites parser/importer expectations; easier to mistake for loadable data | Deferred — future candidate only | Separate approved plan; fictional rows only; placeholder URIs only; stronger non-activation docs; static checks only; no runtime loader |
| **JSON** | Structured field mapping; common for schema examples | Strongly implies parser/schema enforcement; higher risk of app-loader assumptions | Not selected now | Same as CSV plus explicit no-runtime-consumption guards before any artifact |
| **YAML** | Human-readable structured config style | Similar parser/loader risk as JSON; config-file semantics | Not selected now | Same as CSV plus explicit no-runtime-consumption guards before any artifact |
| **SQLite/database** | Would model real registry storage | Implies implementation far too early; violates local-first metadata-only pause | **Blocked for now** | Requires separate approved scope; not allowed at this planning stage |

## 6. Markdown-Only Option

Markdown remains the canonical sample format because:

- it is easiest to review in pull requests and maintainer handoffs
- it is safest for documentation/status-first planning
- it avoids creating the appearance of a machine-ingested registry
- it avoids prematurely introducing parsers, importers, schema enforcement, or data-loading expectations
- existing static checks already validate the Markdown sample proof (`docs/curriculum-builder-static-sample-validation-checks.md`)
- the seven-row fictional table is sufficient for schema-shape proof at this stage

## 7. CSV Placeholder Option

A future CSV placeholder sample could mirror the seven Markdown rows for validator **planning** only. It is **not** introduced in this PR.

CSV is the preferred future secondary format candidate because:

- it matches tabular registry thinking without JSON/YAML parser semantics
- prior planning (`docs/curriculum-builder-manual-registry-sample-proof-plan.md`) already listed CSV as a future example path
- it can remain a separate static file with explicit non-activation boundaries

CSV must not be added without an approved format-specific plan PR first.

## 8. JSON Placeholder Option

JSON is deferred. Structured JSON samples strongly suggest schema files, parsers, and loaders even when labeled fictional. JSON may be reconsidered only after Markdown and any approved CSV planning path are stable, and only with stronger non-activation language than Markdown requires.

## 9. YAML Placeholder Option

YAML is deferred for the same reasons as JSON. Config-style formats increase the risk that maintainers or future automation will treat the artifact as loadable configuration.

## 10. Recommended Path

1. **Now:** keep `docs/curriculum-builder-manual-registry-sample-proof.md` as the only canonical sample artifact.
2. **Maintain:** extend static validation through documentation/status PRs only.
3. **Next approved PR:** CSV placeholder sample plan (`docs/curriculum-builder-csv-placeholder-sample-plan.md`) without creating the CSV file (completed in PR #140).
4. **Later:** only after CSV plan approval, a separate PR may add a static fictional CSV artifact plus matching static checks — still no parser, importer, loader, or app consumption.

## 11. Why Not Add Another Format Yet

- PR #138 just completed the first substantial static validation layer on Markdown; adding a second format now would split proof surfaces prematurely.
- CSV/JSON/YAML artifacts look more machine-readable and therefore need stronger non-activation language and separate safety planning.
- No approved CSV-specific safety plan exists yet.
- Introducing another format before decision documentation would blur the boundary between planning proof and implementation-ready data.
- The approval gate (`docs/curriculum-builder-approval-gate.md`) still blocks registry implementation behavior.

## 12. Criteria for Adding a Future Secondary Format

Any future secondary sample format must meet **all** of these criteria:

- fictional placeholder rows only
- same seven sample concepts or a documented safe subset aligned with the Markdown sample
- placeholder URI schemes only (`gdrive://placeholder/...`, `nas://placeholder/...`, `local://placeholder/...`, `icloud://placeholder/...`)
- no real Drive URLs
- no real Canvas URLs
- no real NAS paths
- no real iCloud paths
- no local absolute home-directory paths
- no student data
- no copyrighted excerpts
- no generated lesson content
- no generated review notes
- not imported by app code
- not parsed by a runtime loader
- not treated as a live registry
- validated only by repo-local static checks
- no dependencies added
- no network calls
- no OAuth
- no APIs
- no scanning, indexing, OCR, embeddings, or generation

## 13. Required Safety Rules for Any Future Secondary Format

Future CSV, JSON, or YAML sample artifacts must:

- live under `docs/` or another explicitly approved documentation path — never app runtime paths
- use the `sample-` registry ID prefix and Placeholder titling conventions from the Markdown sample
- include a Non-Activation Statement in the artifact or its companion plan doc
- be accompanied by static text checks in `scripts/curriculum-builder-foundation-status.sh` before merge
- prohibit live URL/path patterns using the same negative guards as the Markdown sample
- remain git-tracked documentation only unless explicitly approved otherwise
- never be referenced by app code, CLI loaders, or background jobs without a crossed approval gate

SQLite or other database formats remain blocked until a separate approved implementation scope exists.

## 14. Validation Expectations

For the current Markdown-only decision:

- continue enforcing checks documented in `docs/curriculum-builder-static-sample-validation-checks.md`
- add doc-presence checks for this format decision document
- do not add parser, row-loader, or schema-enforcement checks

For any future secondary format:

- require a format-specific validation plan before the artifact
- require static grep/doc checks only — no runtime validator
- require negative guards for live URLs, real paths, and activation wording
- require cross-links from canonical planning index and maintainer handoff docs

## 15. What This Decision Does Not Do

This decision does **not**:

- create a CSV, JSON, YAML, or database sample file
- change the Markdown sample table rows
- activate registry, parser, importer, loader, or validator behavior
- imply that Chief of Staff owns raw curriculum files
- copy raw curriculum files into the repo or app
- replace the manual registry schema plan or static validation plans

## 16. Blocked Capabilities

Unless explicitly approved through `docs/curriculum-builder-approval-gate.md` and completed decision intake:

- CSV, JSON, YAML, or database sample artifacts without an approved format plan
- live registry behavior consumed by app code
- runtime validator, parser, importer, or loader implementation
- database schema activation
- document scanning, folder scanning, or file indexing
- OCR, embeddings, vector database, AI parsing, or auto-classification
- real lesson generation, generated briefs/drafts, or real review notes
- student data handling
- Google Drive API, Canvas API, iCloud integration, NAS crawler, or local folder crawler
- network calls, OAuth, automation, live integrations, or new runtime services

## 17. Recommended Next PR

**PR #140 — Curriculum Builder CSV Placeholder Sample Plan** (completed). Next: **PR #141 — Curriculum Builder CSV Placeholder Sample Artifact** (create static CSV file + static checks only; no parser/importer/loader).

## 18. PR Handoff Checklist

Before follow-on Curriculum Builder PRs:

- [ ] Start from `docs/curriculum-builder-canonical-planning-index.md`
- [ ] Read sample proof, static validation checks, and this format decision
- [ ] Complete `docs/curriculum-builder-future-pr-checklist.md`
- [ ] Confirm no secondary sample artifact, parser, importer, or loader activation
- [ ] Run `bash scripts/curriculum-builder-foundation-status.sh` — no FAIL
- [ ] Run `bin/chief-of-staff --dashboard` — no FAIL

## Non-Activation confirmation

This sample format decision is documentation and status proof only. It does not add CSV, JSON, YAML, or database artifacts; live registry behavior; parsers; importers; loaders; runtime validators; connectors; APIs; automation; scanning; indexing; OCR; embeddings; lesson generation; student data; network calls; OAuth; or new dependencies.
