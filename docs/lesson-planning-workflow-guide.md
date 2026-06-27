# Lesson Planning Workflow Guide

## Purpose

This guide documents the safe local sequence for moving from a generic planning idea to local draft files and human review:

```text
planning queue -> lesson brief -> supporting drafts -> lesson pack status -> queue status -> human review
```

It is a workflow guide, not a lesson generator. It helps Owen remember the order of local checks and commands while keeping generated drafts local, gitignored, and review-only.

## Safety Boundaries

- Local only.
- No student-sensitive data.
- No real student names.
- No grades, behavior, medical, IEP, 504, parent communication, or private student information.
- No Gmail.
- No Google Drive.
- No Google Calendar.
- No APIs.
- No OAuth.
- No secrets.
- No LLM calls by default.
- No school systems.
- No publishing, sharing, or sending.
- Human review required before classroom use.

## The Safe Local Workflow

Use this sequence when a generic lesson idea is ready for local planning:

1. Review the planning queue.
2. Confirm the row has a safe lesson slug.
3. Create or review the lesson brief draft.
4. Create or review supporting activity, assessment, and materials drafts.
5. Check lesson pack status.
6. Check lesson queue status.
7. Complete human review before classroom use.
8. Keep generated drafts local and gitignored.

## Step 1: Planning Queue

Start with `assistant/lesson-planning/planning-queue.md`.

Queue rows should stay generic. Use broad lesson topics, source-note placeholders, materials placeholders, and review notes. Do not add student-sensitive details or real student names.

Check the workspace:

```bash
bin/chief-of-staff --lesson-status
```

## Step 2: Lesson Slug

Each queue row can include a `Lesson Slug`. The slug connects the row to local generated files.

Safe slugs use lowercase letters, numbers, and hyphens only. They must not start with a hyphen.

Examples:

```text
fractions-review
map-skills-introduction
ecosystems-vocabulary-practice
```

## Step 3: Lesson Brief Draft

When a queue row is ready for a local brief draft, use the approved local helper:

```bash
bin/chief-of-staff --create-lesson-brief LESSON_SLUG
```

The brief is a local draft for human review. It is not classroom-ready by default.

## Step 4: Supporting Drafts

Create supporting drafts only when useful:

```bash
bin/chief-of-staff --create-lesson-draft activity LESSON_SLUG
bin/chief-of-staff --create-lesson-draft assessment LESSON_SLUG
bin/chief-of-staff --create-lesson-draft materials LESSON_SLUG
```

These drafts are local, gitignored, and review-only.

## Step 5: Lesson Pack Status

Check whether generated local files form a complete or incomplete lesson pack:

```bash
bin/chief-of-staff --lesson-pack-status
```

A complete pack means the matching brief, activity, assessment, and materials drafts exist for the same safe slug.

## Step 6: Lesson Queue Status

Check whether planning queue rows connect to local generated files:

```bash
bin/chief-of-staff --lesson-queue-status
```

Queue warnings are normal when rows do not yet have generated files.

## Step 7: Human Review

Before classroom use, review every local brief and supporting draft for:

- source accuracy
- curriculum fit
- accessibility and safety
- no student-sensitive data
- no private student information
- no accidental secrets or credentials
- readiness for the intended classroom context

## Commands Reference

```bash
bin/chief-of-staff --lesson-status
bin/chief-of-staff --lesson-queue-status
bin/chief-of-staff --create-lesson-brief LESSON_SLUG
bin/chief-of-staff --create-lesson-draft activity LESSON_SLUG
bin/chief-of-staff --create-lesson-draft assessment LESSON_SLUG
bin/chief-of-staff --create-lesson-draft materials LESSON_SLUG
bin/chief-of-staff --lesson-pack-status
bin/chief-of-staff --dashboard
```

## What This Does Not Do

- It does not generate lesson content.
- It does not edit the planning queue.
- It does not create slugs automatically.
- It does not mark items reviewed.
- It does not export to Google Docs.
- It does not use Gmail or Google Drive.
- It does not call APIs, OAuth, databases, or school systems.
- It does not call an LLM.
- It does not publish, send, or share lesson files.

## Troubleshooting

Blank `Lesson Slug`: add a safe slug only when the row is generic and the slug is obvious.

Unsafe slug: replace uppercase letters, spaces, slashes, leading hyphens, or punctuation with lowercase words and hyphens.

Missing brief: create a local brief only when the row is ready for a review draft.

Missing supporting draft: create activity, assessment, or materials drafts only when they are useful.

Draft-only pack: review whether a lesson brief should be created or whether the supporting drafts are exploratory.

No generated lesson files yet: this is normal for new queue ideas.

Dashboard warning vs failure: warnings flag review items; failures mean required local files or syntax checks need attention.

Generated draft accidentally left behind: generated brief and draft files should stay local and gitignored. Remove test files after testing.

## Future Ideas Not Included

- single-slug workflow view
- next-action recommendations
- mark-reviewed workflow
- queue editing helper
- JSON output
- Google Docs export
- Gmail/Drive integrations
- AI lesson drafting
