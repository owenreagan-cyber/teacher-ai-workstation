# Canvas LLM Phase 21 — Codex Autonomous Sandbox Learning Agent

## Status

Implementation framework, local runner, doctrine, and status proof.

Phase 21 builds a safe Canvas learning agent that can run from Codex or a local terminal. Its default behavior is read-only inventory. Canvas writes remain blocked unless the operator intentionally runs experiment or cleanup mode with `--allow-writes`, `CANVAS_BASE_URL`, and `CANVAS_TOKEN`.

## Scope

- Inspect sandbox course `24399`.
- Inspect reference courses `21944`, `21957`, and `21919` read-only.
- Learn tabs, pages, assignments, announcements, files, modules, module items, page slugs, front-page hints, QxWy candidates, and safe HTML shell hints.
- Write local learning outputs under `.local/canvas-llm/sandbox-learning-runs/phase-21/`.
- Generate `questions.json`, `findings.json`, and `next-actions.json`.
- Log temporary sandbox artifacts in an artifact ledger.
- Sanitize summaries before printing or writing committed examples.

## Commands

```bash
scripts/canvas-llm/canvas_learning_agent.py --mode inventory
scripts/canvas-llm/canvas_learning_agent.py --mode questions
scripts/canvas-llm/canvas_learning_agent.py --mode existing-page-dry-run
scripts/canvas-llm/canvas_learning_agent.py --mode experiment --allow-writes
scripts/canvas-llm/canvas_learning_agent.py --mode cleanup --allow-writes
```

## Environment

The runner requires:

- `CANVAS_BASE_URL`
- `CANVAS_TOKEN`

The token must never be printed, committed, logged, or copied into docs.

## Phase Decision

```text
AUTONOMOUS_SANDBOX_LEARNING_FRAMEWORK_READY_WITH_WRITES_LOCKED
```
