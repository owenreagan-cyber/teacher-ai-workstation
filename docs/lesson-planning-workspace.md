# Lesson Planning Workspace

## Purpose

The Lesson Planning Workspace is a safe, local scaffold for future teacher lesson workflows.

It creates structure for planning queues, lesson briefs, classroom activities, assessments, and materials checklists without generating real lesson content automatically.

## Folder Structure

```text
assistant/lesson-planning/
assistant/lesson-planning/README.md
assistant/lesson-planning/planning-queue.md
assistant/lesson-planning/templates/
assistant/lesson-planning/templates/lesson-brief-template.md
assistant/lesson-planning/templates/activity-template.md
assistant/lesson-planning/templates/assessment-template.md
assistant/lesson-planning/templates/materials-checklist-template.md
```

## How To Use The Planning Queue

Use `assistant/lesson-planning/planning-queue.md` for generic lesson ideas only.

Keep entries structured with the existing table columns:

- Title
- Grade/Subject
- Date Needed
- Standards/Source Notes
- Materials
- Status
- Review Status
- Next Action

Allowed status values are `idea`, `drafted`, `reviewed`, `ready`, and `archived`.

Future lesson-brief tooling may read this queue, so keep entries generic and safe.

## How To Use Templates

Copy the relevant template content into a local draft when planning:

- lesson brief
- activity
- assessment
- materials checklist

Templates are starting points only. They require human review before classroom use.

## Commands

Run the lesson planning status script:

```bash
bash scripts/lesson-planning-status.sh
```

Run through the Chief of Staff CLI:

```bash
bin/chief-of-staff --lesson-status
```

Run the broader dashboard:

```bash
bin/chief-of-staff --dashboard
```

## Safety Rules

- No real student names.
- No private student data.
- No grades, medical notes, or behavior notes.
- No IEP/504 details.
- No parent contact information.
- Human review before classroom use.
- No connected services yet.
- No Gmail, Drive, Calendar, school systems, OAuth, APIs, secrets, databases, or deployment.

## What This Does Not Do

- It does not generate full lessons automatically.
- It does not align to standards automatically.
- It does not access school systems.
- It does not send, share, publish, or export anything.
- It does not use student data.
- It does not call external services.

## Future Lesson Tooling

`planning-queue.md` can become a safe input queue for future lesson brief helpers.

The templates can become safe local starting points for future tools that help Owen draft briefs, activities, assessments, and materials checklists. Those future tools should keep the same safety boundaries and require human review.

## Recommended Next Step

Developer Mode project templates.

If Owen wants to go deeper into lessons first, a later lesson brief helper can be considered after the scaffold is reviewed.
