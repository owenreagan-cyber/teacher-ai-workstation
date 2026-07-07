# Teacher AI Workstation Master Plan

```text
Status: repo authority
Classification: documentation/status only
Teacher-facing system: Teacher Workstation
Orchestration/readiness layer: Chief of Staff
Implementation approval: required for runtime/product writes
```

## Direction

Teacher AI Workstation is a local-first teacher-facing system. The Chief of Staff coordinates status, safety, readiness, workflow guidance, and proof surfaces. Curriculum Library, Teacher Knowledge Vault, and Curriculum Registry remain metadata/reference-based: the repo/app stores references, review state, tags, hashes, source links, relationships, and safety status while large curriculum files remain in Google Drive, NAS, iCloud, or local folders.

## Current Focus

The near-term focus is preserving coherent repo authority, maintaining local-first curriculum/library planning, and keeping high-risk runtime work behind explicit Owen approval. Canvas LLM, Canvas self-healing, Morning Brief, Medical Center/System Health, classroom apps, local LLM, and widgets/workshop are named roadmap tracks but do not activate runtime behavior from this plan.

## Blocked By Default

Blocked unless separately approved:

- Canvas API, Canvas OAuth, live Canvas reads/writes, and Canvas publishing.
- Google Drive/NAS/iCloud connectors or live filesystem scanning outside approved fixed fixtures.
- real curriculum ingestion, OCR, embeddings, RAG, AI generation, or local model inference.
- student data handling.
- production registry writes or active `--write`.
- Supabase/Firebase implementation or migration.
- Mac system changes, widget install, shortcut install, automation/scheduler, or app execution.

## Authority Model

Repo docs, status scripts, and committed fixtures are authority. Uploaded notes, chat summaries, external memos, and prior assistant output are planning references until promoted into repo docs. Unsupported claims must be labeled as candidate, planned, unknown, blocked, or needing Owen decision.
