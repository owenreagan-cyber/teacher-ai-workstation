# Instructional Artifact Quality Operator Guide

Local-first preflight for printable teacher-created resources.

## Quick start

```bash
python3 scripts/artifact_quality/run_preflight.py --help
bin/chief-of-staff --artifact-quality-status
```

Install optional dependencies if needed:

```bash
pip3 install -r scripts/artifact_quality/requirements.txt
```

## Visual metrics (Phase 2)

Preflight now reports **separate** rendered-page metrics per page:

| Metric | Meaning |
| --- | --- |
| Text coverage | Extracted text block occupancy — **not** total page utilization |
| Drawing coverage | Vector structure (lines, boxes, table geometry) |
| Visible ink | Rendered marks differing from page background |
| Estimated writing space | Heuristic for ruled lines and answer boxes |
| Bottom whitespace | Gap below lowest meaningful occupied row (inches) |
| Page balance | WARN-only layout distribution heuristic |
| Safe margin state | Content vs printable/safe bounds |

**Instructional quality remains manual review.** PASS/WARN/FAIL scores do not authorize classroom distribution without teacher visual review.

## Educational layout (Phase 3)

Preflight adds an **Instructional Layout** section with conservative Grade 4 heuristics:

| Category | Checks |
| --- | --- |
| Typography | Body/direction font sizes, heading consistency, font families |
| Visual Chunking | Headings, dividers, spacing between sections |
| Writing Space | Subject-aware workspace estimates |
| Text Density | Paragraph length, question density, cognitive load |
| Directions | Length, single-block multi-step instructions |
| Grade 4 Readability | Worksheet, guided notes, assessment, subject-specific rules |
| Presentation Visibility | Slide bullets, title prominence, reading load (PPTX) |

Educational heuristics produce **WARN** by default. FAIL is reserved for objectively unreadable text (profile threshold) or existing mechanical rules.

False positives are expected — tune thresholds in profile `educational_layout` blocks.

## Examples

### Math worksheet (standard PDF preflight)

```bash
python3 scripts/artifact_quality/run_preflight.py \
  --profile worksheet-letter \
  --subject math \
  --input dist/chapter-2-worksheet-student.pdf
```

### Annotated rendering

```bash
python3 scripts/artifact_quality/run_preflight.py \
  --profile guided-notes-letter \
  --input dist/chapter-2-notes-student.pdf \
  --render --annotate --json
```

### Contact sheet

```bash
python3 scripts/artifact_quality/run_preflight.py \
  --profile worksheet-letter \
  --input dist/chapter-2-worksheet-student.pdf \
  --render --contact-sheet
```

### Shurley guided notes

```bash
python3 scripts/artifact_quality/run_preflight.py \
  --profile guided-notes-letter \
  --subject shurley \
  --input dist/chapter-2-notes-student.pdf \
  --render
```

### Reading check

```bash
python3 scripts/artifact_quality/run_preflight.py \
  --profile quiz-letter \
  --subject reading \
  --input dist/reading-check.pdf
```

### History packet

```bash
python3 scripts/artifact_quality/run_preflight.py \
  --profile worksheet-letter \
  --subject history \
  --input dist/history-packet.pdf
```

### Science diagram handout

```bash
python3 scripts/artifact_quality/run_preflight.py \
  --profile worksheet-letter \
  --subject science \
  --input dist/science-diagram-handout.pdf \
  --render
```

### Projector presentation

```bash
python3 scripts/artifact_quality/run_preflight.py \
  --profile projector-slides \
  --input dist/unit-intro.pptx
```

### Student / teacher key comparison with visual diff

```bash
python3 scripts/artifact_quality/run_preflight.py \
  --profile teacher-key-letter \
  --subject shurley \
  --student dist/chapter-2-notes-student.pdf \
  --teacher dist/chapter-2-notes-key.pdf \
  --visual-compare --json --render
```

### JSON report with strict warnings

```bash
python3 scripts/artifact_quality/run_preflight.py \
  --profile worksheet-letter \
  --input dist/worksheet.pdf \
  --json --strict
```

## Flags

| Flag | Purpose |
| --- | --- |
| `--json` | Write `report.json` under output directory |
| `--output-dir PATH` | Override `.local/artifact-quality/<name>/` |
| `--render` | Render PDF pages to PNG previews |
| `--annotate` | Annotated previews with boundary/metric overlays |
| `--contact-sheet` | Multi-page contact-sheet PNG |
| `--visual-compare` | Student/teacher diff and overlay images |
| `--analysis-dpi N` | Override profile analysis render DPI |
| `--strict` | Exit code 2 on WARN (FAIL remains exit 1) |

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | PASS, or WARN without `--strict` |
| 1 | FAIL |
| 2 | WARN with `--strict` |

## Output layout

```text
.local/artifact-quality/<artifact-name>/
  report.json
  report.txt
  renders/
    page-001.png
  annotated/
    page-001-annotated.png
  preview-contact-sheet.png
  visual-compare/
    page-001-student.png
    page-001-teacher.png
    page-001-diff.png
    page-001-overlay.png
```

`.local/` is gitignored. Do not commit rendered output.

## Validation layers

1. **Mechanical** — automated PASS/WARN/FAIL from profiles.
2. **Visual heuristic** — rendered geometry metrics, contact sheets, optional diffs.
3. **Instructional** — teacher judgment for pedagogy and classroom fit (always manual).
4. **Final acceptance** — the eight-stage classroom-readiness gate in `docs/qa/universal-instructional-artifact-qa-standard.md`.

Automated preflight PASS is evidence for final acceptance, but it is not by itself permission to call an artifact complete or classroom-ready.

## DOCX / HTML / PPTX

Structural checks run on source files. Authoritative pagination proof still requires PDF export + PDF preflight.

## Quality score

When analysis runs, reports include transparent preliminary scores:

- **Mechanical score** — ratio of passing checks
- **Visual heuristic score** — ink/margin/balance heuristics (Phase 2)
- **Educational layout score** — typography, chunking, density heuristics (Phase 3)
- **Instructional approval** — always `Manual Review Required`

No score overrides FAIL. PDF remains the authoritative print artifact.

## Tooling validation override

When critical tooling tests fail or were not run on the expected branch, treat automated artifact findings as **provisional**. Do not report geometry QA as complete or the preflight system as PASS until tooling confidence is verified separately from artifact quality.

Critical tooling tests: safe-margin clipping detection, visible-ink classification, vector-only page detection, student/key page-count mismatch detection, output sandbox enforcement, source hash preservation, working-tree preservation, stash preservation.

See `docs/instructional-artifact-quality-foundation.md` and Explorer Academy `docs/15_Grade_4_Chapter_Artifact_Preflight_Prompt.md` (PHASE 17).
