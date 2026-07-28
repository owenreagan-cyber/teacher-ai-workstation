# History Subject Profile

Automated educational heuristics (Phase 3, WARN-only):

- Tiny diagram or map labels
- Crowded diagram regions (visible-ink heuristic)

Manual instructional review required for:

- Timelines retain order
- Map labels remain visible
- Legends are readable
- Grayscale usability
- Visuals do not displace essential text

Use:

```bash
python3 scripts/artifact_quality/run_preflight.py \
  --profile worksheet-letter \
  --subject history \
  --input path/to/history-packet.pdf
```
