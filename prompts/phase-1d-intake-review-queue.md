# Phase 1D Intake Review Queue Prompt

You are continuing work in `https://github.com/owenreagan-cyber/teacher-ai-workstation.git`.

Task: add the Phase 1D Chief of Staff intake review queue.

Create a Markdown intake structure under `assistant/intake/`:

- `README.md`
- `intake-policy.md`
- `review-queue.md`
- `approved-context.md`
- `rejected-context.md`
- `quarantine.md`
- `intake-log.md`
- `intake-review-checklist.md`
- `templates/intake-item-template.md`
- `templates/review-decision-template.md`
- `templates/sanitized-summary-template.md`
- `examples/README.md`
- `examples/sample-intake-item.md`
- `examples/sample-review-decision.md`
- `raw/.gitkeep`
- `quarantine-files/.gitkeep`
- `approved-files/.gitkeep`

Add `.gitignore` protection:

```gitignore
assistant/intake/raw/*
!assistant/intake/raw/.gitkeep

assistant/intake/quarantine-files/*
!assistant/intake/quarantine-files/.gitkeep

assistant/intake/approved-files/*
!assistant/intake/approved-files/.gitkeep
```

Rules:

- No automatic intake loading.
- Raw intake is not approved context.
- `approved-context.md` stores safe Markdown summaries.
- `approved-files/` stores actual reviewed files and is not auto-loaded.
- `rejected-context.md` and `quarantine.md` are not approved context.
- Raw, quarantine-file, and approved-file folders are refused with `--context`.
- `rejected-context.md` and `quarantine.md` require `--force-sensitive-context` when explicitly used as review-only context.

Add CLI flags:

- `--include-approved-intake`
- `--include-intake-policy`
- `--include-intake-queue`
- `--include-intake-checklist`
- `--intake-status`
- `--intake-summary`
- `--intake-diff`
- `--next-intake-id`
- `--validate-intake`
- `--force-sensitive-context`

Update prompt assembly so approved intake, policy, queue, and checklist appear only when explicitly requested. Add sensitive-context warnings for review-only files.

Update smoke tests for intake flags, raw intake refusal, review-only force behavior, source header format, and validation. Do not call a real model.

Update docs, roadmap, setup verification, setup report, Day 1 manual steps, recovery guide, and assistant training docs. Phase 1D should come before selected folder indexing, Drive, Gmail, Canvas, and the final MacBook opening checkpoint. Phase 0D remains the final installer audit before opening the MacBook unless Owen chooses earlier.
