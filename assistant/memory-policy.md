# Memory Policy

Phase 1C uses simple Markdown memory files in `assistant/memory/`. It does not use SQLite, a vector database, embeddings, cloud sync, or hidden ingestion.

Memory is not automatically loaded. Memory is explicitly included through CLI flags such as `--include-memory`, `--include-project-memory`, and `--include-writing-style-memory`.

Memory must remain inspectable and manually editable.

Sensitive student, parent, and confidential records are not allowed.

Memory cannot override safety, permission, sensitivity, source-verification, or current user instructions.

Use `assistant/memory/memory-log.md` for meaningful memory changes.

`bin/chief-of-staff --validate-memory` is available as a quick warning check, but it is not a security guarantee.

| Memory Type | What Gets Stored | What Does Not Get Stored | Local Location Later | Inspect/Delete | Privacy Level | Earliest Phase |
| --- | --- | --- | --- | --- | --- | --- |
| Project Memory | Project goals, decisions, blockers, next actions, source names | Private files copied wholesale, secrets, student-sensitive data | `assistant/memory/projects/` | Open/delete Markdown files | Medium | 1C |
| Knowledge Vault | User-approved reference summaries and reusable notes | Full Drive/Gmail dumps, unreviewed private data | `assistant/memory/knowledge/` | Open/delete Markdown files | Medium | 1C |
| Writing Style Memory | Approved, anonymized style patterns and examples | Raw inbox samples, student names, parent contact info | `assistant/memory/writing-style/` | Open/delete Markdown files | Medium | 1C |
| Source Summaries | Human-approved summaries of selected files/folders | Unverified citations, invented file names | `assistant/memory/source-summaries/` | Open/delete Markdown files | Medium | 1C |
| Artifact Memory | Final generated Teacher OS artifact notes and links | Draft clutter, obsolete temp files, private student details | `assistant/memory/artifacts/` | Open/delete Markdown files | Medium | 1C |
| Preference Memory | Explicit preferences for tone, workflows, tools, and formatting | Sensitive credentials, implicit guesses treated as facts | `assistant/memory/preferences/` | Open/delete Markdown files | Low to Medium | 1C |
| Feedback Memory | Corrections, ratings, edits, and "do this differently" notes | Unreviewed raw private content | `assistant/training/feedback-log.md` | Edit/delete entries | Low to Medium | 1A |
| Future 3D Project Memory | Product ideas, prototype notes, vendor notes, print outcomes | Copyright-infringing assets, private customer data | `assistant/memory/3d-projects/` | Open/delete Markdown files | Medium to High | 1I |

## Rules

- Memory must be inspectable by Owen.
- Memory must be deletable by Owen.
- Raw candidate writing samples are never automatically trusted.
- The assistant must ask before creating persistent memory.
- Full-drive or full-inbox memory is not allowed.
- Intake is the review stage before material becomes memory.
- Memory files should only receive information that has been approved or summarized through review.
- Raw intake should not be copied directly into memory without review.
- Intake decisions should be logged.
