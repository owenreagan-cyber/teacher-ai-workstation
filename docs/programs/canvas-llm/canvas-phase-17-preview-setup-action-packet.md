# Canvas LLM Phase 17: Preview-Only Canvas Setup Action Packet

## Status

Phase 17 converts the Phase 16 relationship map into a practical, preview-only Canvas setup action packet.

This phase reads ignored Phase 14B local metadata and the tracked Phase 16 relationship map. It performs no Canvas API calls, no live fetches, no Canvas writes, no renames, no moves, no uploads, no publish changes, no deletes, no copies, no file downloads, no file content reads, no page body ingestion, no announcement body ingestion, no assignment body ingestion, no student data access, no database writes, no RAG, no embeddings, no local model execution, and no lesson generation.

Raw fetched metadata remains ignored under `.local/canvas-llm/approved-course-metadata/...` and is not committed.

## Source Inputs

```text
.local/canvas-llm/approved-course-metadata/manifest.json
docs/programs/canvas-llm/canvas-phase-16-preview-relationship-map.md
```

## Setup Packet Summary

| Subject | Priority | Template Course | Target Course | Template Year | Files | Folders | Modules | Module Items | Pages | Assignments | Preview Relationship Total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Math | highest | 19428 | 26404 | 2024-2025 | 351 | 17 | 4 | 330 | 39 | 150 | 891 |
| Reading/Spelling | highest | 19419 | 26442 | 2024-2025 | 326 | 40 | 8 | 65 | 39 | 173 | 651 |
| Language Arts | high | 19426 | 26495 | 2024-2025 | 143 | 13 | 5 | 161 | 38 | 56 | 416 |
| History | medium | 21934 | 26493 | 2025-2026 | 114 | 45 | 12 | 150 | 40 | 52 | 413 |
| Science | medium | 21970 | 26496 | 2025-2026 | 59 | 19 | 7 | 46 | 40 | 35 | 206 |
| Homeroom/Newsletter | high | 19424 | 26427 | 2024-2025 | 40 | 9 | 3 | 46 | 42 | 0 | 140 |

## Subject-by-Subject Preview Setup Actions

### Math

- Template course: `19428` (`2024-2025`)
- Target course: `26404` (`2026-2027`)
- Priority: `highest`
- Notes: Largest historical relationship set; likely first academic setup candidate.
- Preview scale: 17 folders, 351 files, 4 modules, 330 module items, 39 pages, 150 assignment relationships.

Preview actions:

- Review current target course shell before any write gate.
- Prepare proposed folder groups from historical folder metadata.
- Prepare proposed module shells from historical module metadata.
- Prepare page placement preview from historical page metadata.
- Prepare file relationship groups from historical file and folder metadata.
- Prepare module item relationship preview for pages/files/assignments.
- Prepare assignment relationship references only; do not ingest assignment bodies.

Blocked before a later write gate:

- No Canvas folder creation.
- No Canvas module creation.
- No Canvas page creation or editing.
- No Canvas file upload or download.
- No Canvas rename, move, delete, copy, or publish action.
- No body/content ingestion.

### Reading/Spelling

- Template course: `19419` (`2024-2025`)
- Target course: `26442` (`2026-2027`)
- Priority: `highest`
- Notes: Shared Reading/Spelling course; preserve RM4 and SPELL prefix distinction.
- Preview scale: 40 folders, 326 files, 8 modules, 65 module items, 39 pages, 173 assignment relationships.

Preview actions:

- Review current target course shell before any write gate.
- Prepare proposed folder groups from historical folder metadata.
- Prepare proposed module shells from historical module metadata.
- Prepare page placement preview from historical page metadata.
- Prepare file relationship groups from historical file and folder metadata.
- Prepare module item relationship preview for pages/files/assignments.
- Prepare assignment relationship references only; do not ingest assignment bodies.
- Preserve RM4 and SPELL as separate canonical prefixes inside the shared Canvas course.

Blocked before a later write gate:

- No Canvas folder creation.
- No Canvas module creation.
- No Canvas page creation or editing.
- No Canvas file upload or download.
- No Canvas rename, move, delete, copy, or publish action.
- No body/content ingestion.

### Language Arts

- Template course: `19426` (`2024-2025`)
- Target course: `26495` (`2026-2027`)
- Priority: `high`
- Notes: Strong module-item structure and ELA page/file relationship depth.
- Preview scale: 13 folders, 143 files, 5 modules, 161 module items, 38 pages, 56 assignment relationships.

Preview actions:

- Review current target course shell before any write gate.
- Prepare proposed folder groups from historical folder metadata.
- Prepare proposed module shells from historical module metadata.
- Prepare page placement preview from historical page metadata.
- Prepare file relationship groups from historical file and folder metadata.
- Prepare module item relationship preview for pages/files/assignments.
- Prepare assignment relationship references only; do not ingest assignment bodies.

Blocked before a later write gate:

- No Canvas folder creation.
- No Canvas module creation.
- No Canvas page creation or editing.
- No Canvas file upload or download.
- No Canvas rename, move, delete, copy, or publish action.
- No body/content ingestion.

### History

- Template course: `21934` (`2025-2026`)
- Target course: `26493` (`2026-2027`)
- Priority: `medium`
- Notes: Best History template; no current assignments expected, so prioritize structure clarity.
- Preview scale: 45 folders, 114 files, 12 modules, 150 module items, 40 pages, 52 assignment relationships.

Preview actions:

- Review current target course shell before any write gate.
- Prepare proposed folder groups from historical folder metadata.
- Prepare proposed module shells from historical module metadata.
- Prepare page placement preview from historical page metadata.
- Prepare file relationship groups from historical file and folder metadata.
- Prepare module item relationship preview for pages/files/assignments.
- Prepare assignment relationship references only; do not ingest assignment bodies.

Blocked before a later write gate:

- No Canvas folder creation.
- No Canvas module creation.
- No Canvas page creation or editing.
- No Canvas file upload or download.
- No Canvas rename, move, delete, copy, or publish action.
- No body/content ingestion.

### Science

- Template course: `21970` (`2025-2026`)
- Target course: `26496` (`2026-2027`)
- Priority: `medium`
- Notes: Only approved Science model; sufficient page/module/folder structure.
- Preview scale: 19 folders, 59 files, 7 modules, 46 module items, 40 pages, 35 assignment relationships.

Preview actions:

- Review current target course shell before any write gate.
- Prepare proposed folder groups from historical folder metadata.
- Prepare proposed module shells from historical module metadata.
- Prepare page placement preview from historical page metadata.
- Prepare file relationship groups from historical file and folder metadata.
- Prepare module item relationship preview for pages/files/assignments.
- Prepare assignment relationship references only; do not ingest assignment bodies.

Blocked before a later write gate:

- No Canvas folder creation.
- No Canvas module creation.
- No Canvas page creation or editing.
- No Canvas file upload or download.
- No Canvas rename, move, delete, copy, or publish action.
- No body/content ingestion.

### Homeroom/Newsletter

- Template course: `19424` (`2024-2025`)
- Target course: `26427` (`2026-2027`)
- Priority: `high`
- Notes: Newsletter setup is separate from academic scoring; useful for parent-facing reminders.
- Preview scale: 9 folders, 40 files, 3 modules, 46 module items, 42 pages, 0 assignment relationship.

Preview actions:

- Review current target course shell before any write gate.
- Prepare proposed folder groups from historical folder metadata.
- Prepare proposed module shells from historical module metadata.
- Prepare page placement preview from historical page metadata.
- Prepare file relationship groups from historical file and folder metadata.
- Prepare module item relationship preview for pages/files/assignments.
- Keep newsletter/reminder packet separate from academic curriculum setup.

Blocked before a later write gate:

- No Canvas folder creation.
- No Canvas module creation.
- No Canvas page creation or editing.
- No Canvas file upload or download.
- No Canvas rename, move, delete, copy, or publish action.
- No body/content ingestion.

## Cross-Course Setup Order

Recommended preview-only setup order:

1. Math and Reading/Spelling first, because these have the largest academic relationship sets and likely drive daily classroom operations.
2. Language Arts next, because it has strong module-item structure and should align with writing/language routines.
3. Homeroom/Newsletter in parallel, but in a separate newsletter/reminder lane.
4. History and Science after core daily courses, unless classroom calendar requirements make one of them urgent.
5. Run a human review before any future Canvas write gate.

## Folder / File Grouping Priorities

- Start with folder metadata and file metadata only.
- Group by historical course, subject, and likely unit/module relationship.
- Do not infer file content from names beyond safe metadata-level planning.
- Do not download files.
- Do not commit raw file metadata.

## Module Shell Priorities

- Use historical modules as preview candidates for current module shells.
- Use module item counts to identify where pages/files/assignments likely connect.
- Treat module shell creation as blocked until a later explicit Canvas write gate.

## Page Placement Priorities

- Use pages metadata only to preview possible module placements.
- Do not read page bodies.
- Do not summarize page bodies.
- Do not use page text for RAG or embeddings.

## Assignment Relationship References

- Use assignments metadata only for relationship mapping.
- Do not ingest assignment bodies.
- Do not recreate assignments yet.
- Treat History and Science assignment-prefix expectations as N/A unless later planning changes them.

## Homeroom / Newsletter Packet

- Keep Homeroom/Newsletter separate from academic course setup.
- Use `19424` as the primary newsletter template and `22254` as a supporting reference.
- Current target is `26427`.
- Do not ingest newsletter page bodies or announcement bodies.
- Future work may need a separate approval gate if newsletter layout/body review becomes necessary.

## Explicitly Blocked Actions

- Canvas API calls
- Live fetches
- Canvas writes
- Canvas renames
- Canvas moves
- Canvas uploads
- Canvas deletes
- Canvas copy/import actions
- Canvas publish changes
- File downloads
- File content reads
- Page body ingestion
- Announcement body ingestion
- Assignment body ingestion
- Student data access
- Users, enrollments, rosters, submissions, grades, analytics, messages, discussion replies, or quiz responses
- Knowledge DB writes
- Runtime DB writes
- Production writes
- Canonical catalog writes
- RAG
- Embeddings
- Local model/Ollama execution
- Lesson generation
- Tracked school Canvas URL
- Tracked tokens
- Committed `.local/...` raw metadata

## Recommended Next Phase

```text
Canvas LLM Phase 18: Canvas Setup Write Gate Readiness Review
```

Phase 18 should decide whether the repo is ready for a tightly constrained write gate, or whether another preview-only refinement is needed first. Any write gate must require explicit approval, target only approved current 2026-2027 course IDs, and start with the smallest safe Canvas action.
