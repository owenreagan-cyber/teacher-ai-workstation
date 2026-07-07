# Thales Canvas Standard

```text
Status: PHASE_0_DOCS_ONLY
Classification: Canvas LLM standards scaffold
Runtime activation: no
Canvas API/OAuth/live reads: blocked
Canvas writes/publishing: blocked
Student data: blocked
```

## Purpose

This document is the Phase 0 standards scaffold for future Canvas LLM work. Canvas should become the living specification before Canvas-related generation, validation, export, deployment, or self-healing is considered.

Phase 0 does not claim complete Canvas policy coverage. It defines the safe categories that a future Canvas Knowledge Sweep should fill with repo-approved, evidence-backed notes.

## Standard Categories

Future evidence should be organized under these categories:

| Category | Evidence to capture later | Phase 0 boundary |
| --- | --- | --- |
| Course structure | modules, pages, assignments, navigation expectations | fake/local examples only |
| Page formatting | headings, links, lists, embedded media, accessibility expectations | no real course pages |
| Assignment metadata | due dates, points, submission type, rubric presence | fake metadata only |
| Teacher workflow | review states, approval states, manual export expectations | no automation |
| Student safety | what must never be stored, generated, or inspected | student data blocked |
| Publishing readiness | manual checklist concepts | Canvas writes blocked |
| Drift/self-healing | future issue categories and recommendation language | recommendation-only future |

## Phase 0 Non-Activation

This standard does not approve:

- Canvas API or OAuth.
- live Canvas reads.
- Canvas writes or publishing.
- browser automation.
- generated assignments, pages, newsletters, or modules.
- student data handling.
- real curriculum ingestion.
- AI generation/runtime behavior.
- Supabase/Firebase use.

## Future Promotion Gate

A future phase may only promote these standards after a separate approved mission defines allowed sources, evidence capture rules, review responsibilities, and explicit non-student-data handling.
