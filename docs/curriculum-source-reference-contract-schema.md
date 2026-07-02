# Curriculum Source Reference Contract Schema (Program A5)

Last updated: 2026-07-02

```text
Status: documentation/status only — inactive schema draft
Program: A5 — Curriculum Source Reference Contract
Validator: none
Runtime: not active
Crawling: blocked
```

## Purpose

Define how the future registry can reference **where a resource lives** without crawling, opening, scanning, or validating the source.

## Supported Future Source Systems (Planning Only)

| `source_system` | Meaning | Activation |
| --- | --- | --- |
| `google_drive` | Google Drive reference | blocked — no API, no crawl |
| `nas` | NAS archive reference | blocked — no crawl |
| `icloud` | iCloud convenience reference | blocked — no crawl |
| `local_folder` | Local folder reference | blocked — no scan |
| `canvas_export` | Canvas export bundle reference | blocked — no API |
| `manual_reference` | Teacher-entered reference | planning only |

## Field Definitions

| Field | Type (conceptual) | Purpose |
| --- | --- | --- |
| `source_reference_id` | string | Stable fictional ID (`sample-source-*`) |
| `source_system` | enum | See table above |
| `source_label` | string | Human-readable label |
| `source_kind` | enum | file, folder, export_bundle, manual_note |
| `path_or_url_reference` | string | Placeholder URI only (see rules below) |
| `owner_context` | string | Planning context (e.g. `teacher_workstation_planning`) |
| `access_notes` | string | How access would be obtained manually in future |
| `content_hash_future` | string \| null | Reserved for future change detection — not computed |
| `last_verified_future` | string \| null | Reserved — not populated |
| `not_scanned` | boolean | Must be `true` in inactive samples |
| `not_ingested` | boolean | Must be `true` in inactive samples |

## Placeholder Reference Rules

Allowed placeholder schemes:

- `placeholder://curriculum/example-resource`
- `placeholder://source/example-drive-reference`
- `gdrive://placeholder/example-drive-reference`
- `nas://placeholder/example-nas-reference`
- `icloud://placeholder/example-icloud-reference`
- `local://placeholder/example-folder-reference`
- `canvas://placeholder/example-future-reference`

Blocked: real `http://` / `https://` URLs, real Drive URLs, real NAS paths, real iCloud paths, real Canvas course IDs.

## Fictional Sample (Inactive)

```json
{
  "contract_type": "curriculum_source_reference_contract",
  "contract_version": "0.0.0-inactive",
  "metadata_only": true,
  "read_only": true,
  "source_reference_id": "sample-source-drive-001",
  "source_system": "google_drive",
  "source_label": "example-drive-reference",
  "source_kind": "file",
  "path_or_url_reference": "placeholder://source/example-drive-reference",
  "owner_context": "teacher_workstation_planning",
  "access_notes": "Manual future access only — no API or crawl in v0.",
  "content_hash_future": null,
  "last_verified_future": null,
  "not_scanned": true,
  "not_ingested": true
}
```

Canonical inactive file: `assistant/curriculum-builder/metadata-contract/v0/samples/sample-source-reference-001.json`

## Non-Activation

No connectors, crawlers, sync, API, OAuth, or network behavior.
