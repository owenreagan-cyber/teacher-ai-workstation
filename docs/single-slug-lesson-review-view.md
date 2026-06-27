# Single-Slug Lesson Review View

## Purpose

This helper shows one safe lesson slug's local review context in one place. It helps Owen inspect queue membership, local brief and draft file presence, and human review reminders before classroom use. It does not generate content, edit files, or decide readiness.

## Safety Boundaries

- Local only
- Read-only
- No student-sensitive data
- No real student names
- No grades, behavior, medical, IEP, 504, parent communication, or private student information
- No Gmail
- No Google Drive
- No Google Calendar
- No APIs
- No OAuth
- No secrets
- No LLM calls by default
- No school systems
- No publishing, sharing, or sending
- Human review required before classroom use

## How It Works

1. Provide one safe lesson slug.
2. The script validates the slug format.
3. It checks whether the slug appears in `assistant/lesson-planning/planning-queue.md`.
4. It checks whether matching local brief and draft files exist.
5. It prints review reminders and suggested status commands.
6. Owen completes human review using the Safe Local Lesson Review Checklist.

## Safe Slug Format

Lesson slugs must match:

```text
^[a-z0-9][a-z0-9-]*$
```

Allowed:

- lowercase letters
- numbers
- hyphens after the first character

Not allowed:

- spaces
- uppercase letters
- slashes or path traversal
- leading hyphen
- punctuation other than hyphen

Example safe slug: `fractions-review`

## What The View Shows

For one slug, the view reports:

- whether the slug is safe
- whether the slug appears in the planning queue
- queue row context when matched (title, status, review status, next action)
- whether the lesson brief exists
- whether activity, assessment, and materials drafts exist
- review checklist reminders
- suggested commands for deeper status checks

Missing local files produce warnings, not failures.

## Commands

Inspect one lesson slug:

```bash
bin/chief-of-staff --lesson-review-view fractions-review
bash scripts/lesson-review-view.sh fractions-review
```

Related read-only helpers:

```bash
bin/chief-of-staff --lesson-review-checklist-status
bin/chief-of-staff --lesson-pack-status
bin/chief-of-staff --lesson-queue-status
bin/chief-of-staff --dashboard
```

## Review Reminders

- Human review required before classroom use.
- Do not include student-sensitive data.
- Do not include real student names.
- Verify source accuracy and curriculum fit.
- Check accessibility, safety, and materials.
- Use `docs/safe-local-lesson-review-checklist.md` for the full checklist.

## What This Does Not Do

- Does not generate lesson content
- Does not edit lesson drafts
- Does not edit the planning queue
- Does not approve or mark lessons reviewed
- Does not publish, send, share, export, or upload anything
- Does not call Gmail, Drive, Calendar, APIs, OAuth, secrets, school systems, or LLMs by default
- Does not deeply inspect lesson file content or score quality

## Troubleshooting

**Unsafe slug error**

Use lowercase letters, numbers, and hyphens only. Do not include spaces, uppercase letters, slashes, or a leading hyphen.

**Slug not in planning queue**

The view still runs and warns. Add or verify the queue row manually if the lesson should be tracked there.

**Missing brief or drafts**

Warnings are expected for new queue rows. Create local drafts with the existing brief and draft helpers, then re-run the review view.

**Required repo file missing**

If a required repo file is missing, the script fails. Restore the repo file or re-run from a clean checkout.

## Future Ideas Not Included

The following are intentionally not part of this PR:

```text
mark-reviewed workflow
review notes template
JSON output
Google Docs export
Gmail/Drive integrations
AI lesson revision
rubric scoring
queue editing
```

These may be considered in separate future PRs with explicit approval and safety review.
