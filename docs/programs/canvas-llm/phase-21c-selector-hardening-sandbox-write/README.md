# Canvas LLM Phase 21C — Selector Hardening + Sandbox Write Readiness

## Purpose

Phase 21C moves beyond documentation-only readiness by hardening the existing-page selector and preparing a tightly gated first sandbox existing-page write path.

## Observed Phase 21B Problem

Phase 21B proved Canvas access was healthy and inventory could see sandbox QxWy pages, but existing-page dry-run returned:

```text
WARN: no sandbox QxWy candidate page found
```

Phase 21C fixes the selector path before any sandbox write experiment.

## Scope

Phase 21C may:

- read sandbox course `24399`
- read reference courses `21919`, `21944`, `21957`
- select one existing sandbox QxWy page for preview
- prefer unpublished, non-front-page, normal weekly pages
- avoid QxEND special pages
- avoid Q4W10 unless explicitly requested
- generate a write preview for one existing page
- expand local learning plans for announcements, attachments/files, assignments, Math lesson/Power Up/fact test mapping, and Reading lesson/comprehension/page mapping

## Write Boundary

Phase 21C may prepare a first sandbox write preview.

Actual writing remains blocked unless all of these are true:

```text
course_id == 24399
target page already exists
operation == update existing page
--allow-writes is supplied
approval phrase == PHASE_21C_SANDBOX_EXISTING_PAGE_WRITE_APPROVED
```

No production write is approved.

No reference course write is approved.

No parent notification is approved.

No grade/student/people access is approved.

## Learning Expansion

Phase 21C begins organizing future rule learning for:

- announcements
- attachments/files
- assignment naming
- Math lesson numbers
- Math Power Ups
- Math fact tests
- practice assignments
- Reading lesson numbers
- comprehension letters
- Reading page numbers
- resource attachment patterns

Runtime evidence remains under ignored `.local` paths.
