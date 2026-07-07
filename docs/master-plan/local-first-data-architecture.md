# Local-First Data Architecture

```text
Status: repo authority
Classification: architecture boundary
Supabase: deprecated and blocked for new work
Firebase: deprecated and blocked for new work
```

Teacher AI Workstation should store durable working state locally whenever possible.

Preferred storage:

- local files.
- local memory/state.
- SQLite or similar local database.
- local JSON, YAML, Markdown, or CSV registries.
- optional future local Postgres or DuckDB only after explicit approval.
- Google Drive, NAS, iCloud, and local folders as source storage references, not app-owned hosted storage.

Curriculum Library, Teacher Knowledge Vault, and Curriculum Registry should store metadata, references, hashes, tags, review status, source links, relationships, and safety status. Large curriculum files remain in their source locations.

Do not create new Supabase or Firebase dependencies, schemas, clients, services, auth flows, storage buckets, Firestore collections, Firebase Functions, Supabase Edge Functions, hosted databases, realtime services, environment variables, emulator configs, or deployment paths.
