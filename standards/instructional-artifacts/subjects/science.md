# Science Subject Profile

Automated educational heuristics (Phase 3, WARN-only):

- Tiny diagram labels
- Crowded diagram regions (visible-ink heuristic)

Manual instructional review required for:

- Diagram labels remain visible
- Process arrows remain readable
- Tables stay together
- Symbols render correctly
- Image and label groupings stay together

Use:

```bash
python3 scripts/artifact_quality/run_preflight.py \
  --profile worksheet-letter \
  --subject science \
  --input path/to/science-handout.pdf
```
