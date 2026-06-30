# Curriculum Builder Next-Phase Decision Note

## Purpose

This document records the next-phase decision point for Curriculum Builder / Curriculum Resource Registry work. The current planning stack is documentation/status-only.

This note does not start implementation. Future implementation requires explicit approval through a later PR.

## Current Planning Stack Status

The following planning artifacts exist:

- Local-first foundation plan
- Source storage strategy
- Metadata-only registry plan
- Field inventory
- Safety/status values
- Manual-first workflow
- Metadata-only backup/export planning
- Local validator planning
- Placeholder metadata shape
- Implementation approval gate
- Planning stack summary

These artifacts define boundaries and future vocabulary only. They do not create active registry behavior.

## Recommended Next-Phase Decision

Default recommendation: **pause implementation**.

Use the planning stack as a reference point. Only continue with a next PR if the next path is explicitly selected. Do not drift into schema/data/validator/runtime work accidentally.

## Allowed Next Paths

| Path | What it may add | What it must not activate | Approval level |
| --- | --- | --- | --- |
| Continue documentation/status hardening | Summaries, audit notes, non-activation notes, or planning cross-references | Schema, data files, commands, validators, or runtime behavior | current docs/status pattern |
| schema planning only | A prose schema decision note | Active schema files, migrations, database tables, or registry data | explicit approval required |
| fake placeholder fixture planning only | Documentation of what fake fixtures could look like | Fixture files or registry files | explicit approval required |
| local validator planning only | Refined future validator expectations | A validator or command | explicit approval required |
| metadata export/import planning only | Refined future metadata-only backup/export design | Scripts, files, bundles, or write behavior | explicit approval required |
| Teacher Workstation reference planning only | Documentation of how lesson planning might reference registry metadata later | Lesson-planning runtime behavior or generation | explicit approval required |
| Stop Curriculum Builder work for now | Leave current docs/status stack as-is and return to another repo priority | New Curriculum Builder behavior | safe default |

## Blocked Without Explicit Approval

- active schema files
- database tables
- migrations
- registry JSON/CSV/YAML files
- fake registry data files
- real registry records
- sample curriculum records
- validators
- new commands
- dashboard sections
- entry forms
- import/export scripts
- backup scripts
- archive bundles
- file caches
- raw file copying
- Drive mirroring
- NAS mirroring
- iCloud mirroring
- file reads
- hashing
- scanning
- indexing
- OCR
- embeddings
- vector search
- APIs
- OAuth
- network calls
- automation
- background jobs
- schedulers
- review workflows
- approval workflows
- real review notes
- generated lesson briefs
- generated lesson drafts
- lesson generation
- student data
- live integrations

## Decision Questions for the Next PR

1. Is the next PR documentation/status only?
2. Does it create any file that could be mistaken for active registry data?
3. Does it add or change a command?
4. Does it affect dashboard check counts?
5. Does it read files outside the repo planning docs?
6. Does it introduce any network/API/OAuth behavior?
7. Does it create any sample real curriculum resource?
8. Does it process or store student data?
9. Does it generate lesson content or review notes?
10. Is rollback simple and auditable?
11. Are existing PASS/WARN/FAIL semantics preserved?
12. Is the full PR lifecycle still included?

## Safe Default

If no explicit next implementation path is approved, keep Curriculum Builder parked at planning/status readiness.

Return to lesson-planning readiness, Chief of Staff status hardening, dashboard documentation, or another small local-first docs/status PR. Do not create schema/data/runtime behavior by implication.

## Relationship to Teacher Workstation

Teacher Workstation may use the Curriculum Builder planning stack later. No Teacher Workstation runtime behavior changes in this PR.

No lesson-planning registry reference is activated. No lesson generation is activated.

## Relationship to Chief of Staff

Chief of Staff continues to report existing planning/status readiness. Chief of Staff does not own raw curriculum files.

Chief of Staff does not scan, index, validate real registry records, call APIs, back up files, or generate content. Any future Chief of Staff behavior beyond status reporting requires explicit approval.

## Explicit Non-Activation

This note does not add:

- no active schema
- no database tables
- migrations
- no registry data files
- no fake registry data files
- no real registry records
- backup scripts
- export scripts
- archive bundles
- file caches
- raw file copying
- Drive mirroring
- NAS mirroring
- iCloud mirroring
- no active validators
- entry forms
- no new commands
- no dashboard sections
- review workflows
- approval workflows
- real review notes
- automated safety classifiers
- importers
- scanners
- crawlers
- parsers
- indexers
- no file reads
- no hashing
- no scanning
- no indexing
- no OCR
- no embeddings
- no vector search
- no APIs
- no OAuth
- no network calls
- no automation
- no background jobs
- no schedulers
- no generated lesson briefs
- no generated lesson drafts
- no lesson generation
- no student data
- no live integrations
