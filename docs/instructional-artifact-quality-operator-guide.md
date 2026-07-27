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

## Examples

### Math worksheet

```bash
python3 scripts/artifact_quality/run_preflight.py \
  --profile worksheet-letter \
  --subject math \
  --input dist/chapter-2-worksheet-student.pdf
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

### Student / teacher key comparison

```bash
python3 scripts/artifact_quality/run_preflight.py \
  --profile teacher-key-letter \
  --subject shurley \
  --student dist/chapter-2-notes-student.pdf \
  --teacher dist/chapter-2-notes-key.pdf \
  --json --render
```

## Flags

| Flag | Purpose |
| --- | --- |
| `--json` | Write `report.json` under output directory |
| `--output-dir PATH` | Override `.local/artifact-quality/<name>/` |
| `--render` | Render PDF pages to PNG previews |
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
```

`.local/` is gitignored. Do not commit rendered output.

## Validation layers

1. **Mechanical** — automated PASS/WARN/FAIL from profiles.
2. **Visual** — teacher review of renders and flagged pages.
3. **Instructional** — teacher judgment for pedagogy and classroom fit.

## DOCX / HTML / PPTX

Structural checks run on source files. Authoritative pagination proof still requires PDF export + PDF preflight.
