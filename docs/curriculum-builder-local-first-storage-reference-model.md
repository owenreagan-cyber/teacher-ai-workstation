# Curriculum Builder — Local-First Storage and Reference Model

Last updated: 2026-07-02

```text
Status: planning_only
Classification: architecture reference — not runtime implementation
Production registry writes: blocked
Real metadata intake: blocked
```

## Purpose

Clarify how curriculum **files** and curriculum **metadata** relate in the Teacher AI Workstation local-first architecture. This supports production registry governance without scanning, copying, or ingesting real curriculum.

## Core Principle

```text
Large curriculum files stay where Owen already stores them.
The workstation stores metadata, references, status, and orchestration — not paid duplicate copies of curriculum content.
```

## Storage Layers (Planning)

| Layer | What lives here | Examples | Active today? |
| --- | --- | --- | --- |
| **Source files (external)** | Real curriculum files | Google Drive, NAS, iCloud, local folders | Outside repo — not scanned |
| **Workstation metadata (future production)** | Titles, labels, review state, manual source references | Future production registry path (Owen decision pending) | **Blocked** |
| **Repo fake fixtures** | Planning validation only | v0.2 samples, source readiness fake inventory | Read-only proof |
| **Chief of Staff** | Status, orchestration, read-only commands | `--curriculum-registry-*`, governance status | Active — no file database |
| **Optional future metadata DB** | Indexed metadata (e.g. Supabase) | Not chosen; not required for raw file storage | **Not active** |

## What the Registry Stores (When Approved)

Metadata and **manual** source references only:

- Resource title/label Owen enters
- Subject, unit, lesson labels
- Review state
- Source reference string (path or URL Owen types — no auto-resolution)

## What the Registry Does Not Store

- PDF/DOCX/slide bodies
- Worksheet or answer-key text
- Scanned or OCR content
- Embeddings or vector indexes
- Student names, rosters, grades

## Source-System Posture (Manual-First)

| System | v1 production workflow | Notes |
| --- | --- | --- |
| Manual entry | First when implementation approved | Owen-typed metadata only |
| Local folder labels | Later; separate mission | Path metadata only — no scanning |
| Google Drive | Blocked until separate approval | Reference label only — no API |
| NAS / iCloud | Blocked until separate approval | Reference label only — no API |
| Canvas | Blocked until separate approval | Export reference only — no API |

## Supabase / Cloud Metadata DB

Supabase or similar is **optional and future**. It is not required for raw curriculum file storage. No Supabase client, credentials, or schema is activated by governance foundation work.

## Related Documents

| Document | Role |
| --- | --- |
| `docs/curriculum-source-readiness-and-intake-boundary-plan.md` | Fake readiness vs real intake |
| `docs/curriculum-builder-production-registry-path-options.md` | Path options |
| `docs/curriculum-builder-registry-authority-map.md` | Authority surfaces |

## Non-Activation

No folder scanning, APIs, OAuth, file copying, embeddings, or student data.
