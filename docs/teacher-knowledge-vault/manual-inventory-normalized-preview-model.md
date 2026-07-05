# Teacher Knowledge Vault — Manual Inventory Normalized Preview Model

Last updated: 2026-07-04

```text
Status: preview-only normalized candidate model
Fixture: assistant/teacher-knowledge-vault/m7c/fake-normalized-preview-candidates.json
```

## Purpose

Defines preview-only normalized outputs from valid manual inventory records. Preview objects are **not catalog records** and must not be used as proof that real files exist.

## Candidate Types

| Type | Description |
| --- | --- |
| `SourceInventoryCandidate` | Sanitized source inventory preview |
| `ResourceCandidate` | Resource identity preview |
| `RepresentationCandidate` | Representation identity preview |
| `SourceItemCandidate` | Source item label preview |
| `ReviewQueuePreview` | Review routing preview |
| `SourceReconciliationPreview` | Drive/Canvas/NAS reconciliation preview |
| `EventLogPreview` | Event log entry preview |

## Required Preview Fields

Every preview object includes:

| Field | Requirement |
| --- | --- |
| `preview_id` | Fake preview identifier |
| `source_manual_inventory_id` | Originating M7b record |
| `source_label` | Sanitized label only |
| `candidate_type` | One of the types above |
| `status` | Preview status (e.g. `preview_only`) |
| `review_requirement` | Review state if applicable |
| `blocked_actions` | Runtime actions blocked |
| `runtime_imported` | `false` |
| `runtime_connected` | `false` |
| `runtime_ingested` | `false` |

## Policy Mapping

| M7b policy | Preview behavior |
| --- | --- |
| `10_TEACHER_ONLY` | `teacher_only_restricted_preview` — restricted-indexable only |
| `99_DO_NOT_SCAN` | Blocked from normal mapping; no index/discover preview |
| `only_in_canvas` / `only_in_drive` / `drive_and_canvas` | `SourceReconciliationPreview` |
| `notebooklm_planning` / `gemini_planning` | Planning source candidate preview |
