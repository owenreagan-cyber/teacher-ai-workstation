# Canvas LLM Safety and Approval Contract

## Purpose

This contract defines safety boundaries and required approval gates for the Teacher App Designer / Canvas LLM track. It applies during the documentation/status foundation and remains binding for all future implementation phases unless explicitly revised in a separate approved PR.

This document is planning/status only. It does not activate Canvas, Google Drive, OAuth, APIs, network calls, automation, or student data handling.

## Foundation Prohibitions

The following are prohibited during the foundation phase and remain blocked until separate explicit approval:

| Prohibition | Status |
| --- | --- |
| **No silent publishing** | Nothing may publish to Canvas without explicit teacher approval and a separate connector PR. |
| **No student data** | No real student names, IDs, grades, or student-facing personal information. |
| **No Canvas API during foundation** | No Canvas API access, tokens, or live connector behavior. |
| **No Google Drive API during foundation** | No Drive API access, OAuth, or live file sync. |
| **No OAuth during foundation** | No OAuth flows, token storage, or credential handling. |
| **No network calls** | No outbound network requests from status scripts, docs, or foundation code paths. |
| **No real lesson generation** | No generated lesson plans, activities, or assessments. |
| **No generated lesson briefs/drafts** | No files in lesson brief or draft directories beyond existing scaffold rules. |
| **No real review notes** | No teacher review note generation or student-performance commentary. |
| **No scanning, indexing, OCR, embeddings, or vector DB** | No document scanning, folder scanning, file indexing, OCR, embeddings, or vector database. |

## Required Future Approval Gates

Before any live Canvas connector may be considered, a separate approved PR must document and pass review for each gate:

1. **Canvas connector design doc** — scope, boundaries, and non-goals.
2. **OAuth/token handling plan** — how tokens are stored, rotated, and revoked locally.
3. **Canvas permission/scope plan** — minimum scopes required; no excess permissions.
4. **Dry-run contract** — preview-only mode that cannot mutate live Canvas state.
5. **Rollback/export plan** — how to undo or re-export without data loss.
6. **Idempotency plan** — safe re-runs without duplicate publishes.
7. **No-student-data proof** — explicit verification that connector paths exclude student data.
8. **Explicit network activation PR** — network calls are not implied by planning docs.

## Required Approval States

Future Teacher App Designer workflows must track explicit approval states. No state may skip teacher review or auto-advance to export.

| State | Meaning |
| --- | --- |
| `not_started` | Work has not begun; no draft exists. |
| `drafted` | A local draft exists but has not been submitted for review. |
| `needs_teacher_review` | Draft is ready for teacher review. |
| `teacher_revised` | Teacher has edited the draft; may need another review cycle. |
| `approved_for_export` | Teacher explicitly approved the draft for export (not publish). |
| `exported` | Copy-ready export package was produced locally; still not live on Canvas. |
| `blocked` | Work is blocked pending safety, missing metadata, or policy violation. |
| `rejected` | Teacher rejected the draft; must not proceed to export or publish. |

Publishing to Canvas (if ever approved) requires a state beyond `exported` and a separate connector activation PR. `exported` does not imply live Canvas publication.

## Human Approval Principle

- Teacher review is required before export.
- Export does not imply publish.
- Publish requires a future connector PR with all approval gates satisfied.
- Chief of Staff verifies readiness and safety markers only; it does not approve content on behalf of the teacher.

## Related Documents

- Plan: `docs/teacher-app-designer-canvas-llm-plan.md`
- Architecture: `docs/canvas-llm-local-first-drive-first-architecture.md`
- Curriculum references: `docs/curriculum-builder-canonical-planning-index.md`

## Related Verification Commands

```bash
bash scripts/teacher-app-designer-canvas-llm-status.sh
bin/chief-of-staff --teacher-app-designer-canvas-llm-status
```
