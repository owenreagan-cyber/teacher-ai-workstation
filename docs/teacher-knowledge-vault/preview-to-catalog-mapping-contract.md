# Teacher Knowledge Vault — Preview-to-Catalog Mapping Contract

Last updated: 2026-07-04

```text
Status: future-only mapping contract — mapping not execution
Fixture: assistant/teacher-knowledge-vault/m7d/fake-preview-to-catalog-mapping.json
Mapping contract: future_only_not_execution
```

## Mapping (Future Only)

| M7c Preview Type | Future Catalog Record |
| --- | --- |
| `SourceInventoryCandidate` | Source record |
| `ResourceCandidate` | Resource record |
| `RepresentationCandidate` | Representation record |
| `SourceItemCandidate` | SourceItem record |
| `SourceReconciliationPreview` | SourceReconciliation record |
| `ReviewQueuePreview` | ReviewQueueItem |
| `EventLogPreview` | EventLogEntry |

## Contract Rules

- Mapping is not execution — M7d documents the contract only
- Preview IDs are not final record IDs — import must generate new local IDs
- Blocked records must not map
- `99_DO_NOT_SCAN` records must not map into searchable/indexable records
- Teacher-only records must map with restricted-indexing flags only
- Student-data-risk records must not map
- Rejected M7c rows must not map
