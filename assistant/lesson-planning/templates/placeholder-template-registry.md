# Lesson-Planning Placeholder Template Registry

This registry is local-first documentation only. It records known placeholder template skeletons without enabling lesson generation, draft creation, document scanning, file indexing, API calls, automation, live integrations, or student-data handling.

## Status and Scope

The lesson-planning placeholder template registry is readiness scaffolding only. Entries in this registry are inert references to placeholder template structure; they do not generate lesson plans, briefs, drafts, review notes, or student-facing content.

The registry must remain local-first and non-integrated. Placeholder entries must not scan documents, index files, use student data, call networks or APIs, trigger automation, or connect to live services.

Any future move from placeholder-only structure to active lesson-planning behavior must be explicitly approved and reviewed in a separate PR.

## Registered Placeholders

| id | name | status | path | generates_content | uses_student_data | uses_network | uses_document_scanning | uses_file_indexing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `lesson-planning-placeholder-template` | Lesson-planning placeholder template | placeholder-only | `assistant/lesson-planning/templates/lesson-planning-placeholder-skeleton.md` | false | false | false | false | false |

## Placeholder Entry Shape

Placeholder registry entries should stay descriptive and static. Each entry should identify:

- a stable placeholder/template `id`
- a human-readable `name`
- `placeholder-only` status
- the referenced skeleton `path`
- `generates_content`: explicit non-generative status (must be `false`)
- `uses_student_data`: explicit no-student-data status (must be `false`)
- `uses_network`: explicit no-network/API status (must be `false`)
- `uses_document_scanning`: explicit no-document-scanning status (must be `false`)
- `uses_file_indexing`: explicit no-file-indexing status (must be `false`)

New rows should follow the table format above and include the same local-first safety markers.

## Placeholder Skeleton Section Inventory

The registered skeleton at `assistant/lesson-planning/templates/lesson-planning-placeholder-skeleton.md` reserves the following inert placeholder sections. None of these sections collect inputs or produce output.

| section | purpose |
| --- | --- |
| Metadata | Reserved structure only; no lesson metadata is collected or generated. |
| Learning Goals | Reserved structure only; no objectives, standards, or curriculum claims are generated. |
| Materials | Reserved structure only; no materials list is generated. |
| Activity Sequence | Reserved structure only; no warm-up, instruction, practice, or activity steps are generated. |
| Checks for Understanding | Reserved structure only; no assessment prompts, rubrics, or review notes are generated. |
| Differentiation Notes | Reserved structure only; no student-sensitive details are accepted. |
| Assessment Placeholder | Reserved structure only; no quiz, task, rubric, or grading guidance is generated. |
| Safety / Local-First Notes | Static documentation boundary; no scanning, indexing, parsing, APIs, automation, or live integrations. |

## Negative Scope

The lesson-planning placeholder path is not active yet. It does not support:

- lesson generation
- document scanning
- file indexing
- generated briefs
- generated drafts
- real review notes
- student data handling
- network/API calls
- automation
- live integrations

Any move from placeholder-only scaffolding to active lesson-planning behavior requires a separate explicitly approved PR.

## Safety Notes

- Registry entries are descriptive only.
- Registry entries do not create briefs, drafts, review notes, or student-facing content.
- Registry entries do not activate generation hooks.
- Registry entries do not permit student data.
- Registry entries do not permit document scanning, file indexing, network/API use, automation, or live integrations.

## Contributor Note

When extending this placeholder registry, keep entries descriptive and inert unless a separate PR explicitly approves active lesson-planning behavior. New placeholder entries should include clear local-first safety markers and must not imply lesson generation, document scanning, file indexing, student-data handling, network/API use, automation, or live integrations.

After editing the registry or placeholder skeletons, run:

```bash
bash scripts/lesson-planning-template-readiness-status.sh
```

## Readiness Milestone

PRs #93–#100 established the lesson-planning placeholder readiness scaffold. The scaffold now includes an inert placeholder template skeleton, a placeholder registry entry, status and scope documentation, README discoverability, contributor guidance, registry entry shape notes, a placeholder skeleton section inventory, explicit negative scope, static readiness validation, and smoke coverage.

This milestone remains placeholder-only. It does not activate lesson generation, document scanning, file indexing, student-data handling, network/API calls, automation, live integrations, generated briefs, generated drafts, or real review notes. Any future activation requires a separate explicitly approved PR.

## Phase Handoff

As of PR #101, the lesson-planning placeholder readiness phase is complete. The current scaffold is intentionally inert, local-first, and readiness-only.

Future work should begin from a separately approved next-phase plan. Follow-on cleanup or polish PRs must not activate lesson generation, document scanning, file indexing, student-data handling, network/API calls, automation, live integrations, generated briefs, generated drafts, or real review notes.

Any change that moves this area beyond placeholder-only scaffolding requires explicit approval in a separate PR.
