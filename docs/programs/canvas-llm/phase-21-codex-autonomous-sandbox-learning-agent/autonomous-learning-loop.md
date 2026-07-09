# Autonomous Learning Loop

## Local Outputs

The agent writes all raw and learned outputs under:

```text
.local/canvas-llm/sandbox-learning-runs/phase-21/
```

Required learning files:

- `questions.json`
- `findings.json`
- `next-actions.json`

## Loop

1. Inventory approved courses through allowlisted endpoints.
2. Store raw API output only under `.local`.
3. Write sanitized findings.
4. Ask self-questions from missing knowledge.
5. Mark questions as `answered`, `unanswered`, or `needs_probe`.
6. Recommend the next safe probe.
7. Keep Canvas writes blocked unless experiment mode is explicitly enabled.
8. Distinguish stable rules from hypotheses.
9. Never invent findings that are not supported by inventory data.

## Probe Boundary

The agent never uses unrestricted browsing or arbitrary endpoints. It only uses allowlisted Canvas course structure endpoints and blocks grades, people, users, enrollments, settings, submissions, gradebook, analytics, and student data.
