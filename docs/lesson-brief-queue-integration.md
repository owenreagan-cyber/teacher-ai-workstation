# Lesson Brief Queue Integration

## Purpose

Lesson Brief Queue Integration is a local, read-only status helper that compares planning queue rows with local generated lesson files.

It helps Owen see which queue ideas have safe lesson slugs, which slugs have matching local lesson briefs, and which slugs have supporting activity, assessment, or materials drafts. It does not generate lesson content, edit the queue, or call any external services.

## Lesson Slug Column

The planning queue includes an optional `Lesson Slug` column. A slug is a short local identifier that connects a queue row to local generated files.

Safe slugs use lowercase letters, numbers, and hyphens only. They must not start with a hyphen.

Examples:

```text
fractions-review
map-skills-introduction
ecosystems-vocabulary-practice
```

Blank slugs are allowed, but the status helper warns because they cannot be matched to local files.

## Local File Matching

For each safe slug, the helper checks for:

```text
assistant/lesson-planning/briefs/LESSON_SLUG.md
assistant/lesson-planning/drafts/LESSON_SLUG-activity.md
assistant/lesson-planning/drafts/LESSON_SLUG-assessment.md
assistant/lesson-planning/drafts/LESSON_SLUG-materials.md
```

If no generated files exist yet, the helper reports `no` for those file columns and exits successfully with warnings.

## How To Run

```bash
bash scripts/lesson-queue-status.sh
bin/chief-of-staff --lesson-queue-status
```

The Chief of Staff dashboard also includes a compact Lesson Queue summary:

```bash
bin/chief-of-staff --dashboard
```

## Warnings

Warnings do not mean the helper failed. They identify queue rows that need human review.

The helper warns for:

- zero queue entries
- blank `Lesson Slug`
- unsafe `Lesson Slug`
- duplicate safe slugs
- slugs with no matching brief
- slugs with no supporting drafts
- risky labels such as `Student:`, `IEP:`, `504:`, `Medical:`, `Behavior:`, `API key:`, `Secret:`, `Token:`, or `Password:`
- table rows that are malformed enough to skip safely

Duplicate slugs are not automatically fixed. Owen should decide whether the rows are duplicates or whether one slug should be changed.

## Safety Boundaries

- Local read-only status only.
- No lesson generation.
- No queue editing.
- No student-sensitive data.
- No real student names.
- No Gmail, Google Drive, Calendar, APIs, OAuth, secrets, school systems, databases, deployment, or network calls.
- No LLM calls.
- Human review remains required before classroom use.

## Troubleshooting

If a row has a blank slug, add a generic safe slug only when the row is safe and the slug is obvious.

If a row has an unsafe slug, replace spaces, slashes, uppercase letters, or punctuation with lowercase words and hyphens.

If a row has no generated files, that can be normal. Create or review local drafts only through the approved local lesson helper workflow.

## Future Ideas

Future ideas not included in this PR:

- automatic slug suggestion
- queue row editing
- single-slug filtering
- JSON output
- next-action recommendations
- mark-reviewed workflow
- Google Docs export
- Gmail/Drive integrations
