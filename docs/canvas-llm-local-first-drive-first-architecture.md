# Canvas LLM Local-First / Drive-First Architecture

## Purpose

This document describes the preferred architecture for Teacher App Designer and Canvas LLM inside Teacher Workstation. It adapts a hosted, Supabase-heavy automation concept into a single-user, local-first, Drive-first model suitable for Owen's school workflow.

This document is planning/status only. It does not activate storage connectors, Canvas APIs, Google Drive APIs, OAuth, or network calls.

## Preferred Architecture

```text
Google Drive / local files / NAS / iCloud
        ↓
Manual or approved registry metadata
        ↓
Teacher Workstation local app
        ↓
Canvas LLM draft/preview/export layer
        ↓
Optional future Canvas publishing connector
```

Data flows down as references and drafts. Nothing publishes upward without explicit teacher approval and a separate connector PR.

## Storage Roles

| Storage | Role |
| --- | --- |
| **Google Drive** | Likely active school/curriculum working source; primary Drive-first location for live school files. |
| **NAS** | Archive, backup, and bulk curriculum vault. |
| **iCloud** | Optional convenience sync where useful. |
| **Local folders** | Repo fixtures, exported drafts, app data, and teacher-reviewed export packages. |

Files remain in Google Drive, NAS, iCloud, or local folders where possible. The workstation stores metadata and references, not paid hosted copies of all raw curriculum files.

## Workstation Data Model

Teacher Workstation should:

- store metadata and references to source files
- track approval states and export package locations locally
- avoid duplicating every raw curriculum file into paid hosted storage

Supabase is optional/future only, not default. Prefer local Markdown/CSV/JSON fixtures and SQLite only later if local state is genuinely needed.

## Canvas LLM Layer

Canvas LLM sits inside Teacher Workstation as a draft/preview/export layer:

- **Draft** — produce copy-ready Canvas page, assignment, announcement, or module plans locally.
- **Preview** — render drafts for teacher review without live Canvas API calls during foundation.
- **Export** — write local export packages (Markdown, CSV, JSON) for manual copy or future connector use.

Canvas API access is deferred until much later, after all safety and approval gates in `docs/canvas-llm-safety-and-approval-contract.md` are satisfied.

## Curriculum Registry Integration

Manual or approved registry metadata from Curriculum Builder feeds planning references only:

- pacing links
- resource labels
- subject/grade/unit metadata
- teacher-only vs student-facing flags

No live sync, crawler, or importer is activated by this architecture doc.

## First Useful Implementation Path

When implementation is separately approved, prefer this sequence:

1. **Markdown/CSV/JSON fixtures** — static planning and sample export shapes.
2. **Local copy-ready export package** — teacher-reviewed bundles on disk.
3. **SQLite only later** — if local approval-state tracking needs a database.
4. **Canvas API only much later** — after connector design, OAuth plan, dry-run contract, and explicit network activation PR.

## Non-Goals

This architecture is not:

- a multi-tenant hosted platform
- a Supabase-first data layer (Supabase is optional/future only, not default)
- a Google Drive sync service
- an autonomous Canvas publisher
- a lesson-generation or student-data system

## Related Documents

- Plan: `docs/teacher-app-designer-canvas-llm-plan.md`
- Safety contract: `docs/canvas-llm-safety-and-approval-contract.md`
- Curriculum Builder index: `docs/curriculum-builder-canonical-planning-index.md`

## Related Verification Commands

```bash
bash scripts/teacher-app-designer-canvas-llm-status.sh
bin/chief-of-staff --teacher-app-designer-canvas-llm-status
```
