# Instructional Artifact Quality System Foundation

Last updated: 2026-07-27

Status: **implemented foundation** — local-first mechanical validation with teacher visual review required.

## Implemented

- Profiles under `configs/artifact-profiles/`
- Standards under `standards/instructional-artifacts/`
- Validators: PDF (primary), DOCX, HTML, PPTX
- Student/teacher key comparison
- Page utilization heuristics and PNG rendering
- Subject extensions: math, shurley, reading, history, science
- CLI: `python3 scripts/artifact_quality/run_preflight.py`
- Status: `bin/chief-of-staff --artifact-quality-status`

## Heuristic / WARN-only

- Page utilization on diagram-heavy or workspace-heavy pages
- Font embedding confirmation
- HTML/PPTX/DOCX final pagination without PDF export
- One-core-idea slide density
- Student/key structural drift without pixel comparison

## Manual / instructional review required

- Pedagogy and semantic correctness
- Grayscale and projector readability
- Shurley alignment quality beyond single-line heuristic
- Map, diagram, and timeline instructional fit

## Future enhancements

- Optional local HTML-to-PDF conversion path when approved browser tooling exists
- Richer math layout analysis
- Visual diff previews for student/key pairs
- Ricoh / print-shop specific profiles

## Non-activation

This track validates local files only. No Canvas, Drive, network APIs, student data, or automatic classroom distribution.

Operator guide: `docs/instructional-artifact-quality-operator-guide.md`
