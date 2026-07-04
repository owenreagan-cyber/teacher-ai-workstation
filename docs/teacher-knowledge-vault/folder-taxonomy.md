# Teacher Knowledge Vault — Folder Taxonomy

Last updated: 2026-07-04

```text
Status: planning-only
Real knowledge files on disk: no
assistant/memory/knowledge/ population: blocked — future Owen mission
Auto-loading: blocked
```

## Purpose

Define the **planned** directory layout for Teacher Knowledge Vault under Chief of Staff memory. This taxonomy is documentation only — no folders or files are created by the M0 architecture freeze mission.

## Planned Root

```text
assistant/memory/knowledge/
```

Aligned with `assistant/memory-policy.md` — Knowledge Vault local location.

## Planned Subdirectories (Inactive)

| Path | Purpose | Status |
| --- | --- | --- |
| `assistant/memory/knowledge/reference-summaries/` | Approved reference summaries (curriculum refs, workflow notes) | inactive — not created |
| `assistant/memory/knowledge/teaching-notes/` | Reusable classroom strategy notes (sanitized) | inactive — not created |
| `assistant/memory/knowledge/workflow-guides/` | Approved how-to snippets for Chief of Staff workflows | inactive — not created |
| `assistant/memory/knowledge/archive/` | Retired vault entries (manual move only) | inactive — not created |

## File Naming Conventions (Planning)

| Kind | Pattern | Example |
| --- | --- | --- |
| Reference summary | `ref-<topic-slug>.md` | `ref-shurley-pattern-placeholders.md` |
| Teaching note | `note-<topic-slug>.md` | `note-review-game-routine-placeholders.md` |
| Workflow guide | `guide-<workflow-slug>.md` | `guide-morning-brief-placeholders.md` |

All examples use fictional placeholder slugs. Real filenames require Owen approval per manual entry plan.

## Relationship to Other Memory Paths

| Path | Distinction |
| --- | --- |
| `assistant/memory/projects.md` | Active project continuity — not reference vault |
| `assistant/memory/teaching-context.md` | General teaching context — not full reference dumps |
| `assistant/intake/approved-context.md` | Approved intake summaries — promotion to vault is separate |
| `assistant/training/writing-samples/` | Writing style — not knowledge reference vault |

## Boundaries

- No automatic folder creation scripts
- No Git-tracked real knowledge content in M0
- No student-sensitive filenames or content
- No copied textbook chapters or proprietary school materials

## Proof

```bash
bin/chief-of-staff --teacher-knowledge-vault-m0-architecture-freeze-status
```
