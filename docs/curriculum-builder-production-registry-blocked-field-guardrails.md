# Production Registry Blocked Field Guardrails

Last updated: 2026-07-02

```text
Status: metadata_boundary_refinement_planning
Classification: blocked-field guardrail spec — planning validators only
Authority: supplements docs/curriculum-builder-production-registry-metadata-source-boundaries.md
```

## Purpose

Define blocked metadata and source-reference categories and **future validator expectations** for governed production records. No live validation against real curriculum files.

## Guardrail Principle

**Fail closed:** if a field or value matches a blocked category, the validator rejects the record. No auto-sanitization of student data or curriculum content.

## Blocked Categories

| Category | Blocked examples | Future validator rule |
| --- | --- | --- |
| Worksheet text | Pasted worksheet body | Reject > 500 chars in label fields; reject worksheet markers |
| Textbook excerpts | Chapter text | Reject multi-paragraph content |
| Answer keys | Key content | Reject answer-key field names and patterns |
| Assessment questions | Question text | Reject assessment body fields |
| Rubric body | Full rubric text | Reject rubric content fields |
| Student names | Any student identifier | Reject `student_name`, `roster`, name lists |
| Rosters | Class rosters | Reject roster arrays |
| Grades | Numeric grades | Reject `grade`, `score` tied to students |
| Accommodations | IEP/accommodation detail | Reject accommodation fields |
| IEP details | IEP content | Reject IEP field names |
| Student work | Submitted work | Reject student work fields |
| OCR output | OCR text blocks | Reject `ocr_*`, extracted text fields |
| File hashes | Hashes from real files | Reject `sha256`, `md5`, `file_hash` |
| Extracted PDF metadata | PDF parser output | Reject parser metadata fields |
| AI summaries | LLM-generated summaries | Reject `ai_summary`, `generated_*` |
| Embeddings | Vector data | Reject `embedding`, `vector` |
| Vector IDs | Vector store IDs | Reject vector ID fields |
| RAG chunks | RAG retrieval chunks | Reject `chunk`, `rag_*` |
| Drive file IDs | Google Drive IDs | Reject drive ID patterns in any field |
| Canvas course/module IDs | Canvas IDs | Reject canvas ID patterns |
| NAS mount paths | `/Volumes/...`, `smb://` | Reject in source_reference |
| iCloud paths usable by code | Resolvable iCloud paths | Reject absolute paths |
| Live fetch URLs | `http://`, `https://` in source fields | Reject URL schemes |
| OAuth tokens | Tokens | Reject `token`, `oauth`, `bearer` |
| API keys | Keys | Reject `api_key`, `secret` |
| Webhook URLs | Webhooks | Reject webhook fields |
| Crawler-discovered paths | Crawler output | Reject `crawler_*`, indexed paths |
| Folder indexes | Directory listings | Reject index arrays |
| Directory listings | `ls` output | Reject listing blobs |
| Import manifests | Bulk import | Reject `import_manifest`, bulk arrays |
| Dry-run auto-promotion | Promotion flags | Reject `auto_promote`, `promote_from_dry_run` |
| Bulk record arrays | Batch writes | Reject multi-record write payloads |

## Blocked Field Name Patterns (Future)

Reject record keys matching (case-insensitive):

```text
student_
roster
iep_
accommodation
ocr_
embedding
vector_
rag_
api_key
oauth_
webhook
file_hash
drive_file_id
canvas_course_id
import_manifest
auto_promote
```

## Negative Test Expectations

Planning validator `scripts/curriculum-builder-production-registry-metadata-boundary-validate.sh` must:

- Reject `resource-*` IDs in fake planning fixtures
- Accept `example-*` IDs in planning fixtures only
- Reject blocked URL patterns in `source_reference`
- Reject unknown `source_type` values

## Related Documents

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-production-registry-manual-metadata-field-contract.md` | Allowed fields |
| `docs/curriculum-builder-production-registry-source-reference-contract.md` | Allowed source shape |
| `assistant/curriculum-builder/samples/metadata-boundary-planning/` | Fake planning fixtures |

## Non-Activation

These guardrails are planning and fake-fixture validation only. They do not activate production writes or real file reads.
