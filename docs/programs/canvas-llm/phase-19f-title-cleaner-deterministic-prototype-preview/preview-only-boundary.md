# Phase 19F Preview-Only Boundary

## Status

Active boundary for Phase 19F.

## Allowed

- read committed Phase 19D title-normalization fixtures
- read committed Phase 19D title-normalization rules
- run a local deterministic prototype against committed fixture examples
- generate a local preview report
- validate canonical output expectations
- validate ambiguous inputs remain review-required
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
- silent Canvas mutation

## Cleaner Boundary

The prototype may normalize committed fixture examples only.

It may not:

- change Canvas titles
- publish assignments
- rename Canvas objects
- rename local files
- classify ambiguous inputs as final
- silently accept ambiguous inputs without review
