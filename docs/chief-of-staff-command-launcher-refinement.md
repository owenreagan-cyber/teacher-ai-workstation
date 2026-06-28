# Chief of Staff Command Launcher Refinement

## Purpose

This guide makes the local Chief of Staff command launcher and dashboard easier to use and more discoverable. It groups safe local commands so Owen can quickly answer what exists, what is safest to run now, and what to run next.

This is a local UX/status refinement only. It does not add integrations or change lesson-generation behavior.

## Safety Boundaries

- Local only
- Read-only by default
- No student-sensitive data
- No real student names
- No Gmail
- No Google Drive
- No Google Calendar
- No APIs
- No OAuth
- No secrets
- No LLM calls by default
- No document indexing
- No folder scanning
- No school systems
- No publishing, sharing, or sending
- Human review required before classroom use

Status helpers are read-only unless explicitly documented otherwise (for example local draft creation helpers that write gitignored lesson files only).

## Command Groups

| Group | Purpose |
|-------|---------|
| Everyday | Dashboard, setup, workflows, and command discovery |
| Lesson Planning | Workspace, briefs, drafts, packs, queue, workflow |
| Lesson Review | Checklist, single-slug view, review notes template |
| Developer and Workflow | Developer Mode, Cursor workflow, and support workflows |
| Future-Safety | Document indexing plan and other planning-only helpers |
| Verification | Intake review, verify-before-use, and validation helpers |

See also `docs/dashboard-polish-command-grouping-follow-up.md` for dashboard reading order and polish notes.

## Everyday Commands

Safest starting points:

```bash
bin/chief-of-staff --dashboard
bin/chief-of-staff --command-launcher-status
bin/chief-of-staff --list-workflows
bin/chief-of-staff --status
```

Use `--dashboard` first for a full local health picture.
Use `--command-launcher-status` for command grouping and launcher readiness.
Use `--list-workflows` for Markdown workflow names and local command labels.

## Lesson Planning Commands

```bash
bin/chief-of-staff --lesson-status
bin/chief-of-staff --lesson-brief-status
bin/chief-of-staff --lesson-draft-status
bin/chief-of-staff --lesson-pack-status
bin/chief-of-staff --lesson-queue-status
bin/chief-of-staff --lesson-workflow-status
```

Draft creation helpers also exist for local gitignored briefs and drafts. They require human review and are not automatic lesson generation.

## Lesson Review Commands

```bash
bin/chief-of-staff --lesson-review-checklist-status
bin/chief-of-staff --lesson-review-view LESSON_SLUG
bin/chief-of-staff --review-notes-template-status
```

These helpers guide human review. They do not approve lessons or store official review status.

## Developer and Workflow Commands

```bash
bin/chief-of-staff --developer-status
bin/chief-of-staff --cursor-workflow-status
```

Developer project template creation is available through `--create-developer-project`. It copies local templates only.

## Future-Safety Commands

```bash
bin/chief-of-staff --document-indexing-plan-status
```

These are planning-only helpers. They do not index documents, scan folders, or call external services.

## Dashboard Meaning

`bin/chief-of-staff --dashboard` is the local final health check for repo workflows.

The dashboard:

- runs read-only status helpers
- prints compact PASS/WARN/FAIL summaries
- shows the next recommended PR from `docs/build-queue.md`
- does not call Gmail, Drive, Calendar, APIs, OAuth, secrets, or school systems
- does not prove classroom readiness of lesson content by itself

Use the dashboard on local `main` after merges to confirm the repo is in a known-good state.

## Recommended Daily Flow

```text
1. Run dashboard
2. Read next recommended PR/action
3. Run the specific status helper for the workflow
4. Make changes only on a feature branch
5. Verify dashboard before calling work complete
```

## What This Does Not Do

- Does not add external integrations
- Does not call network services
- Does not call LLMs by default
- Does not index documents or scan folders
- Does not generate lesson content
- Does not edit lesson drafts, review notes, or the planning queue
- Does not approve or mark lessons reviewed
- Does not store official review status

## Future Ideas Not Included

```text
interactive TUI
Raycast launcher
Mac menu bar launcher
voice control
automated task routing
connected Gmail/Drive/Calendar commands
background monitoring
automatic workflow execution
```
