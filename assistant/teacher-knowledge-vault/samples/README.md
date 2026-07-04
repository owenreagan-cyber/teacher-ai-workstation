# Teacher Knowledge Vault M0 Sample Fixtures

Fictional planning fixtures for expanded M0 architecture freeze. Not connector implementations.

| Fixture | Purpose |
| --- | --- |
| `fake-connector-capabilities.json` | Connector SDK contract illustration |
| `fake-source-item.json` | Normalized source item shape |
| `fake-resource-identity.json` | Resource with representations |
| `fake-representation-source-map.json` | Representation → source mapping |
| `fake-fingerprint-set.json` | Fingerprint types |
| `fake-classification-rule.yaml` | Rule DSL example |
| `fake-observability-metrics.json` | M0 metrics sample |
| `fake-evidence-package.json` | Evidence/confidence package |
| `fake-smart-rename-suggestion.json` | Rename suggestion (no execute) |
| `fake-source-reconciliation-record.json` | Multi-source reconciliation |
| `fake-taxonomy-target.json` | Canonical taxonomy folders |
| `fake-intake-promotion-record.json` | Intake-to-vault gate |
| `fake-knowledge-entry-outline.md` | Memory-path outline (not vault file) |

M1 catalog fixtures: `../m1/`

```bash
bin/chief-of-staff --teacher-knowledge-vault-m0-architecture-freeze-status
bin/chief-of-staff --teacher-knowledge-vault-m1-fake-catalog-status
```
