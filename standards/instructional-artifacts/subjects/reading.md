# Reading Subject Profile

Automated educational heuristics (Phase 3, WARN-only):

- Visually crowded passage lines
- Questions embedded in dense passage text
- Large paragraph blocks without chunking

Manual instructional review required for:

- Passage and questions visually distinct
- Reading text size meets profile
- Line numbers when required
- Questions remain with response areas
- Fluency or word-attack columns remain aligned
- No passage truncation

Use:

```bash
python3 scripts/artifact_quality/run_preflight.py \
  --profile quiz-letter \
  --subject reading \
  --input path/to/reading-check.pdf
```
