# Canvas GET-Only Sweep Plan (2026-2027)

```text
Status: implementation-ready plan (no live execution performed)
Classification: read-only exploration prep
Live Canvas writes: forbidden
```

This is the Phase 2 prep spec. It defines a safe, GET-only exploration of live 2026-2027 Canvas. Do not execute in Phase 1.

## Read-only guarantee

Any exploration script must:

```text
allow GET only
forbid POST
forbid PUT
forbid PATCH
forbid DELETE
never print CANVAS_API_TOKEN
never persist the token into repo files
```

Static validation must prove no write verbs (`POST`, `PUT`, `PATCH`, `DELETE`) exist in the exploration path.

## Target courses

| Subject | Course ID |
| --- | --- |
| Math | 26404 |
| Reading/Spelling | 26442 |
| Language Arts | 28171 |
| History | 28165 |
| Science | 28166 |
| Homeroom | 26429 |

## Sweep scope (per course)

Capture:

```text
course metadata
relevant course settings
front page
weekly agenda page titles/slugs
representative weekly page HTML
modules
module items
assignment groups
representative assignments
recent announcements
Homeroom newsletter
relevant Canvas file metadata
points
grading type
submission type
due dates/times
availability dates
published state
counts-toward-final-grade behavior where exposed
```

## Unresolved items to investigate

```text
current module-placement enforcement
parent/observer relationship resolution
Canvas Conversation attachment/image support
```

These are currently unresolved/insufficiently verified and must be confirmed by fresh read-only observation, not inferred.

## Raw vs normalized data

Plan for both:

```text
raw GET snapshots
+
normalized precedent JSON
```

Target normalized organization:

```text
data/canvas/precedent/math/
├── course.json
├── assignment-groups.json
├── modules.json
├── weekly-page-samples.json
├── assignments/
│   ├── lesson-homework.json
│   ├── fact-assessment.json
│   └── written-assessment.json
└── announcements.json
```

Raw/live snapshots stay local and gitignored (`.local/canvas-llm/`) per existing privacy policy. Normalized precedent JSON may be reviewed for tracking only after teacher approval.

## Credential loading

Read the token env-first, then `~/.config/teacher-ai-workstation/canvas.env` (mode 0600), reusing `scripts/canvas_llm_phase22/canvas_credentials.py`. Never print or persist the token.

## Execution gating

If live execution is not yet required, stop at this implementation-ready plan. Live GET execution begins only with explicit Owen approval.
