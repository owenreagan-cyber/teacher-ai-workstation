# Phase 1C Project Memory + Writing Style Memory Prompt

Use this prompt to recreate or review the Phase 1C memory layer.

## Task

Add simple, inspectable Markdown memory files for the Teacher AI Chief of Staff and update the CLI so Owen can explicitly include approved memory context.

This is not a database, vector index, embedding system, connector, or automatic ingestion layer.

## Required memory files

- `assistant/memory/README.md`
- `assistant/memory/projects.md`
- `assistant/memory/teaching-context.md`
- `assistant/memory/writing-style-rules.md`
- `assistant/memory/preferences.md`
- `assistant/memory/decisions.md`
- `assistant/memory/active-priorities.md`
- `assistant/memory/memory-review-checklist.md`
- `assistant/memory/memory-log.md`

## CLI memory flags

- `--include-memory`
- `--include-project-memory`
- `--include-writing-style-memory`
- `--include-teaching-context-memory`
- `--include-preferences-memory`
- `--include-decisions-memory`
- `--include-active-priorities-memory`
- `--memory-status`
- `--validate-memory`

Memory must not be loaded automatically. Memory must be included only through explicit flags.

## Approved memory order

1. `assistant/memory/projects.md`
2. `assistant/memory/teaching-context.md`
3. `assistant/memory/writing-style-rules.md`
4. `assistant/memory/preferences.md`
5. `assistant/memory/decisions.md`
6. `assistant/memory/active-priorities.md`

Do not auto-include:

- `assistant/memory/memory-review-checklist.md`
- `assistant/memory/memory-log.md`

Those files can only be included through explicit `--context`.

## Source header normalization

Every included source should use:

```markdown
---
SOURCE: relative/path/to/file.md
---
```

Do not emit heading-style `## SOURCE:` markers.

## Memory behavior

- Memory is Markdown-only.
- Memory is inspectable and manually editable.
- Memory is helpful context, not unquestionable truth.
- Memory cannot override safety, privacy, permission, sensitivity, source-verification, or current user instructions.
- Newer user instructions beat older memory.
- `--show-context` should list memory files in final prompt order.
- `--show-context` should mark memory files older than 30 days with `[STALE?]`.
- `--memory-status` should show file existence, size, modified date, stale marker, and one-line purpose.
- `--validate-memory` should scan memory files only for obvious warning patterns. It is not a security guarantee.

## Writing style precedence

When `writing-style-rules.md` is explicitly included with `--include-writing-style-memory` or `--include-memory`, it takes precedence over `assistant/writing-style.md` only for style decisions.

It cannot override safety, permission, sensitivity, source-verification, or current user instructions.

## Writing style confidence

- Confidence starts at Low.
- Owen must manually update confidence after reviewing real outputs.
- The CLI cannot promote confidence automatically.
- Each confidence change should be recorded in `assistant/memory/memory-log.md`.

## Roadmap placement

- Phase 1A: complete safety/training docs.
- Phase 1B: complete interactive CLI.
- Phase 1C: explicit Markdown memory.
- Phase 1D: intake review queue.
- Phase 0D: final installer audit.
- Open the new MacBook Pro M5 Pro after Phase 1D and Phase 0D unless Owen intentionally chooses earlier.

## Smoke tests

Add tests for:

- Source header canonical format.
- `--include-memory` dry-run succeeds.
- Targeted memory flags succeed.
- Normal dry-run does not include memory.
- `--include-memory` includes `projects.md`.
- `--include-memory` does not include `memory-review-checklist.md`.
- `--include-memory` does not include `memory-log.md`.
- `--memory-status` exits zero.
- `--validate-memory` exits zero with starter files.
- Raw/rejected writing sample refusal still works.
