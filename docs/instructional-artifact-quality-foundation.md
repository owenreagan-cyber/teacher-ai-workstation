# Instructional Artifact Quality System Foundation

Last updated: 2026-07-28

Status: **Phase 3 educational layout** — mechanical + visual + Grade 4 layout heuristics; teacher approval required.

## Implemented

- Profiles under `configs/artifact-profiles/`
- Standards under `standards/instructional-artifacts/`
- Validators: PDF (primary), DOCX, HTML, PPTX
- Student/teacher key comparison (structural + optional visual diff)
- Rendered-page geometry metrics (`scripts/artifact_quality/visual_geometry.py`)
- **Educational layout intelligence** (`scripts/artifact_quality/educational_layout.py`)
- Visible-ink analysis, contact sheets, annotated previews, visual comparison
- Subject-specific layout heuristics: math, shurley, reading, history, science
- Instructional layout report section with separate educational score
- CLI: `python3 scripts/artifact_quality/run_preflight.py`
- Status: `bin/chief-of-staff --artifact-quality-status`

## Heuristic / WARN-only

- Typography, chunking, cognitive load, direction quality
- Worksheet, guided notes, assessment, slide layout heuristics
- Subject-specific writing-space and diagram readability checks
- Educational layout score (never overrides FAIL)
- Visual geometry metrics (Phase 2)
- Font embedding confirmation

## Manual / instructional review required

- Instructional approval always **Manual Review Required**
- Pedagogy, semantic correctness, attractiveness
- Grade 4 cognitive appropriateness for a specific class
- Sufficient writing space for individual students

## Tooling validation override

If a critical analyzer, comparison, output-sandbox, or source-preservation test fails:

- automated artifact findings become **provisional**
- do **not** mark the automated preflight system as PASS
- do **not** claim geometry QA is fully validated
- continue manual review
- report **tooling confidence** separately from artifact quality

Critical tooling tests include: safe-margin clipping detection, visible-ink classification, vector-only page detection, student/key page-count mismatch detection, output sandbox enforcement, source hash preservation, working-tree preservation, stash preservation.

Grade 4 chapter preflight policy: Explorer Academy `docs/15_Grade_4_Chapter_Artifact_Preflight_Prompt.md` (PHASE 17).

## Future enhancements

- Optional local HTML-to-PDF conversion path when approved browser tooling exists
- Richer math layout analysis
- Ricoh / print-shop specific profiles

## Non-activation

This track validates local files only. No Canvas, Drive, network APIs, student data, or automatic classroom distribution.

Operator guide: `docs/instructional-artifact-quality-operator-guide.md`

Universal classroom-readiness acceptance gate:
`docs/qa/universal-instructional-artifact-qa-standard.md`

The automated Artifact Quality system provides mechanical, visual, and educational-layout evidence. It does not independently authorize the completion language defined by the universal acceptance standard.
