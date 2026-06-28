# Dashboard Polish and Command Grouping Follow-Up

## Purpose

This guide polishes how Owen reads the Chief of Staff dashboard and discovers grouped local commands after the command launcher refinement. It makes the dashboard calmer, clearer, and easier to scan without adding integrations or changing lesson-generation behavior.

## Safety Boundaries

- Local only
- Read-only/status/documentation polish
- No student-sensitive data
- No real student names
- No Reddit
- No Devvit
- No Gmail
- No Google Drive
- No Google Calendar
- No APIs
- No OAuth
- No secrets
- No LLM calls by default
- No document indexing
- No folder scanning
- No image fetching
- No image downloading
- No image processing
- No school systems
- No publishing, sharing, or sending
- Human review required before classroom use

## Dashboard Reading Order

Preferred reading order:

```text
1. Health summary
2. Critical blockers, if any
3. Available workflows
4. Command launcher
5. Lesson planning and review sections
6. Future-safety/planning sections
7. Recommendation
```

Start with the final `Summary` health line, then scan upward only if a section needs attention.

## Command Grouping Model

Use these group names consistently:

```text
Everyday
Lesson Planning
Lesson Review
Developer and Workflow
Future-Safety
Verification
```

`bin/chief-of-staff --list-workflows` and `bin/chief-of-staff --command-launcher-status` should reflect these groups.

## Everyday Commands

Safest first commands:

```bash
bin/chief-of-staff --dashboard
bin/chief-of-staff --list-workflows
bin/chief-of-staff --status
bin/chief-of-staff --command-launcher-status
```

## Lesson Planning Commands

```bash
bin/chief-of-staff --lesson-status
bin/chief-of-staff --lesson-brief-status
bin/chief-of-staff --lesson-draft-status
bin/chief-of-staff --lesson-pack-status
bin/chief-of-staff --lesson-queue-status
bin/chief-of-staff --lesson-workflow-status
```

## Lesson Review Commands

```bash
bin/chief-of-staff --lesson-review-checklist-status
bin/chief-of-staff --lesson-review-view LESSON_SLUG
bin/chief-of-staff --review-notes-template-status
```

## Developer and Workflow Commands

```bash
bin/chief-of-staff --developer-status
bin/chief-of-staff --cursor-workflow-status
```

Markdown workflows such as `project-review`, `lesson-support`, and `app-development-support` also live under this group in `--list-workflows`.

## Future-Safety Commands

```bash
bin/chief-of-staff --document-indexing-plan-status
bin/chief-of-staff --wallpaper-photo-curator-plan-status
```

These are planning-only helpers. They do not index documents, scan folders, fetch images, or call external services.

## Recommended Daily Flow

```text
1. Run dashboard
2. Read next recommended PR/action
3. Run the specific status helper for the workflow
4. Make changes only on a feature branch
5. Verify dashboard before calling work complete
```

## Future Appearance & Vibe Upgrade

Future Appearance & Vibe Upgrade:

```text
Automated Wallpaper and Photo Curator
```

Planning-only. See `docs/appearance-vibe-wallpaper-photo-curator-plan.md` for the full future design.

Status command:

```bash
bin/chief-of-staff --wallpaper-photo-curator-plan-status
```

A future local app may automatically fetch wallpaper/photo candidates from approved sources, keep a small temporary review queue, notify Owen, show Approve/Dismiss choices, delete dismissed images, process approved images, and store them in wallpaper/photo-widget rotation folders.

Future boundaries (dashboard polish PR and curator plan PR):

```text
Not implemented in this PR.
No Reddit or Devvit integration in this PR.
No image fetching in this PR.
No image downloading in this PR.
No image processing in this PR.
No macOS wallpaper automation in this PR.
No notifications in this PR.
No folder scanning in this PR.
No network calls in this PR.
```

## What This PR Does Not Do

- Does not build the Automated Wallpaper and Photo Curator app
- Does not add Reddit, Devvit, or external integrations
- Does not fetch, download, or process images
- Does not automate macOS wallpaper or Photos settings
- Does not send notifications
- Does not scan folders or index documents
- Does not generate lesson content
- Does not edit lesson drafts, review notes, or the planning queue

## Future Ideas Not Included

```text
interactive TUI
Raycast launcher
Mac menu bar launcher
voice control
automated task routing
connected Gmail/Drive/Calendar commands
Reddit or Devvit wallpaper app
wallpaper fetcher
image processing worker
photo widget rotation automation
background monitoring
automatic workflow execution
```
