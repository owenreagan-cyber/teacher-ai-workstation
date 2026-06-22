# Interactive Chief of Staff CLI

Phase 1B is the first runnable Teacher AI Chief of Staff interface.

The CLI assembles approved Markdown context, one selected workflow, optional approved writing samples, explicit user-provided context files, and a user question into a single prompt. It can send that prompt to the `llm` CLI when available.

## What it does

- Runs in the terminal.
- Uses approved Markdown context from this repo.
- Uses one selected workflow at a time.
- Includes only explicit `--context` files passed by the user.
- Supports dry-run mode so Owen can inspect exactly what would be sent.
- Supports status and context debugging.

## What it does not do

- It does not scan Drive, Gmail, Apple Mail, or local folders.
- It does not recursively read directories.
- It does not auto-load raw or rejected writing samples.
- It does not auto-load raw intake, rejected intake, quarantine intake, or approved file folders.
- It does not send email, publish Canvas content, modify files, delete files, or run background jobs.
- It does not hardcode a model.

## Why interactive first

The Chief of Staff must become teachable before becoming powerful. This CLI proves the core loop safely before any UI, connector, database, or automation exists.

## Repo root resolution

The CLI finds the repo root in this order:

1. `CHIEF_OF_STAFF_REPO`
2. `git rev-parse --show-toplevel`
3. Parent directory of the script location, if it looks like this repo

If needed:

```bash
export CHIEF_OF_STAFF_REPO="/path/to/teacher-ai-workstation"
```

## Basic commands

```bash
bin/chief-of-staff --status
```

```bash
bin/chief-of-staff --version
```

```bash
bin/chief-of-staff --list-workflows
```

```bash
bin/chief-of-staff --show-context --workflow request-training-materials
```

## Ask a question

```bash
bin/chief-of-staff \
  --workflow request-training-materials \
  --question "What files or writing samples would help you become more useful?"
```

## Pass a context file

```bash
bin/chief-of-staff \
  --workflow project-review \
  --context assistant/training/feedback-log.md \
  --question "What should I work on next?"
```

## Dry-run mode

Dry-run prints the full assembled prompt and does not call a model.

```bash
bin/chief-of-staff \
  --workflow project-review \
  --context examples/sample-project-note.md \
  --question "What is the next action?" \
  --dry-run
```

## Manual copy/paste mode

Use `--no-model` if `llm` is unavailable or if you want to paste the prompt into ChatGPT, Claude, or another model.

```bash
bin/chief-of-staff \
  --workflow project-review \
  --context examples/sample-project-note.md \
  --question "What is the next action?" \
  --no-model > chief-of-staff-prompt.txt
```

## Approved writing samples

Approved writing samples are included only when explicitly requested:

```bash
bin/chief-of-staff \
  --workflow email-style-support \
  --include-approved-writing-samples \
  --question "Draft a warm parent email using only approved style guidance."
```

`raw-inbox.md` and `rejected-samples.md` are refused even if passed with `--context`.

## Memory

Phase 1C adds approved Markdown memory files in `assistant/memory/`.

Memory is Markdown because it is inspectable, manually editable, and easy to review before use. Memory is explicit because the Chief of Staff should not silently personalize itself from private files.

Memory is not included by default. Use `--show-context` to confirm what will be included and `--dry-run` before real model calls.

Memory cannot override safety, permission, sensitivity, source-verification, or current user instructions. If `writing-style-rules.md` is explicitly included, it takes precedence over `assistant/writing-style.md` only for style decisions.

`memory-review-checklist.md` and `memory-log.md` are not auto-included by memory flags. They can only be included by passing them explicitly with `--context`.

Use `--memory-status` to check freshness and `--validate-memory` for a quick warning scan. `--validate-memory` is not a security guarantee.

### Memory flags

- `--include-memory`: include all approved memory files.
- `--include-project-memory`: include `assistant/memory/projects.md`.
- `--include-writing-style-memory`: include `assistant/memory/writing-style-rules.md`.
- `--include-teaching-context-memory`: include `assistant/memory/teaching-context.md`.
- `--include-preferences-memory`: include `assistant/memory/preferences.md`.
- `--include-decisions-memory`: include `assistant/memory/decisions.md`.
- `--include-active-priorities-memory`: include `assistant/memory/active-priorities.md`.

### Memory examples

```bash
bin/chief-of-staff \
  --workflow project-review \
  --include-memory \
  --question "What should I work on next?"
```

```bash
bin/chief-of-staff \
  --workflow email-style-support \
  --include-writing-style-memory \
  --question "Draft a short parent email reminder."
```

```bash
bin/chief-of-staff \
  --workflow lesson-support \
  --include-teaching-context-memory \
  --context examples/sample-lesson-notes.md \
  --question "Turn this into a 4th grade lesson plan idea."
```

```bash
bin/chief-of-staff --memory-status
```

```bash
bin/chief-of-staff --validate-memory
```

When `--show-context` lists memory older than 30 days, it marks it with `[STALE?]`.

## Intake Review Queue

Phase 1D adds `assistant/intake/`, a Markdown review queue for candidate context. It exists before local indexing, Drive, Gmail, or Canvas connectors so material can be reviewed by Owen before it becomes approved context.

Intake is not automatic memory. Raw intake is not approved context. Approved summaries are safer than raw pasted data because they can remove sensitive details, preserve only the useful learning, and cite the intake item that was reviewed.

### Intake areas

- `assistant/intake/raw/`: unreviewed holding area; ignored by Git except `.gitkeep`; refused with `--context`.
- `assistant/intake/approved-context.md`: safe Markdown summaries that can be included with `--include-approved-intake`.
- `assistant/intake/approved-files/`: reviewed files such as PDFs or exports; ignored by Git except `.gitkeep`; not read automatically.
- `assistant/intake/rejected-context.md`: minimal rejected-item index; not approved context.
- `assistant/intake/quarantine.md`: review-needed index for sensitive, unclear, private, copyrighted, or risky material.
- `assistant/intake/quarantine-files/`: file holding area for quarantined artifacts; ignored by Git except `.gitkeep`; refused with `--context`.
- `assistant/intake/intake-log.md`: review activity log; not auto-included.

`approved-context.md` is for sanitized Markdown summaries. `approved-files/` is for actual reviewed artifacts and is not automatically read by the CLI. Raw intake folders are refused with `--context` because they may contain copied files, private data, or material that has not passed review.

### Intake flags

- `--include-approved-intake`: include `assistant/intake/approved-context.md`.
- `--include-intake-policy`: include `assistant/intake/intake-policy.md`.
- `--include-intake-queue`: include `assistant/intake/review-queue.md`.
- `--include-intake-checklist`: include `assistant/intake/intake-review-checklist.md`.
- `--intake-status`: show intake file status.
- `--intake-summary`: show queue counts and validation status.
- `--intake-diff`: show uncommitted changes in `assistant/intake/` and `.gitignore`.
- `--next-intake-id`: print the next `ITEM-####` ID.
- `--validate-intake`: scan approved intake Markdown files for obvious warning patterns.
- `--force-sensitive-context`: allow `rejected-context.md` or `quarantine.md` as review-only context.

`--force-large-context` is only for file-size overrides. `--force-sensitive-context` is only for explicitly reviewing non-approved intake files. It does not turn rejected or quarantined material into approved context.

### Intake examples

```bash
bin/chief-of-staff --intake-status
```

```bash
bin/chief-of-staff --intake-summary
```

```bash
bin/chief-of-staff --intake-diff
```

```bash
bin/chief-of-staff --next-intake-id
```

```bash
bin/chief-of-staff --validate-intake
```

```bash
bin/chief-of-staff \
  --workflow intake-review \
  --include-intake-policy \
  --include-intake-queue \
  --include-intake-checklist \
  --question "Review the pending intake queue and suggest next actions." \
  --dry-run
```

```bash
bin/chief-of-staff \
  --workflow project-review \
  --include-approved-intake \
  --question "What approved intake context affects current priorities?" \
  --dry-run
```

## Large file handling

Files larger than 200 KB are refused by default. Choose a smaller file or intentionally rerun with:

```bash
bin/chief-of-staff \
  --workflow project-review \
  --context path/to/large-file.md \
  --question "Summarize this." \
  --force-large-context
```

Large files included with `--force-large-context` are listed in the prompt warnings.

## Teaching example

```bash
bin/chief-of-staff \
  --workflow lesson-support \
  --context examples/sample-lesson-notes.md \
  --question "Turn this into a 4th grade lesson idea."
```

## Troubleshooting example

```bash
bin/chief-of-staff \
  --workflow troubleshooting-support \
  --question "Help me diagnose this error message: paste error here."
```

## 3D coordination example

```bash
bin/chief-of-staff \
  --workflow 3d-printing-coordination \
  --question "I have an idea for a classroom fidget. What information should I collect before sending it to the future 3D agent?"
```
