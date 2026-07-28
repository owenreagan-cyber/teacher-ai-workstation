# Math Subject Profile

Mechanical checks: Letter PDF, safe margins, placeholders, utilization heuristics.

Automated educational heuristics (Phase 3, WARN-only):

- Crowded math expressions per page
- Insufficient computation workspace (writing-space estimate)
- Profile thresholds in `educational_layout` blocks — tune for false positives

Manual instructional review required for:

- Computation space adequacy
- Vertical problem alignment
- Mathematical symbol rendering
- Fraction and exponent readability
- Problem/workspace grouping
- Number-line and model size

Use:

```bash
python3 scripts/artifact_quality/run_preflight.py \
  --profile worksheet-letter \
  --subject math \
  --input path/to/worksheet.pdf
```
