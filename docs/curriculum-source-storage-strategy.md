# Curriculum Source Storage Strategy

## Purpose

This document defines where curriculum resources should live and how Teacher Workstation should reference them later. It expands the Curriculum Builder local-first foundation with a source storage strategy only.

This is a planning/status document only. It does not activate scanning, indexing, syncing, importing, OCR, embeddings, APIs, OAuth, network calls, automation, or lesson generation.

## Source Storage Decision

Large curriculum files remain in existing source storage. Teacher Workstation stores metadata, references, hashes, status, and relationships. Teacher Workstation does not become the paid hosted storage home for every raw file.

There is no Supabase Storage requirement for raw curriculum files and no paid storage dependency for this strategy.

## Supported Source Storage Types

### Google Drive

**Role:**

- active school/curriculum working library
- resources currently used in teaching
- shared folders and school-compatible workflows
- future manually referenced Drive links or IDs

**Allowed future metadata:**

- `source_system`: `google_drive`
- `source_label`
- `source_path_or_url`
- `drive_file_id`, if manually provided in the future
- `modified_at`, if manually recorded in the future
- `content_hash`, if explicitly approved later

**Current boundaries:**

- no Google Drive API activation
- no OAuth
- no Drive crawler
- no automatic Drive scanning
- no automatic folder indexing
- no network calls

### NAS

**Role:**

- archive
- backup
- large curriculum vault
- long-term storage for textbooks, worksheets, tests, study guides, presentations, and source packs

**Allowed future metadata:**

- `source_system`: `nas`
- `source_label`
- `source_path_or_url`
- `local_mount_hint`, if manually documented
- `archive_status`
- `backup_status`

**Current boundaries:**

- no NAS crawler
- no SMB/NFS integration
- no folder scanning
- no file indexing
- no background sync

### iCloud

**Role:**

- optional convenience sync
- personal working copies
- temporary access bridge between devices

**Allowed future metadata:**

- `source_system`: `icloud`
- `source_label`
- `source_path_or_url`
- `sync_note`

**Current boundaries:**

- no iCloud crawler
- no automatic sync assumptions
- no indexing
- no file import

### Local Folders

**Role:**

- repo-adjacent planning examples
- manually managed local references
- local-first development/testing fixtures only when explicitly approved

**Allowed future metadata:**

- `source_system`: `local_folder`
- `source_label`
- `source_path_or_url`
- `relative_path`, if safe and repo-local
- `notes`

**Current boundaries:**

- no recursive local folder scanning
- no document scanning
- no indexing user curriculum folders
- no generated lesson output

## Source-Reference Model

The future registry should use a source-reference model: reference files in place instead of copying raw files into app-owned storage.

Example reference and metadata fields:

| Field | Purpose |
| --- | --- |
| `source_system` | Google Drive, NAS, iCloud, or local folders. |
| `source_label` | Human-readable source label. |
| `source_path_or_url` | Stable reference to the source location. |
| `source_owner` | Ownership or stewardship label for review. |
| `source_scope` | Active, archive, convenience sync, or local reference scope. |
| `resource_type` | Worksheet, test, study guide, presentation, textbook section, etc. |
| `title` | Resource title for discovery. |
| `subject` | Subject label. |
| `grade` | Grade or level label. |
| `unit` | Unit label. |
| `lesson` | Lesson label. |
| `review_status` | Human review state. |
| `teacher_only` | Teacher-only marker. |
| `student_facing` | Student-facing marker when approved. |
| `notes` | Teacher review notes about the reference. |

This table is planning documentation only. No registry records are created by this PR.

## Raw File Ownership Rules

- **Google Drive** owns active cloud files.
- **NAS** owns archive/vault files.
- **iCloud** owns optional convenience sync copies.
- **Local folders** own local working references.
- **Teacher Workstation** owns metadata/status/reference records only.
- **Chief of Staff** owns status checks and readiness reporting only.
- **Chief of Staff** does not own raw curriculum files.

## Duplicate Storage Avoidance

The system should avoid duplicating every raw file into hosted storage.

**Allowed future exceptions, only if explicitly approved:**

- small repo-local fixtures
- manually created sample metadata
- temporary export artifacts
- backup/export bundles for metadata only
- explicitly approved cache strategy

**Not allowed by default:**

- uploading all curriculum files to Supabase Storage
- copying all Drive files into app storage
- mirroring the NAS into app storage
- creating hidden curriculum file caches
- automatic ingestion pipelines

## Future Manual Registry Flow

A future manual-first flow may look like this:

1. Teacher identifies a resource.
2. Teacher records its source location/reference manually.
3. Teacher adds metadata manually or through an explicitly approved local form later.
4. Teacher marks review/status fields.
5. Teacher Workstation can later reference the registry.
6. Chief of Staff can report whether registry planning/status is present.

This PR does not implement the flow. No file importers, crawlers, or sync jobs are activated.

## Safety Boundaries

Prohibited current capabilities:

- no document scanning
- no folder scanning
- no file indexing
- no OCR
- no embeddings
- no vector database
- no lesson generation
- no generated lesson briefs
- no generated lesson drafts
- no real review notes
- no student data
- no network calls
- no APIs
- no OAuth
- no automation
- no live integrations
- no background jobs
- no scheduler
- no Google Drive API activation
- no NAS crawler
- no iCloud crawler
- no Canvas API activation

## Future Phases

Each phase requires separate explicit approval.

### Phase 0 — Source storage strategy docs only

May add planning docs and read-only status checks.

Must not activate scanning, indexing, sync, import, or integrations.

### Phase 1 — Static registry field planning

May define registry field inventories and safety-flag planning.

Must not create a live schema or validator.

### Phase 2 — Manual sample registry planning

May add fictional or manually authored sample registry planning entries.

Must not read user curriculum files.

### Phase 3 — Metadata-only export/backup planning

May document metadata export/backup boundaries.

Must not copy raw curriculum files into app storage by default.

### Phase 4 — Read-only local status checks

May add static status scripts that verify docs and safety markers only.

Must not scan folders or index files.

### Phase 5 — Future connector planning only, if explicitly approved

May document connector boundaries for Google Drive, NAS, iCloud, or Canvas.

Must not activate OAuth, APIs, network calls, or live integrations.

### Phase 6 — Future local registry implementation, if explicitly approved

May implement a local metadata registry after field planning and safety review.

Must not activate lesson generation, OCR, embeddings, vector search, or background jobs without separate approval.

## Acceptance Criteria

This PR is complete when:

- `docs/curriculum-source-storage-strategy.md` exists and defines Google Drive, NAS, iCloud, and local folders
- the metadata/reference model and source-reference model are explicit
- raw file ownership boundaries are explicit
- no paid duplicate-storage dependency is introduced
- no scanning, indexing, generation, or integration behavior is activated
- `scripts/curriculum-builder-foundation-status.sh` verifies the new doc with read-only PASS/WARN/FAIL checks

## Related Verification Commands

```bash
bash scripts/curriculum-builder-foundation-status.sh
bin/chief-of-staff --curriculum-builder-foundation-status
```
