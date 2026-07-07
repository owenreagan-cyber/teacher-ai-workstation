# Approved Boundaries

```text
Status: repo authority
Classification: safety boundary
Runtime activation: no
```

## Approved In This Planning Layer

- Documentation.
- Status scripts.
- Tests for docs/status scripts.
- Fake/local schemas and fixtures when clearly non-runtime.
- Roadmap, build queue, command index, dashboard/status wiring.

## Blocked Without Separate Approval

- Production registry writes or active `--write`.
- Canvas API/OAuth/live reads/writes/publishing.
- Firestore reads/writes.
- Supabase/Firebase implementation.
- Real metadata intake from live systems.
- Real curriculum ingestion, parsing, copying, indexing, summarizing, OCR, embeddings, RAG, or generation.
- Student data.
- Drive/Canvas/NAS/iCloud/API/OAuth/network integrations.
- Local model inference or Ollama probing.
- Mac system changes, widget/shortcut installation, automation, scheduler, or app execution.
- Secrets, credentials, and external services.

PASS results are readiness evidence only. PASS does not authorize blocked work.
