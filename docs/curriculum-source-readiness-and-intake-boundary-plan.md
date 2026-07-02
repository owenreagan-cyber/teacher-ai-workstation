# Curriculum Source Readiness and Intake Boundary Plan

Last updated: 2026-07-02

```text
Status: planning_only
Closure status: complete_curriculum_source_readiness_plan
Real curriculum ingestion: blocked
Real metadata intake: blocked
Production registry writes: blocked
Active user-facing --write: blocked
Student data: blocked
Implementation: blocked until explicit Owen Reagan approval
```

## Purpose

Prepare the Teacher AI Workstation for **future** Owen-approved curriculum **metadata** intake without pulling, scanning, crawling, parsing, summarizing, copying, embedding, or ingesting real curriculum content.

This plan defines fake/local readiness scope only. It does **not** authorize real intake.

**Proof (read-only):**

```bash
bin/chief-of-staff --curriculum-source-readiness-status
```

---

## Curriculum Metadata vs Curriculum Content

| Category | Examples | This mission |
| --- | --- | --- |
| **Metadata** | grade band, subject label, unit placeholder, source type, review state, fake source ID | Fake fixtures only |
| **Content** | textbook text, worksheet bodies, answer keys, test items, slides, PDFs, excerpts | **Blocked** — never copied or ingested |

Metadata describes *where* or *what kind* of resource might exist in a future approved workflow. It is not the resource itself.

---

## Fake / Local Readiness Scope (Active Today)

| Artifact | Path |
| --- | --- |
| Fake metadata schema | `assistant/curriculum-builder/samples/curriculum-source-readiness/curriculum-source-metadata.schema.json` |
| Fake inventory | `assistant/curriculum-builder/samples/curriculum-source-readiness/fake-curriculum-source-inventory.json` |
| Markdown index | `docs/curriculum-source-readiness-fake-inventory-index.md` |
| Validator | `scripts/curriculum-source-readiness-validate.sh` |
| Status | `scripts/curriculum-source-readiness-status.sh` |

All fixtures use generic fake labels (`fake-source-001`, `grade-4`, `ela`, `sample-unit`). No real curriculum titles, paths, or URLs.

---

## No-Ingest Policy (Non-Negotiable Until Owen Approval)

Blocked without separate explicit mission:

- Reading or copying real curriculum files (PDF, DOCX, slides, worksheets, tests, answer keys)
- Folder scanning, document scanning, crawling, OCR
- Embeddings, vector databases, RAG
- AI generation of lesson/material content from real sources
- Google Drive, Canvas, NAS, iCloud, API, OAuth, or network intake
- Student names, rosters, grades, accommodations, behavior notes, parent emails
- Automatic promotion of fake fixtures to production registry

---

## Source-System Priority (Planning Only)

Future manual-first priority (Owen may revise):

1. **Manual reference** — Owen-entered metadata only
2. **Local folder index** — path metadata only; no file reads without approval
3. **Canvas export metadata** — export manifest only; no Canvas API
4. **Google Drive / NAS / iCloud** — blocked until integration missions approved

See also `docs/curriculum-builder-production-registry-workflow-planning-brief.md` § source-system planning.

---

## Manual-First Future Workflow (Not Active)

```text
1. Owen approves tiny pilot mission
2. Owen authors ONE metadata record manually (or approves fake fixture promotion pattern)
3. Human reviews against schema and boundary plan
4. Run --curriculum-source-readiness-status (must PASS)
5. Run registry lane status aggregate proof
6. No automatic intake, no batch import, no folder scan
```

Cross-link: `docs/curriculum-builder-registry-dry-run-fixture-promotion-planning-spec.md`

---

## Future Owen Approval Gate — Tiny Pilot Checklist

Before any real metadata pilot (not authorized today):

- [ ] Owen completes production registry planning brief § J checklist
- [ ] Owen approves single source-system path (manual vs folder vs export)
- [ ] Owen approves ID namespace for real records
- [ ] Owen confirms no student data in scope
- [ ] Owen confirms no curriculum content copying
- [ ] Owen approves scoped implementation prompt
- [ ] ChatGPT review recommended before implementation prompt

---

## Student Data and Curriculum Content Boundaries

- `student_data_allowed` must remain **false** on all fake fixtures
- `real_curriculum_content_allowed` must remain **false**
- `content_ingestion_allowed` must remain **false**
- Validators reject student-like field names and real-looking paths/URLs

---

## Copyrighted / Test / Answer-Key Prohibition

Fake `source_type` values may include planning placeholders (e.g. `teacher_created_placeholder`). Real answer keys, real test names, and real textbook excerpts are **out of scope** for intake missions unless Owen explicitly approves a bounded exception (not expected).

---

## Explicit Non-Goals

- Real curriculum ingestion, parsing, summarization, indexing
- Production registry writes or active `--write`
- Hidden write paths or automatic fixture promotion
- Integrations (Drive, Canvas, NAS, iCloud, APIs, OAuth)
- Lesson generation, renderers with real content, RAG pipelines
- Scanning Owen's school folders or connected workspace directories

---

## Safest Future First Implementation PR (Planning Only)

When Owen approves a pilot, the first implementation PR should:

1. Add **one** manual metadata entry path with human review gate
2. Reuse existing registry validators; no new network code
3. Prove non-mutation of live registry and fixtures
4. Include negative tests for paths, URLs, student fields
5. Not add `--write` or batch import

---

## Related Documents

| Doc | Role |
| --- | --- |
| `docs/curriculum-builder-registry-authority-map.md` | Registry authority surfaces |
| `docs/curriculum-builder-production-registry-workflow-planning-brief.md` | Production registry planning |
| `docs/curriculum-builder-registry-dry-run-fixture-promotion-planning-spec.md` | Blocked promotion seam |
| `docs/curriculum-source-readiness-fake-inventory-index.md` | Fake inventory index |

## Non-Activation

This plan does not activate intake, scanning, generation, APIs, or production writes.
