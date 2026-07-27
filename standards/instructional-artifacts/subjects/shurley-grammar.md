# Shurley Grammar Subject Profile

Mechanical checks: guided-notes margins, pagination, student/key comparison, single-line sentence heuristic when enabled.

Manual instructional review required for:

- Sentence remains on one line
- Required word spacing preserved
- Classification lines have sufficient vertical space
- Student and teacher sentences match structurally
- Teacher answers do not cause wrapping
- Vocabulary writing space is generous
- Nonbreaking-space or equivalent alignment support

Use:

```bash
python3 scripts/artifact_quality/run_preflight.py \
  --profile guided-notes-letter \
  --subject shurley \
  --input path/to/notes-student.pdf
```

For keys:

```bash
python3 scripts/artifact_quality/run_preflight.py \
  --profile teacher-key-letter \
  --subject shurley \
  --student path/to/notes-student.pdf \
  --teacher path/to/notes-key.pdf
```
