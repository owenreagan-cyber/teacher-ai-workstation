# Teacher Knowledge Vault — Smart Rename Rule DSL Examples

Last updated: 2026-07-04

```text
Status: fake rule examples only — rule execution runtime is future
Rules are data, not buried in TypeScript
```

## Example Rule Types (M4 Fake)

- Saxon lesson homework odds
- Saxon Power Up letter
- Teacher guide/manual
- Completed study guide / answer key
- CKHG study guide
- CKSci assessment teacher key
- AI-generated review game

Each rule produces: evidence, extracted fields, suggested filename, suggested destination, confidence, review requirement, blocked actions when needed.

Fixture: `assistant/teacher-knowledge-vault/m4/fake-rule-dsl-rename-examples.yaml`

Cross-reference: `docs/teacher-knowledge-vault/classification-rule-dsl.md`, M0 `fake-classification-rule.yaml`

## Rule Output Requirements

| Output | Required |
| --- | --- |
| `evidence` | yes |
| `extracted_fields` | yes |
| `suggested_filename` | yes |
| `suggested_destination` | yes |
| `confidence` | yes |
| `requires_review` | yes |
| `blocked_actions` | when teacher-only or do-not-scan risk |

Rule execution runtime remains blocked until Owen-approved mission.
