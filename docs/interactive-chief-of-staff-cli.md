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
