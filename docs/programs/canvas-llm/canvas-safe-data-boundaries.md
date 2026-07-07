# Canvas Safe Data Boundaries

```text
Status: PHASE_0_DOCS_ONLY
Classification: safety boundary
Student data: blocked
Live Canvas access: blocked
```

## Allowed In Phase 0

- repo-authored standards notes.
- fake/local page, module, and assignment examples.
- report templates.
- manual review categories.
- non-authoritative planning notes clearly labeled as candidates.

## Blocked In Phase 0

- Canvas API or OAuth.
- live Canvas reads.
- Canvas writes or publishing.
- browser automation.
- student names, grades, submissions, comments, accommodations, analytics, messages, or rosters.
- real course pages, modules, assignments, rubrics, or discussions.
- real curriculum ingestion.
- AI generation/runtime behavior.
- Supabase/Firebase.

## Safe Evidence Rule

If evidence would require logging into Canvas, querying Canvas, viewing student-specific data, or copying real course content, it is blocked for Phase 0.

## PASS Boundary

PASS from a status command means the docs/status scaffold is present. PASS does not authorize Canvas access, content generation, export, deployment, or self-healing.
