# Lesson Brief Helper

## Purpose

The Lesson Brief Helper is a local-only teacher workflow that creates a draft lesson brief file from a safe lesson idea slug and the existing lesson brief template.

It supports Owen in starting a structured lesson brief for human review. It is not a full lesson generator, not an AI automation pipeline, and not connected to Gmail, Drive, Calendar, APIs, or school systems.

## What The Helper Creates

The creation helper writes one Markdown draft under:

```text
assistant/lesson-planning/briefs/
```

Each draft includes:

- lesson slug metadata
- draft status
- human review requirement
- student-sensitive data prohibition
- safety notice
- source notes
- a Planning Queue Reference placeholder
- the contents of `assistant/lesson-planning/templates/lesson-brief-template.md`

Generated drafts are manual/local outputs and are gitignored except for `assistant/lesson-planning/briefs/README.md`.

## Folder Structure

```text
assistant/lesson-planning/briefs/
assistant/lesson-planning/briefs/README.md
assistant/lesson-planning/templates/lesson-brief-template.md
scripts/create-lesson-brief.sh
scripts/lesson-brief-status.sh
```

## How To Run

Check helper status:

```bash
bash scripts/lesson-brief-status.sh
bin/chief-of-staff --lesson-brief-status
```

Create a local draft brief:

```bash
bash scripts/create-lesson-brief.sh fractions-review
bin/chief-of-staff --create-lesson-brief fractions-review
```

Review the broader dashboard:

```bash
bin/chief-of-staff --dashboard
```

The helper uses a slug only in this PR. It does not parse planning queue rows yet.

The `Planning Queue Reference` section in each generated brief is a placeholder for future queue integration. Owen can fill it manually after reviewing the planning queue.

## Safety Rules

- No real student names.
- No private student data.
- No grades, medical notes, or behavior notes.
- No IEP/504 details.
- No parent contact information.
- No secrets.
- No external services.
- No sending, sharing, uploading, syncing, or publishing.
- Human review before classroom use.

## What This Does Not Do

- It does not generate a finished lesson automatically.
- It does not call an LLM by default.
- It does not align to standards automatically.
- It does not access school systems.
- It does not send or share anything.
- It does not read private student data.

## Future Ideas Not Implemented

- Read a specific planning queue row by title.
- List existing briefs from the CLI.
- Create related activity, assessment, and materials files.
- Create a full lesson package command.
- Optional LLM-assisted drafting after explicit review and permission.
- Update planning queue status after human confirmation.

## Recommended Next Step

Lesson activity and assessment helper, or lesson brief queue integration, depending on the build queue.
