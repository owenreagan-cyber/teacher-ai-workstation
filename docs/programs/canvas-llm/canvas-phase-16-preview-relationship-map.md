# Canvas LLM Phase 16: Preview-Only Canvas Module/File/Page Relationship Map

## Status

Phase 16 creates a preview-only relationship map from historical template courses to current 2026-2027 Canvas target courses.

This phase reads ignored Phase 14B local metadata only. It performs no Canvas API calls, no live fetches, no Canvas writes, no renames, no moves, no uploads, no publish changes, no file downloads, no file content reads, no page body ingestion, no announcement body ingestion, no assignment body ingestion, no student data access, no database writes, no RAG, no embeddings, no local model execution, and no lesson generation.

Raw fetched metadata remains ignored under `.local/canvas-llm/approved-course-metadata/...` and is not committed.

## Preview Relationship Map

| Subject | Template Course | Target Course | Template Year | Target Year | Files | Folders | Modules | Module Items | Pages | Assignments | Relationship Total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Math | 19428 | 26404 | 2024-2025 | 2026-2027 | 351 | 17 | 4 | 330 | 39 | 150 | 891 |
| Reading/Spelling | 19419 | 26442 | 2024-2025 | 2026-2027 | 326 | 40 | 8 | 65 | 39 | 173 | 651 |
| Language Arts | 19426 | 26495 | 2024-2025 | 2026-2027 | 143 | 13 | 5 | 161 | 38 | 56 | 416 |
| History | 21934 | 26493 | 2025-2026 | 2026-2027 | 114 | 45 | 12 | 150 | 40 | 52 | 413 |
| Science | 21970 | 26496 | 2025-2026 | 2026-2027 | 59 | 19 | 7 | 46 | 40 | 35 | 206 |
| Homeroom/Newsletter | 19424 | 26427 | 2024-2025 | 2026-2027 | 40 | 9 | 3 | 46 | 42 | 0 | 140 |

## Current Target Course Setup Order Preview

### Math

- Historical template: `19428` (`2024-2025`)
- Current target: `26404` (`2026-2027`)
- Reason: Highest Math structure score and strongest file/module-item depth.
- Preview-only relationship total: `891`
- Current target relationship total: `1`

Suggested preview order:

- 1. Preview folder structure from historical template.
- 2. Preview file inventory and likely folder destinations.
- 3. Preview module shell order.
- 4. Preview module item relationships to pages/files/assignments.
- 5. Preview page inventory and likely module placement.
- 6. Preview assignment relationship metadata without body ingestion.

Blocked in Phase 16:

- Do not write to Canvas.
- Do not rename, move, upload, delete, publish, or copy anything in Canvas.
- Do not download files or read file contents.
- Do not ingest page, announcement, assignment, or file bodies.

### Reading/Spelling

- Historical template: `19419` (`2024-2025`)
- Current target: `26442` (`2026-2027`)
- Reason: Strongest shared RM4/SPELL historical structure.
- Preview-only relationship total: `651`
- Current target relationship total: `1`

Suggested preview order:

- 1. Preview folder structure from historical template.
- 2. Preview file inventory and likely folder destinations.
- 3. Preview module shell order.
- 4. Preview module item relationships to pages/files/assignments.
- 5. Preview page inventory and likely module placement.
- 6. Preview assignment relationship metadata without body ingestion.

Blocked in Phase 16:

- Do not write to Canvas.
- Do not rename, move, upload, delete, publish, or copy anything in Canvas.
- Do not download files or read file contents.
- Do not ingest page, announcement, assignment, or file bodies.

### Language Arts

- Historical template: `19426` (`2024-2025`)
- Current target: `26495` (`2026-2027`)
- Reason: Strongest ELA historical module-item relationship depth.
- Preview-only relationship total: `416`
- Current target relationship total: `1`

Suggested preview order:

- 1. Preview folder structure from historical template.
- 2. Preview file inventory and likely folder destinations.
- 3. Preview module shell order.
- 4. Preview module item relationships to pages/files/assignments.
- 5. Preview page inventory and likely module placement.
- 6. Preview assignment relationship metadata without body ingestion.

Blocked in Phase 16:

- Do not write to Canvas.
- Do not rename, move, upload, delete, publish, or copy anything in Canvas.
- Do not download files or read file contents.
- Do not ingest page, announcement, assignment, or file bodies.

### History

- Historical template: `21934` (`2025-2026`)
- Current target: `26493` (`2026-2027`)
- Reason: Strongest History structure, folders, modules, and module-item depth.
- Preview-only relationship total: `413`
- Current target relationship total: `1`

Suggested preview order:

- 1. Preview folder structure from historical template.
- 2. Preview file inventory and likely folder destinations.
- 3. Preview module shell order.
- 4. Preview module item relationships to pages/files/assignments.
- 5. Preview page inventory and likely module placement.
- 6. Preview assignment relationship metadata without body ingestion.

Blocked in Phase 16:

- Do not write to Canvas.
- Do not rename, move, upload, delete, publish, or copy anything in Canvas.
- Do not download files or read file contents.
- Do not ingest page, announcement, assignment, or file bodies.

### Science

- Historical template: `21970` (`2025-2026`)
- Current target: `26496` (`2026-2027`)
- Reason: Only approved historical Science model and sufficient page/module structure.
- Preview-only relationship total: `206`
- Current target relationship total: `1`

Suggested preview order:

- 1. Preview folder structure from historical template.
- 2. Preview file inventory and likely folder destinations.
- 3. Preview module shell order.
- 4. Preview module item relationships to pages/files/assignments.
- 5. Preview page inventory and likely module placement.
- 6. Preview assignment relationship metadata without body ingestion.

Blocked in Phase 16:

- Do not write to Canvas.
- Do not rename, move, upload, delete, publish, or copy anything in Canvas.
- Do not download files or read file contents.
- Do not ingest page, announcement, assignment, or file bodies.

### Homeroom/Newsletter

- Historical template: `19424` (`2024-2025`)
- Current target: `26427` (`2026-2027`)
- Reason: Best Homeroom/newsletter structure score; keep separate from academic scoring.
- Preview-only relationship total: `140`
- Current target relationship total: `1`

Suggested preview order:

- 1. Preview folder structure from historical template.
- 2. Preview file inventory and likely folder destinations.
- 3. Preview module shell order.
- 4. Preview module item relationships to pages/files/assignments.
- 5. Preview page inventory and likely module placement.

Blocked in Phase 16:

- Do not write to Canvas.
- Do not rename, move, upload, delete, publish, or copy anything in Canvas.
- Do not download files or read file contents.
- Do not ingest page, announcement, assignment, or file bodies.

## Per-Course Relationship Metadata Availability

| Course ID | Role | Year | Subject | Prefixes | Files | Folders | Modules | Module Items | Pages | Assignments | Announcements |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 19422 | historical_academic_course | 2024-2025 | History A | N/A | 29 | 10 | 3 | 47 | 38 | 34 | 0 |
| 19423 | historical_academic_course | 2024-2025 | History B | N/A | 38 | 7 | 3 | 47 | 39 | 36 | 0 |
| 19426 | historical_academic_course | 2024-2025 | Language Arts | ELA4 | 143 | 13 | 5 | 161 | 38 | 56 | 0 |
| 19428 | historical_academic_course | 2024-2025 | Math | SM5 | 351 | 17 | 4 | 330 | 39 | 150 | 0 |
| 19419 | historical_academic_course | 2024-2025 | Reading | RM4, SPELL | 326 | 40 | 8 | 65 | 39 | 173 | 0 |
| 19424 | historical_homeroom_newsletter_course | 2024-2025 | Homeroom | Newsletter | 40 | 9 | 3 | 46 | 42 | 0 | 0 |
| 21934 | historical_academic_course | 2025-2026 | History | N/A | 114 | 45 | 12 | 150 | 40 | 52 | 0 |
| 21944 | historical_academic_course | 2025-2026 | Language Arts | ELA4 | 137 | 52 | 5 | 70 | 41 | 52 | 0 |
| 21957 | historical_academic_course | 2025-2026 | Math | SM5 | 209 | 37 | 3 | 174 | 56 | 150 | 0 |
| 21919 | historical_academic_course | 2025-2026 | Reading | RM4, SPELL | 137 | 24 | 5 | 48 | 42 | 172 | 0 |
| 21970 | historical_academic_course | 2025-2026 | Science | N/A | 59 | 19 | 7 | 46 | 40 | 35 | 0 |
| 22254 | historical_homeroom_newsletter_course | 2025-2026 | Homeroom | Newsletter | 11 | 4 | 26 | 42 | 44 | 0 | 0 |
| 26427 | current_homeroom_newsletter_course | 2026-2027 | Homeroom | Newsletter | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| 26493 | current_operational_course | 2026-2027 | History | N/A | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| 26495 | current_operational_course | 2026-2027 | Language Arts | ELA4 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| 26404 | current_operational_course | 2026-2027 | Math | SM5 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| 26442 | current_operational_course | 2026-2027 | Reading | RM4, SPELL | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| 26496 | current_operational_course | 2026-2027 | Science | N/A | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| 24399 | demo_sandbox_course | demo | Math Automation Sandbox | SM5 | 220 | 20 | 3 | 185 | 48 | 115 | 0 |

## Homeroom / Newsletter Boundary

Homeroom/newsletter mapping is previewed separately from academic course mapping.

- Current Homeroom target: `26427`
- Recommended Homeroom/newsletter template: `19424`
- Supporting Homeroom/newsletter reference: `22254`
- Phase 16 does not evaluate Homeroom as academic curriculum.
- Phase 16 does not ingest newsletter page bodies or announcement bodies.

## Known Pattern

Announcements metadata is zero across the fetched course set. Treat this as a known metadata pattern until a later phase explicitly investigates whether newsletter/reminder content lives primarily in pages, modules, or another Canvas surface.

## Safety Boundaries Preserved

- Phase 16 reads local ignored metadata only.
- Phase 16 does not fetch from Canvas.
- Phase 16 does not write to Canvas.
- Phase 16 does not rename, move, upload, delete, publish, or copy Canvas objects.
- Phase 16 does not download files.
- Phase 16 does not read file contents.
- Phase 16 does not ingest page, announcement, assignment, or file bodies.
- Phase 16 does not access student data, rosters, grades, submissions, analytics, messages, discussion replies, users, or enrollments.
- Phase 16 does not write to a knowledge DB, runtime DB, production system, or canonical catalog.
- Phase 16 does not run RAG, embeddings, local model/Ollama, or lesson generation.
- Phase 16 does not track the school Canvas URL or tokens.

## Recommended Next Phase

```text
Canvas LLM Phase 17: Preview-Only Canvas Setup Action Packet
```

Phase 17 should convert this relationship map into a preview-only setup action packet: proposed folders, module shells, page placements, file relationship groups, and subject-by-subject setup order. It should still block writes, downloads, body ingestion, and raw metadata commits.
