# Teacher Knowledge Vault — Catalog Schema Direction (M1)

Last updated: 2026-07-04

```text
Status: schema direction only — SQL draft not executed
No SQLite database file created in M1
```

## Entity Model

| Entity | Role |
| --- | --- |
| Resource | Canonical curriculum object |
| Representation | Resource form at a source |
| Source | Drive, NAS, Canvas, local staging, etc. |
| SourceItem | Connector-normalized file record |
| ResourceVersion | Time-ordered variant |
| FingerprintSet | Identity/similarity signals |
| ResourceRelationship | duplicate, version-of, derived-from |
| Collection | Unit/pacing grouping |
| ReviewQueueItem | Teacher inbox state |
| EventLogEntry | Append-only audit event |
| SearchIndexRecord | Fake index row (M1 fixture only) |
| GovernanceStatus | Policy/compliance snapshot |

## SQL Schema Draft (Not Executed)

```sql
-- DRAFT ONLY — M1 does not create this database
-- classification: fake_local_planning_only

CREATE TABLE resources (
  resource_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  subject_slug TEXT,
  curriculum_program TEXT,
  audience TEXT CHECK (audience IN ('teacher_only', 'student_facing', 'mixed_planning_only')),
  taxonomy_folder TEXT,
  metadata_only INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE sources (
  source_id TEXT PRIMARY KEY,
  source_type TEXT NOT NULL,
  label TEXT NOT NULL,
  connector_status TEXT NOT NULL DEFAULT 'blocked'
);

CREATE TABLE source_items (
  source_item_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  placeholder_uri TEXT NOT NULL,
  scan_policy TEXT CHECK (scan_policy IN ('normal', 'restricted_indexable', 'do_not_scan'))
);

CREATE TABLE representations (
  representation_id TEXT PRIMARY KEY,
  resource_id TEXT NOT NULL REFERENCES resources(resource_id),
  source_item_id TEXT REFERENCES source_items(source_item_id),
  representation_type TEXT NOT NULL,
  label TEXT NOT NULL
);

CREATE TABLE resource_versions (
  version_id TEXT PRIMARY KEY,
  resource_id TEXT NOT NULL REFERENCES resources(resource_id),
  version_label TEXT NOT NULL
);

CREATE TABLE fingerprint_sets (
  fingerprint_set_id TEXT PRIMARY KEY,
  source_item_id TEXT REFERENCES source_items(source_item_id),
  binary_hash_placeholder TEXT,
  filename_fingerprint_placeholder TEXT
);

CREATE TABLE resource_relationships (
  relationship_id TEXT PRIMARY KEY,
  from_resource_id TEXT NOT NULL,
  to_resource_id TEXT NOT NULL,
  relationship_type TEXT CHECK (relationship_type IN ('duplicate_candidate', 'version_candidate', 'derived_from', 'publishes_to'))
);

CREATE TABLE collections (
  collection_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  collection_type TEXT
);

CREATE TABLE review_queue_items (
  queue_item_id TEXT PRIMARY KEY,
  resource_id TEXT,
  review_state TEXT NOT NULL,
  requires_teacher_approval INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE event_log_entries (
  event_id TEXT PRIMARY KEY,
  event_type TEXT NOT NULL,
  runtime_executed INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE search_index_records (
  index_record_id TEXT PRIMARY KEY,
  resource_id TEXT NOT NULL,
  search_label TEXT NOT NULL,
  teacher_mode_only INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE governance_status (
  status_id TEXT PRIMARY KEY,
  m0_freeze_accepted INTEGER NOT NULL DEFAULT 1,
  real_files_processed INTEGER NOT NULL DEFAULT 0
);
```

## Fake Fixture Mapping

JSON fixtures under `assistant/teacher-knowledge-vault/m1/` mirror this schema without creating SQLite.

## Rules

- Duplicates are **candidates** — not auto-merged
- Versions are **related** — not overwritten
- `10_TEACHER_ONLY` → `restricted_indexable` scan policy
- `99_DO_NOT_SCAN` → `do_not_scan` — never in normal review or search
