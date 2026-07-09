# Phase 19D Preview-Only Boundary

## Status

Active boundary for Phase 19D.

## Allowed

- create machine-readable seed evidence preview data
- create machine-readable seed rule preview data
- create source links preview data
- create title normalization preview rules
- create title normalization fixtures
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
- raw `.local` metadata commits
- school Canvas URL commits
- token exposure
- app implementation
- database migration
- RAG
- embeddings
- local model/Ollama execution

## Cleaner Boundary

The Title Cleaner is preview-only in Phase 19D.

It may describe and validate expected normalization behavior.

It may not:

- change Canvas titles
- publish assignments
- rename Canvas objects
- rename local files
- classify ambiguous inputs without review
