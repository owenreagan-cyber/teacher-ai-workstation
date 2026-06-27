# Lesson Activity and Assessment Helper

## Purpose

The Lesson Activity and Assessment Helper is a local-only teacher workflow for creating activity, assessment, and materials checklist draft files from approved local templates.

It supports Owen in starting structured classroom materials for human review. It is not a lesson generator, not an AI automation pipeline, and not connected to Gmail, Drive, Calendar, APIs, or school systems.

## What The Helper Creates

The creation helper writes one Markdown draft under:

```text
assistant/lesson-planning/drafts/
```

Supported draft types:

- `activity`
- `assessment`
- `materials`

Each draft includes metadata, a safety notice, source notes, and the contents of the matching template.

Generated drafts are manual/local outputs and are gitignored except for `assistant/lesson-planning/drafts/README.md`.

## How To Run

Check helper status:

```bash
bash scripts/lesson-draft-status.sh
bin/chief-of-staff --lesson-draft-status
```

Create a local draft:

```bash
bash scripts/create-lesson-draft.sh activity fractions-review
bin/chief-of-staff --create-lesson-draft activity fractions-review
```

Valid types are `activity`, `assessment`, and `materials`.

Review the broader dashboard:

```bash
bin/chief-of-staff --dashboard
```

## Safety Rules

- No real student names.
- No private student data.
- No grades, medical notes, or behavior notes.
- No IEP/504 details.
- No parent contact information.
- No secrets, API keys, tokens, or passwords.
- No external services.
- No sending, sharing, uploading, syncing, or publishing.
- Human review before classroom use.

## What This Does Not Do

- It does not generate finished classroom materials automatically.
- It does not call an LLM by default.
- It does not access school systems.
- It does not send or share anything.
- It does not read private student data.
