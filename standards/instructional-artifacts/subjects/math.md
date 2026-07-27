# Math Subject Profile

Mechanical checks: Letter PDF, safe margins, placeholders, utilization heuristics.

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
