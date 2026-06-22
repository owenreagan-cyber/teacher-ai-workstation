# Phase 1B Interactive Chief of Staff CLI Prompt

Use this prompt to recreate or review the Phase 1B terminal Chief of Staff runner.

## Task

Create a safe, local-first, terminal-based Chief of Staff CLI that assembles approved Markdown context and explicit user-provided files, then sends the prompt to the `llm` CLI when available.

Do not build React, local APIs, Google Drive/Gmail/Canvas connectors, autonomous agents, MCP servers, desktop-control agents, the full 3D agent, Docker, databases, vector stores, or background jobs.

## Required flags

- `--workflow <name>`
- `--question <text>`
- `--context <path>` repeatable
- `--include-approved-writing-samples`
- `--model <model-name>`
- `--dry-run`
- `--list-workflows`
- `--show-context`
- `--no-model`
- `--force-large-context`
- `--status`
- `--version`

## Repo root resolution

Resolve the repo root in this order:

1. `CHIEF_OF_STAFF_REPO`
2. `git rev-parse --show-toplevel`
3. Parent directory of the script location if it contains expected repo files

Do not silently use the wrong directory.

## Prompt assembly order

1. Operating Rules
2. Included Files
3. Large Context Warnings, if any
4. Base Context docs in this exact sequence:
   - `assistant/chief-of-staff.md`
   - `assistant/permissions.md`
   - `assistant/failure-recovery-policy.md`
   - `assistant/sensitivity-rules.md`
   - `assistant/model-routing.md`
   - `assistant/writing-style.md`
5. Selected Workflow
6. Approved Writing Samples, only if explicitly requested
7. User Context files, in the exact order provided with `--context`
8. User Question, last
9. Required Response Footer

## Source header format

Use this exact source header format for every included file:

```markdown
---
SOURCE: relative/path/to/file.md
---
```

## Safety rules

- `--show-context` always prints the final file list and exits.
- `--dry-run` prints the assembled prompt and does not call a model.
- `--no-model` prints manual copy/paste instructions and the prompt.
- Do not auto-load `assistant/training/writing-samples/raw-inbox.md`.
- Do not auto-load `assistant/training/writing-samples/rejected-samples.md`.
- If either forbidden sample file is passed with `--context`, refuse it.
- Context directories must not be recursively read.
- Missing context paths must produce clear errors.
- Files larger than 200 KB must be refused unless `--force-large-context` is used.
- Large files included intentionally must appear in Large Context Warnings.
- Do not hardcode a model name.

## Status and version

`--version` prints:

```text
chief-of-staff CLI phase-1b
```

`--status` prints the version, resolved repo root, required doc presence, workflow directory status, `llm` availability, approved samples presence, and raw/rejected sample exclusion status.

## Smoke tests

Create `tests/smoke-chief-of-staff-cli.sh` that runs help, version, status, list workflows, show context, dry-run, no-model, and negative refusal tests for raw-inbox and rejected-samples.
