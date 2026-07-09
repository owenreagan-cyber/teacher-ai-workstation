# Sandbox Experiment Contract

## Required Invocation

```bash
scripts/canvas-llm/canvas_learning_agent.py --mode experiment --allow-writes
```

The operator must provide `CANVAS_BASE_URL` and `CANVAS_TOKEN` in the environment.

## Allowed Temporary Artifacts

- Temporary sandbox page
- Temporary sandbox assignment
- Temporary sandbox announcement
- Temporary sandbox module
- Tiny generated text file if implemented safely

## Artifact Ledger

Every artifact must be recorded in:

```text
.local/canvas-llm/sandbox-learning-runs/phase-21/artifact-ledger.json
```

The ledger must include course ID, artifact type, title, ID or slug, creation timestamp, and cleanup status.

## Announcements

Sandbox announcements must be temporary, clearly labeled, and deleted during cleanup.

Do not send student-facing notifications. Do not publish announcements unless a later explicit approval names that exact behavior.

## Cleanup

Cleanup is attempted for temporary artifacts. Cleanup failures are `WARN` or `BLOCKED`, never silent success.

The cleanup mode must not delete any object unless it is recognized as a Phase 21 temporary test artifact.
