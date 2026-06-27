# Lesson Planning Workspace

This is a local planning workspace scaffold, not an automatic lesson generator.

It exists to prepare safe, structured teacher planning workflows before future lesson tools are built. Use it for generic lesson ideas, briefs, activity planning, assessment planning, and materials checklists.

## Safety Rules

- Local teacher planning only.
- Do not store student-sensitive data here by default.
- Do not include real student names.
- Do not include grades, medical information, behavior notes, IEP/504 details, parent contact information, or private school situations.
- Lesson drafts require human review before classroom use.
- Connected services require explicit future permission.

## Current Files

- `planning-queue.md`: safe queue for generic lesson planning ideas.
- `drafts/README.md`: tracked marker for local activity, assessment, and materials drafts.
- `templates/lesson-brief-template.md`: starter structure for future lesson briefs.
- `templates/activity-template.md`: starter structure for classroom activities.
- `templates/assessment-template.md`: starter structure for checks for understanding.
- `templates/materials-checklist-template.md`: starter structure for materials and prep.

## Lesson Brief Helper

Create a local draft lesson brief for teacher review:

```bash
bin/chief-of-staff --create-lesson-brief LESSON_SLUG
```

Check lesson brief helper status:

```bash
bin/chief-of-staff --lesson-brief-status
```

Drafts are written under `assistant/lesson-planning/briefs/`, are local and gitignored, and require human review before classroom use.

## Lesson Draft Helper

Create a local activity, assessment, or materials checklist draft for teacher review:

```bash
bin/chief-of-staff --create-lesson-draft TYPE LESSON_SLUG
```

Check lesson draft helper status:

```bash
bin/chief-of-staff --lesson-draft-status
```

Valid types are `activity`, `assessment`, and `materials`. Drafts are written under `assistant/lesson-planning/drafts/`, are local and gitignored, and require human review before classroom use.

## Future Use

Future tools may help create briefs, activities, assessments, and materials checklists from the queue and templates. Those tools should remain local-first and should require human review before classroom use.

`planning-queue.md` may be read by future lesson-brief tooling, so keep entries generic, structured, and safe.
