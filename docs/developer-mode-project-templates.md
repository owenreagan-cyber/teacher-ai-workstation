# Developer Mode Project Templates

## Purpose

Developer Mode project templates give Owen a safe local starting point for small teacher tools, lesson helpers, classroom productivity scripts, and future app prototypes.

This is a local template system. It does not build production apps, install packages, deploy to the web, create databases, call APIs, or handle school data.

## Folder Structure

```text
developer-mode/
developer-mode/README.md
developer-mode/project-queue.md
developer-mode/templates/
developer-mode/templates/local-script-tool/
developer-mode/templates/lesson-helper/
developer-mode/templates/checklist-generator/
developer-mode/templates/rubric-helper/
developer-mode/templates/mini-app-plan/
developer-mode/projects/
```

`developer-mode/projects/` is generated local workspace output. It is gitignored so user-created local projects are not accidentally committed.

## Template List

- `local-script-tool`: tiny local Bash script starter with a deterministic placeholder test.
- `lesson-helper`: planning-only template for a future local lesson helper.
- `checklist-generator`: planning template for future checklist helpers.
- `rubric-helper`: planning template for future rubric helpers.
- `mini-app-plan`: planning-only template for future small local app ideas.

## Status Commands

Run the Developer Mode status script:

```bash
bash scripts/developer-mode-status.sh
```

Run through the Chief of Staff CLI:

```bash
bin/chief-of-staff --developer-status
```

Run the broader dashboard:

```bash
bin/chief-of-staff --dashboard
```

## Create A Project

Create a local project from a template:

```bash
bash scripts/create-developer-project.sh lesson-helper fractions-review-helper
```

Or use the Chief of Staff CLI wrapper:

```bash
bin/chief-of-staff --create-developer-project lesson-helper fractions-review-helper
```

Project creation writes files under:

```text
developer-mode/projects/
```

Project creation is manual. The dashboard never runs the project creation helper.

This PR does not update `developer-mode/project-queue.md` automatically. A later PR may append created projects to the queue after human confirmation.

## Safety Rules

- No student-sensitive data.
- No real student names.
- No grades, medical notes, or behavior notes.
- No IEP/504 details.
- No parent contact information.
- No secrets.
- No deployment.
- No external services yet.
- Human review before classroom use.

## What This Does Not Do

- It does not build real apps automatically.
- It does not install packages.
- It does not deploy to the web.
- It does not create databases.
- It does not call APIs.
- It does not handle school data.
- It does not start a public server.

## Future Lesson/App Tooling

Templates are safe starting points.

Future helpers may generate or update local project files only after review. Future work can add queue updates, local audit logs, richer queue validation, or starter tests for mini apps, but those are not implemented here.

## Recommended Next PR

Lesson brief helper.

Scope: local helper that reads the lesson planning queue/templates and drafts a lesson brief file for human review only. No student data, no Gmail/Drive, no external integrations.
