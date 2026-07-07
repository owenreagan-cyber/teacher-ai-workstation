# Canvas LLM Import Preview Fixtures

This directory contains tracked fake/local artifacts for Canvas LLM preview gates.

## Phase 12 fixture

`fake-local-sandbox-import-artifact-course-24399.json` is a fake/local import preview artifact shape for the approved sandbox demo course `24399`.

It preserves reviewed entity counts and import-artifact shape only. It does not copy real Canvas staged metadata records from `.local`.

Safety guarantees:

- fake IDs only
- fake sample titles only
- fake source references only
- no copied real Canvas metadata records
- no curriculum body/content
- no student data
- no Canvas API call
- no live fetch
- no import performed
- no knowledge DB write
- no runtime database write
- no production write
- no canonical catalog write
- no generation, RAG, or embeddings
- no local model/Ollama execution
- no tracked school Canvas URL
- no tracked tokens or secrets
