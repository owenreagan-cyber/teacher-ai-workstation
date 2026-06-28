# Review Notes Template

## Purpose

This template helps Owen record personal human review notes after inspecting a lesson slug. It is optional, local-only, and not an official approval system.

Copy this template manually when you want to keep private review thinking alongside lesson planning work. The repo does not create, store, or track your filled-in notes automatically.

## Safety Boundaries

- Local only
- Optional personal notes
- Not official review status
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

## How To Use

1. Inspect the lesson slug with the single-slug review view and review checklist.
2. Copy this template into a personal local file under `assistant/lesson-planning/review-notes/` if desired.
3. Fill in only generic, non-student-specific notes.
4. Keep notes local. Do not commit personal review notes unless Owen explicitly chooses to.

Suggested commands before filling notes:

```bash
bin/chief-of-staff --lesson-review-view LESSON_SLUG
bin/chief-of-staff --lesson-review-checklist-status
bin/chief-of-staff --review-notes-template-status
```

## Template

```markdown
# Lesson Review Notes

Status: personal local notes only
Official review status: no
Human review required: yes

## Lesson Slug

LESSON_SLUG

## Date Reviewed

YYYY-MM-DD

## Reviewer

Owen Reagan

## Source Files Checked

- [ ] Planning queue row
- [ ] Lesson brief
- [ ] Activity draft
- [ ] Assessment draft
- [ ] Materials draft

## Privacy Check

- [ ] No real student names
- [ ] No student-sensitive data
- [ ] No grades, behavior, medical, IEP, 504, parent communication, or private student information

Notes:

## Source and Accuracy Check

Notes:

## Curriculum Fit Check

Notes:

## Classroom Readiness Check

Notes:

## Accessibility and Safety Check

Notes:

## Materials Check

Notes:

## Revision Notes

Notes:

## Human Decision

Choose one personal decision label for your own notes only. This is not official review status.

- [ ] READY FOR CLASSROOM USE AFTER HUMAN REVIEW
- [ ] NEEDS REVISION
- [ ] HOLD
- [ ] DO NOT USE

## Next Action

Notes:
```

## What This Does Not Do

- Does not generate lesson content
- Does not edit lesson drafts
- Does not edit the planning queue
- Does not approve or mark lessons reviewed
- Does not store official review status in the repo
- Does not publish, send, share, export, or upload anything
- Does not call Gmail, Drive, Calendar, APIs, OAuth, secrets, school systems, or LLMs by default

## Commands Reference

```bash
bin/chief-of-staff --review-notes-template-status
bin/chief-of-staff --lesson-review-view LESSON_SLUG
bin/chief-of-staff --lesson-review-checklist-status
bin/chief-of-staff --dashboard
```

## Future Ideas Not Included

```text
mark-reviewed workflow
official review status storage
JSON output
Google Docs export
Gmail/Drive integrations
AI lesson revision
rubric scoring
queue editing
automatic note creation
```
