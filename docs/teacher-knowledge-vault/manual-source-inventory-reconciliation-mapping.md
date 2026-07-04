# Teacher Knowledge Vault — Manual Source Inventory Reconciliation Mapping

Last updated: 2026-07-04

```text
Status: reconciliation mapping — fake records only
```

## Mapping Targets

Manual inventory records may map to:

- source inventory records
- resource candidates
- representation candidates
- source item labels
- source reconciliation records
- review queue items
- future connector targets (blocked in M7b)

## Examples

| Manual label type | Reconciliation role |
| --- | --- |
| Drive-only label | canonical storage candidate |
| Canvas-only label | deployment reconciliation candidate (`only_in_canvas`) |
| NAS label | mirror candidate (`nas_mirror_candidate`) |
| Gemini/NotebookLM label | planning source candidate |
| local staging label | staging source candidate |
| teacher-only label | restricted-indexable candidate |
| `99_DO_NOT_SCAN` label | blocked/non-indexable/non-discoverable |

Fixture: `assistant/teacher-knowledge-vault/m7b/fake-reconciliation-mapping.json`
