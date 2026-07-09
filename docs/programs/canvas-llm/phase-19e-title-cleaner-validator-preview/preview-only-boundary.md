# Phase 19E Preview-Only Boundary

## Status

Active boundary for Phase 19E.

## Allowed

- read Phase 19D committed docs/data
- validate local JSON shape and references
- validate canonical title cleaner patterns
- validate preview-only safety flags
- validate fixtures include expected examples
- update handoff and memory
- add status script
- wire Chief of Staff status command

## Not Allowed

- Canvas API calls
- Canvas writes
- live Canvas fetches
- page creation
- assignment creation
- announcement creation
- file movement
- file upload
- file delete
- file publish
- body ingestion
- student data access
- raw `.local` metadata reads or commits
- school Canvas URL commits
- token exposure
- app implementation
- database migration
- RAG
- embeddings
- local model/Ollama execution

## Cleaner Boundary

The Phase 19E validator may check title-cleaner rules.

It may not:

- change Canvas titles
- publish assignments
- rename Canvas objects
- rename local files
- classify ambiguous inputs as final
- silently accept ambiguous inputs without review
