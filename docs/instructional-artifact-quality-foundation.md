# Instructional Artifact Quality System Foundation

Last updated: 2026-07-28

Status: **Phase 2 visual geometry** — local-first mechanical validation with rendered-page metrics; teacher visual review required.

## Implemented

- Profiles under `configs/artifact-profiles/`
- Standards under `standards/instructional-artifacts/`
- Validators: PDF (primary), DOCX, HTML, PPTX
- Student/teacher key comparison (structural + optional visual diff)
- **Rendered-page geometry metrics** (`scripts/artifact_quality/visual_geometry.py`)
- **Visible-ink analysis** at configurable DPI
- **Contact sheets** and **annotated page previews**
- **Visual student/key comparison** (diff + overlay images)
- Subject extensions: math, shurley, reading, history, science
- CLI: `python3 scripts/artifact_quality/run_preflight.py`
- Status: `bin/chief-of-staff --artifact-quality-status`

## Heuristic / WARN-only

- Text coverage (not total utilization)
- Drawing coverage (vector structure)
- Estimated structured writing space
- Bottom whitespace from rendered occupancy
- Page balance (top-heavy, sparse, dense, title-only)
- Visual student/key differences
- Preliminary visual heuristic score
- Font embedding confirmation
- HTML/PPTX/DOCX final pagination without PDF export

## Manual / instructional review required

- Attractiveness and instructional importance
- Grade 4 cognitive appropriateness
- Semantic and diagram correctness
- Sufficient writing space for an individual class
- Pedagogy and semantic correctness
- Grayscale and projector readability
- Shurley alignment quality beyond single-line heuristic

## Future enhancements

- Optional local HTML-to-PDF conversion path when approved browser tooling exists
- Richer math layout analysis
- Ricoh / print-shop specific profiles

## Non-activation

This track validates local files only. No Canvas, Drive, network APIs, student data, or automatic classroom distribution.

Operator guide: `docs/instructional-artifact-quality-operator-guide.md`
