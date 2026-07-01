# Curriculum Builder Markdown/CSV Alignment Proof

Last verified: 2026-06-30

## 1. Purpose

This document describes **static grep-based alignment proof** between the canonical Markdown manual registry sample proof and the secondary CSV placeholder sample artifact.

The alignment proof confirms that both artifacts continue to represent the same fictional placeholder row concepts using repo-local text checks only. It does not parse CSV, validate rows semantically, or load data into any runtime system.

Planning path:

```text
canonical planning index
→ manual registry sample proof
→ CSV placeholder sample artifact
→ CSV static validation maintenance
→ Markdown/CSV alignment proof (this document)
```

## 2. Non-Activation Statement

This alignment proof does **not**:

- create a parser, importer, loader, or runtime validator
- create a live registry, database, or schema implementation
- parse CSV or Markdown tables into structured data
- semantically validate row equality beyond static string presence
- load sample data into app code
- activate Curriculum Builder behavior
- scan curriculum files or index folders
- resolve placeholder URIs
- call APIs or use OAuth
- generate lessons, briefs, drafts, or review notes
- use student data
- add network calls, dependencies, or automation

Chief of Staff remains a read-only proof/status/reference surface.

## 3. Canonical Markdown Artifact

The **canonical** sample proof:

```text
docs/curriculum-builder-manual-registry-sample-proof.md
```

Markdown is the source of truth for planning handoffs, schema-shape review, and maintainer routing. Alignment checks read this file as static text only.

## 4. Secondary CSV Artifact

The **secondary** static placeholder sample:

```text
docs/examples/curriculum-builder-manual-registry-sample.csv
```

CSV mirrors the seven fictional Markdown rows for tabular documentation proof only. CSV must not be consumed by app code.

## 5. Maintenance Reference

Alignment expectations and edit checklist:

```text
docs/curriculum-builder-csv-static-validation-maintenance.md
```

Future sample edits should follow the maintenance doc before updating static checks.

## 6. Static Alignment Proof Method

Alignment is enforced by `scripts/curriculum-builder-foundation-status.sh` using:

- exact file presence checks
- exact string presence checks (`grep -F`) on each artifact independently
- no CSV parser, row loader, or cross-file runtime diff

If a shared placeholder concept appears in both the Markdown sample and CSV sample, the static check passes. This is a maintenance guardrail only — not semantic row validation.

## 7. Shared Placeholder Concepts

Static checks verify both artifacts contain:

**Seven fictional registry IDs:**

```text
sample-sm5-textbook-001
sample-sm5-worksheet-folder-001
sample-history-slides-001
sample-science-study-guide-001
sample-canvas-export-folder-001
sample-teacher-assessment-001
sample-student-practice-001
```

**Seven placeholder URI references:**

```text
gdrive://placeholder/sm5/textbook
gdrive://placeholder/sm5/worksheet-folder
nas://placeholder/archive/history-slides
nas://placeholder/archive/science-study-guides
local://placeholder/canvas-export
local://placeholder/teacher-only-assessment
icloud://placeholder/student-facing-practice
```

**Safety flag concepts:**

- `placeholder_only` and `no_external_resolution` in both artifacts
- `manual_entry` in Markdown; `manual_static_entry` in CSV (equivalent manual-entry concept, different delimiter naming)

## 8. What This Alignment Proof Proves

This proof demonstrates that:

- both artifacts exist as repo-local static documentation
- shared fictional registry IDs are present in Markdown and CSV
- shared placeholder URI strings are present in Markdown and CSV
- shared safety-flag vocabulary is represented in both artifacts
- Markdown remains canonical and CSV remains secondary

## 9. What This Alignment Proof Does Not Prove

This proof does **not** prove:

- per-field row equality across every column
- CSV parsing correctness or delimiter handling
- curriculum correctness or instructional alignment
- file existence at placeholder locations
- data quality beyond static string presence
- runtime registry, parser, or importer behavior

## 10. Blocked Capabilities

Unless explicitly approved through `docs/curriculum-builder-approval-gate.md`:

- CSV parser, importer, loader, or runtime validator
- live registry or database activation
- app code consumption of CSV or Markdown samples
- document scanning, folder indexing, OCR, embeddings, or AI parsing
- network calls, OAuth, automation, or new runtime services

## 11. PR Handoff Checklist

Before follow-on sample edits:

- [ ] Start from `docs/curriculum-builder-canonical-planning-index.md`
- [ ] Confirm Markdown remains canonical
- [ ] Confirm CSV remains secondary
- [ ] Update both artifacts together when alignment is required
- [ ] Update static checks if shared concepts change
- [ ] Run `bash scripts/curriculum-builder-foundation-status.sh` — no FAIL
- [ ] Run `bin/chief-of-staff --dashboard` — no FAIL

## Non-Activation confirmation

This Markdown/CSV alignment proof is documentation and static grep proof only. It does not activate parsers, importers, loaders, runtime validators, live registry behavior, databases, connectors, APIs, automation, scanning, indexing, OCR, embeddings, lesson generation, student data, network calls, OAuth, or new dependencies.
