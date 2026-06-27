# Lesson Pack Status and Planner

## Purpose

The Lesson Pack Status and Planner is a local read-only status view for generated lesson briefs and related activity, assessment, and materials drafts.

It helps Owen see whether local lesson pack files exist for a safe lesson slug. It does not create, edit, promote, send, upload, or publish lesson files.

## What It Checks

The status script reads local generated files from:

```text
assistant/lesson-planning/briefs/
assistant/lesson-planning/drafts/
```

It groups files into lesson packs by safe slug and reports whether each pack has:

- a lesson brief
- an activity draft
- an assessment draft
- a materials draft

## How To Run

```bash
bash scripts/lesson-pack-status.sh
bin/chief-of-staff --lesson-pack-status
```

The broader dashboard also includes the lesson pack summary:

```bash
bin/chief-of-staff --dashboard
```

## Safety Rules

- Read-only status only.
- No real student names.
- No private student data.
- No external services.
- No Gmail, Drive, Calendar, APIs, or school systems.
- Human review remains required before classroom use.

## Filename Expectations

Generated lesson briefs use the safe lesson slug as the filename.

Draft files are recognized only when they end with one of these exact suffixes:

```text
-activity.md
-assessment.md
-materials.md
```

Unrecognized draft files are warned about and ignored by the pack table.

## Future Ideas

Future ideas not included in this PR:

- single-slug filtering, such as `scripts/lesson-pack-status.sh --slug fractions-review`
- JSON output
- next-action recommendations
- mark-reviewed workflows
- queue parsing
