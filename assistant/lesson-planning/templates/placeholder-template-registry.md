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
