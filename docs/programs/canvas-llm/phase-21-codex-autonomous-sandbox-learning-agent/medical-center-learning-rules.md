# Medical Center Learning Rules

## PASS

- Read-only inventory of approved sandbox/reference courses.
- Sanitized summaries that remove URLs, emails, names, and token-like strings.
- Local learning outputs under `.local/canvas-llm/sandbox-learning-runs/phase-21/`.
- Experiment writes that target only course `24399` and use `--allow-writes`.

## WARN

- Missing inventory findings.
- Missing QxWy candidates.
- Cleanup needs manual review.
- A temporary artifact exists but cleanup has not been confirmed.

## FAIL

- Required docs or scripts are missing.
- The agent cannot prove write locking to course `24399`.
- The status command cannot prove required modes.
- The sanitizer is missing token, URL, or email removal.

## BLOCKED

- Target course for write is not `24399`.
- Experiment mode is requested but `--allow-writes` is missing.
- A request would touch reference courses `21944`, `21957`, or `21919` with a non-GET method.
- A request would touch grades, people, users, enrollments, settings, submissions, gradebook, analytics, or student data.
- A request would commit raw `.local` outputs.
- A token would be printed.
- A school Canvas URL would be committed.
- A deletion target is not recognized as a temporary Phase 21 test artifact.
