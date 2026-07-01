# Teacher App Designer / Canvas LLM Plan

## Purpose

Teacher App Designer is a future section inside Teacher Workstation. Canvas LLM is a future drafting, preview, and export layer — not an autonomous publisher. This plan reframes an earlier Supabase-heavy Canvas automation idea into a single-user, local-first, Drive-first Teacher Workstation feature for Owen.

This PR adds documentation and read-only status only. It does not activate Canvas, Google Drive, OAuth, APIs, network calls, automation, scanning, indexing, OCR, embeddings, lesson generation, or student data handling.

## Strategic Direction

- **Single-user focus:** built for one teacher (Owen), not an enterprise multi-tenant platform.
- **Local-first and Drive-first:** curriculum and school files stay in Google Drive, NAS, iCloud, or local folders where possible.
- **Draft before publish:** Canvas LLM drafts, previews, and exports copy-ready packages before any future publish behavior.
- **Human approval required:** nothing becomes Canvas-facing without explicit teacher approval.
- **Supabase optional/future only:** avoid Supabase first; prefer local metadata and references unless a future need clearly appears.

## Intended Future Outputs

Canvas LLM may eventually help produce:

- Canvas pages
- Canvas assignments
- Canvas announcements
- Canvas module plans
- Canvas file/resource link plans
- weekly copy-ready Canvas packages

All outputs remain planning concepts until separately approved. No live Canvas behavior exists in this foundation.

## Current Status

- planning/status only
- no live Canvas behavior
- no live Drive behavior
- no runtime app code
- no APIs, OAuth, or network calls

## Ownership Split

| Layer | Responsibility |
| --- | --- |
| **Teacher Workstation** | Owns teacher-facing workflows and the overall teacher experience. |
| **Teacher App Designer** | Owns future screens, approval states, and teacher-facing design workflows. |
| **Canvas LLM** | Owns draft, preview, and export concepts — not silent publishing. |
| **Curriculum Builder** | Owns metadata and resource references for curriculum resources. |
| **Chief of Staff** | Status and safety verification only; does not own teacher workflows or Canvas content. |

Teacher Workstation owns teacher-facing workflows. Chief of Staff is status/safety only. Curriculum Builder owns metadata/resource references.

## Fast School-Year Path

A practical near-term sequence that stays local-first:

1. **Manual pacing CSV/export** — teacher-authored pacing references without automation.
2. **Manual curriculum registry references** — link to Curriculum Builder metadata without live sync.
3. **Copy-ready Canvas page/assignment/announcement drafts later** — local Markdown or export packages for review.
4. **Local preview and approval later** — teacher reviews drafts in Teacher Workstation before any export.
5. **Optional future Canvas connector only after approval** — separate explicit PR with OAuth, scope, dry-run, and rollback plans.

## Relationship to Curriculum Builder

Curriculum Builder / Curriculum Registry remains the source-reference layer for curriculum resources. Teacher App Designer and Canvas LLM may reference registry metadata but do not replace Curriculum Builder ownership of resource references.

## Safety Summary

This foundation prohibits:

- silent publishing
- student data
- Canvas API during foundation
- Google Drive API during foundation
- OAuth during foundation
- network calls
- real lesson generation
- generated lesson briefs or drafts
- real review notes
- document scanning, folder scanning, file indexing, OCR, embeddings, or vector database

See `docs/canvas-llm-safety-and-approval-contract.md` for the full safety and approval contract.

## Architecture Pointer

Preferred data flow is documented in `docs/canvas-llm-local-first-drive-first-architecture.md`.

## Placeholder Schema

Object vocabulary and placeholder field shapes are documented in `docs/canvas-llm-placeholder-schema.md`. Approval and export state vocabulary is in `docs/canvas-llm-approval-and-export-states.md`.

## Manual Export Package Plan

Future manual copy/export package workflow is documented in `docs/canvas-llm-manual-export-package-plan.md`.

## Manual Export Review Checklist

Teacher review checklists for future manual export packages are documented in `docs/canvas-llm-manual-export-review-checklist.md`.

## Manual Completion Status Plan

Future manual completion status tracking after teacher copy is documented in `docs/canvas-llm-manual-completion-status-placeholder-plan.md`.

## Related Verification Commands

```bash
bash scripts/teacher-app-designer-canvas-llm-status.sh
bin/chief-of-staff --teacher-app-designer-canvas-llm-status
```
